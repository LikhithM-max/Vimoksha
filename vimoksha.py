# smartpfand_streamlit.py

import streamlit as st
import sqlite3
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode

DB_NAME = "pfand.db"

# 1. Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bottle_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bottle_id TEXT UNIQUE,
            timestamp TEXT,
            amount INTEGER DEFAULT 10
        )
    """)
    conn.commit()
    conn.close()

# 2. Deposit bottle
def add_bottle(bottle_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO bottle_returns (bottle_id, timestamp) VALUES (?, ?)", 
                  (bottle_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# 3. Return bottle
def return_bottle(bottle_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM bottle_returns WHERE bottle_id = ?", (bottle_id,))
    row = c.fetchone()
    if row:
        c.execute("DELETE FROM bottle_returns WHERE bottle_id = ?", (bottle_id,))
        conn.commit()
        conn.close()
        return {
            "bottle_id": bottle_id,
            "timestamp": row[2],
            "amount": "₹10"
        }
    conn.close()
    return None

# 4. View all
def get_all_bottles():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM bottle_returns")
    rows = c.fetchall()
    conn.close()
    return rows

# 5. Scan QR Code using webcam
def scan_qr_code():
    st.info("📸 Starting QR Scan... Press Q to quit.")
    cap = cv2.VideoCapture(0)
    bottle_id = None

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        decoded_objs = decode(frame)
        for obj in decoded_objs:
            bottle_id = obj.data.decode("utf-8")
            cap.release()
            cv2.destroyAllWindows()
            return bottle_id

        cv2.imshow("Scan QR Code (Press Q to cancel)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# -------------------
# Streamlit App Starts
# -------------------
st.set_page_config(page_title="SmartPfand", layout="centered")
st.title("♻️ SmartPfand – QR Code Bottle Return System")

init_db()

option = st.radio("Choose Action", ["Deposit Bottle", "Return Bottle", "View Bottles"])

if option in ["Deposit Bottle", "Return Bottle"]:
    st.markdown("### 📷 Scan a QR Code or Type Manually")

    use_qr = st.checkbox("Use Webcam to Scan")

    bottle_id = None

    if use_qr:
        if st.button("Start QR Scanner"):
            bottle_id = scan_qr_code()
            if bottle_id:
                st.success(f"✅ Scanned: {bottle_id}")
            else:
                st.warning("No QR code detected.")
    else:
        bottle_id = st.text_input("Enter Bottle ID")

    if st.button("Submit"):
        if not bottle_id:
            st.error("❌ Bottle ID is required.")
        else:
            if option == "Deposit Bottle":
                success = add_bottle(bottle_id)
                if success:
                    st.success("✅ Bottle deposited successfully!")
                else:
                    st.warning("⚠️ Bottle already exists.")
            elif option == "Return Bottle":
                receipt = return_bottle(bottle_id)
                if receipt:
                    st.success("✅ Bottle returned successfully!")
                    st.code(f"""
Receipt
-------
Bottle ID: {receipt['bottle_id']}
Returned At: {receipt['timestamp']}
Amount Refunded: {receipt['amount']}
Thank you for recycling!
""", language='text')
                else:
                    st.error("❌ Bottle not found or already returned.")

elif option == "View Bottles":
    st.subheader("📦 Bottles Currently Deposited")
    data = get_all_bottles()
    if data:
        for row in data:
            st.write(f"• Bottle ID: {row[1]} | Time: {row[2]}")
    else:
        st.info("No bottles in the system yet.")
