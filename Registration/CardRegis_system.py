"""
Smart Card Registration System - ระบบลงทะเบียนและเติมเงินบัตร NFC
รันด้วย: python3 Registration/CardRegis_system.py
"""

import sys
from pathlib import Path

# เพิ่ม parent folder เข้า path เพื่อ import nfc_reader
sys.path.append(str(Path(__file__).parent.parent))

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import random
import ssl
import smtplib
import json
import time
import os
from ftplib import FTP
from dotenv import load_dotenv
from email.message import EmailMessage
from io import BytesIO
import datetime
import threading
from nfc_reader import NFC_Reader

# Load environment variables from root directory (parent of Registration folder)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# ===================== GUI COLOR THEME =====================
BG_COLOR = "#F5F5F5"
FRAME_COLOR = "white"
TEXT_COLOR = "#2C3E50"
ACCENT_COLOR = "#3498DB"
SUCCESS_COLOR = "#27AE60"
ERROR_COLOR = "#E74C3C"

# ===================== Data =====================
card_data = {}
accounts_data = {}

# ===================== Email =====================
def generate_otp(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def send_otp_by_email(receiver_email, otp):
    smtp_server = os.getenv("SMTP_SERVER")
    port = int(os.getenv("SMTP_PORT"))
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    message = EmailMessage()
    message.set_content(f"Your OTP is: {otp}")
    message["Subject"] = "Your OTP Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
        print("OTP sent successfully!")
    except Exception as e:
        print("Error sending email:", e)

# ===================== FTP =====================
def download_json_from_ftp(card_id):
    ftp_host = os.getenv("FTP_HOST")
    ftp_port = int(os.getenv("FTP_PORT"))
    ftp_user = os.getenv("FTP_USER")
    ftp_pass = os.getenv("FTP_PASS")
    target_file = f"{card_id}.json"

    ftp = FTP()
    try:
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        ftp.cwd(card_id)
        files = ftp.nlst()
        if target_file not in files:
            ftp.quit()
            return None

        bio = BytesIO()
        ftp.retrbinary('RETR ' + target_file, bio.write)
        ftp.quit()
        bio.seek(0)
        return json.loads(bio.read().decode('utf-8'))
    except Exception as e:
        print("FTP Error while downloading:", e)
        try:
            ftp.quit()
        except:
            pass
        return None

def generate_and_upload_json(card_id, card_data):
    ftp_host = os.getenv("FTP_HOST", "localhost")
    ftp_port = int(os.getenv("FTP_PORT", 2121))
    ftp_user = os.getenv("FTP_USER", "peeraphatmg9")
    ftp_pass = os.getenv("FTP_PASS", "peeraphatmg9")

    print(f"Uploading {card_id}...")

    local_filename = f"{card_id}.json"
    with open(local_filename, 'w', encoding='utf-8') as f:
        json.dump(card_data, f, ensure_ascii=False, indent=4)

    ftp = FTP()
    try:
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        try:
            ftp.mkd(card_id)
        except:
            pass
        ftp.cwd(card_id)
        with open(local_filename, 'rb') as f:
            ftp.storbinary(f'STOR {card_id}.json', f)
        ftp.quit()
        print(f"✅ อัปโหลดสำเร็จ! Card {card_id}")
    except Exception as e:
        print(f"❌ FTP Error: {e}")
        try:
            ftp.quit()
        except:
            pass
    
    try:
        os.remove(local_filename)
    except:
        pass

# ===================== SYNC DATA EVERY 5 MINUTES =====================
updated_cards = set()  # เก็บ card_id ที่มีการ update
SYNC_INTERVAL = 300    # 5 นาที = 300 วินาที

def add_to_sync_queue(card_id):
    """เพิ่ม card_id เข้าคิวสำหรับ sync"""
    updated_cards.add(card_id)
    print(f"เพิ่ม {card_id} เข้าคิว sync")

def sync_to_gates():
    """ส่งข้อมูลที่มีการ update ไปยังด่านต่างๆ ผ่าน FTP Server"""
    global updated_cards
    
    if not updated_cards:
        print("ไม่มีข้อมูลที่ต้อง sync")
        return
    
    print(f"\n=== Sync ข้อมูล {len(updated_cards)} cards ===")
    synced = set()
    
    for card_id in updated_cards.copy():
        try:
            # ดาวน์โหลดข้อมูลล่าสุดจาก FTP แล้วส่งไปด่าน
            card_data = download_json_from_ftp(card_id)
            if card_data:
                # อัปโหลดข้อมูลไป FTP อีกครั้ง (ด่านต่างๆ จะดึงข้อมูลจากที่นี่)
                generate_and_upload_json(card_id, card_data)
                synced.add(card_id)
                print(f"Sync {card_id} สำเร็จ")
        except Exception as e:
            print(f"Sync {card_id} ล้มเหลว: {e}")
    
    updated_cards -= synced
    print(f"=== Sync เสร็จ: {len(synced)} สำเร็จ ===\n")

def start_sync_scheduler():
    """เริ่ม scheduler สำหรับ sync ทุก 5 นาที"""
    def sync_loop():
        while True:
            time.sleep(SYNC_INTERVAL)
            print(f"\n[Auto Sync]")
            sync_to_gates()
    
    threading.Thread(target=sync_loop, daemon=True).start()
    print(f"เริ่ม Sync Scheduler (ทุก {SYNC_INTERVAL//60} นาที)")

# ===================== ฟังก์ชันสำหรับ GUI การลงทะเบียน =====================
def send_otp():
    card_id = card_id_var.get().strip()
    email = email_var.get().strip()

    if not card_id:
        status_var.set("กรุณาใส่ Card ID")
        return
    if not email:
        status_var.set("กรุณาใส่ Email")
        return

    ftp_data = download_json_from_ftp(card_id)
    if ftp_data is not None:
        status_var.set("Card ID มีอยู่แล้วในระบบ FTP")
        messagebox.showerror("Error", f"Card ID {card_id} มีอยู่แล้วในระบบ FTP ไม่สามารถส่ง OTP ได้")
        return

    new_otp = generate_otp()
    if card_id not in card_data:
        card_data[card_id] = {"email": email, "otp": new_otp, "registered": False}
    else:
        card_data[card_id]["email"] = email
        card_data[card_id]["otp"] = new_otp
        card_data[card_id]["registered"] = False

    send_otp_by_email(email, new_otp)
    status_var.set(f"OTP sent to {email} (ตัวอย่าง OTP: {new_otp})")
    messagebox.showinfo("OTP Sent", f"OTP ถูกส่งไปยัง {email} เรียบร้อยแล้ว!")

def confirm_otp():
    card_id = card_id_var.get().strip()
    input_otp = otp_var.get().strip()
  
    if card_id not in card_data:
        status_var.set("ไม่พบข้อมูล Card ID กรุณาส่ง OTP ก่อน")
        return

    correct_otp = card_data[card_id]["otp"]
    if input_otp == correct_otp:
        ftp_data = download_json_from_ftp(card_id)
        if ftp_data is not None:
            status_var.set("Card นี้ลงทะเบียนไปแล้ว ไม่สามารถลงทะเบียนซ้ำได้")
            messagebox.showerror("Error", "Card นี้ลงทะเบียนไปแล้ว กรุณาใช้ Card อื่น หรือเข้าสู่ระบบเติมเงิน")
            return

        card_data[card_id]["registered"] = True
        sample_data = {
            "card_id": card_id,
            "balance": 0,
            "email": card_data[card_id]["email"],
            "top_up_history": [],
            "transaction_log": []
        }
        try:
            generate_and_upload_json(card_id, sample_data)
            accounts_data[card_id] = sample_data
            # เพิ่มเข้าคิว sync
            add_to_sync_queue(card_id)
            # อัพเดทยอดเงินในหน้าหลัก
            balance_var.set("0.00 ฿")
        except Exception as E:
            print("Error:", E)
        status_var.set(f"Card {card_id} ลงทะเบียนสำเร็จ!")
        messagebox.showinfo("Success", f"Card {card_id} ลงทะเบียนและอัปโหลดข้อมูลสำเร็จ! ทำงานสำเร็จ")
    else:
        status_var.set("OTP ไม่ถูกต้อง")

# ===================== ฟังก์ชันสำหรับหน้าการเติมเงิน =====================
def open_top_up_window():
    top_window = Toplevel(root)
    top_window.geometry("420x260")
    top_window.title("Top Up")
    top_window.configure(bg=BG_COLOR)

    top_card_id_var.set(card_id_var.get())

    top_header = Frame(top_window, bg=BG_COLOR)
    top_header.pack(fill=X, pady=(10, 5))

    Label(top_header, text="เติมเงินบัตร NFC", font=("Arial", 16, "bold"),
          fg=ACCENT_COLOR, bg=BG_COLOR).pack()

    Label(top_header, text="เติมเงินเข้า NFC Card", font=("Arial", 10),
          fg="#7F8C8D", bg=BG_COLOR).pack(pady=(3, 0))

    frame_top = Frame(top_window, bg=FRAME_COLOR, bd=1, relief=GROOVE)
    frame_top.pack(padx=20, pady=10, fill=X)

    Label(frame_top, text="Card ID", font=("Arial", 12),
          bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, padx=10, pady=8, sticky='e')
    Label(frame_top, textvariable=top_card_id_var, font=("Consolas", 13),
          width=20, bg="#F0F3F4", anchor="w", padx=8).grid(row=0, column=1, padx=10, pady=8)

    Label(frame_top, text="Amount (฿)", font=("Arial", 12),
          bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, padx=10, pady=8, sticky='e')
    Entry(frame_top, textvariable=top_amount_var, font=("Arial", 12),
          width=22).grid(row=1, column=1, padx=10, pady=8)

    def perform_top_up():
        card_id_local = top_card_id_var.get().strip()
        amount_str = top_amount_var.get().strip()
        if card_id_local == "":
            top_status_var.set("กรุณาใส่ Card ID")
            return
        if amount_str == "":
            top_status_var.set("กรุณาใส่จำนวนเงิน")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            top_status_var.set("จำนวนเงินไม่ถูกต้อง")
            return

        ftp_data = download_json_from_ftp(card_id_local)
        if ftp_data is None:
            top_status_var.set("Card ID ไม่พบในระบบ FTP กรุณาลงทะเบียนก่อน")
            return

        accounts_data[card_id_local] = ftp_data
        account = accounts_data[card_id_local]
        account["balance"] += amount

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        account["top_up_history"].append({"amount": amount, "time": timestamp})

        generate_and_upload_json(card_id_local, account)
        
        # เพิ่มเข้าคิว sync
        add_to_sync_queue(card_id_local)
        
        # อัพเดทยอดเงินในหน้าหลัก
        balance_var.set(f"{account['balance']:.2f} ฿")

        top_status_var.set(f"เติมเงินสำเร็จ! ยอดเงินใหม่: {account['balance']}")
        messagebox.showinfo("Success", f"เติมเงินสำเร็จ!\nยอดเงินใหม่: {account['balance']}\nเวลา: {timestamp}\nทำงานสำเร็จ")

    btn_top = Frame(top_window, bg=BG_COLOR)
    btn_top.pack(pady=(5, 5))

    ttk.Button(btn_top, text="เติมเงิน", command=perform_top_up,
               style="Primary.TButton", width=14).grid(row=0, column=0, padx=8)

    ttk.Button(btn_top, text="ปิด", command=top_window.destroy,
               style="Secondary.TButton", width=10).grid(row=0, column=1, padx=8)

    Label(top_window, textvariable=top_status_var, font=("Arial", 12, "bold"),
          fg=ERROR_COLOR, bg=BG_COLOR).pack(pady=(5, 10))

# ===================== ฟังก์ชันสำหรับ Reset และ Exit =====================
def reset_fields():
    reader = NFC_Reader()
    card_id = reader.read_uid().replace(" ", "_")
    
    card_id_var.set(card_id)
    top_card_id_var.set(card_id)
    
    # ดึงยอดเงินจาก FTP
    ftp_data = download_json_from_ftp(card_id)
    if ftp_data:
        balance = ftp_data.get("balance", 0)
        balance_var.set(f"{balance:.2f} ฿")
        status_var.set("ลงทะเบียนแล้ว")
    else:
        balance_var.set("-")
        status_var.set("ยังไม่ลงทะเบียน")
    
    email_var.set("")
    otp_var.set("")

def exit_app():
    root.destroy()

# ===================== ส่วน GUI หลัก =====================
root = Tk()
root.geometry("820x420")
root.title("Smart Card Registration System")
root.configure(bg=BG_COLOR)

card_id_var = StringVar()
email_var = StringVar()
otp_var = StringVar()
status_var = StringVar()
balance_var = StringVar(value="-")  # ยอดเงินปัจจุบัน

top_card_id_var = StringVar()
top_amount_var = StringVar()
top_status_var = StringVar()

style = ttk.Style()
style.theme_use("clam")
style.configure("Primary.TButton", font=("Arial", 11, "bold"), padding=8,
                background=ACCENT_COLOR, foreground="white")
style.map("Primary.TButton", background=[("active", "#5DADE2")])

style.configure("Secondary.TButton", font=("Arial", 11), padding=8,
                background="#BDC3C7", foreground=TEXT_COLOR)
style.map("Secondary.TButton", background=[("active", "#D5D8DC")])

style.configure("Danger.TButton", font=("Arial", 11), padding=8,
                background=ERROR_COLOR, foreground="white")
style.map("Danger.TButton", background=[("active", "#C0392B")])

# ===================== HEADER =====================
header = Frame(root, bg=BG_COLOR, height=70)
header.pack(fill=X, pady=(15, 5))

Label(header,
    text="NFC SMART CARD REGISTRATION SYSTEM",
    font=("Arial", 18, "bold"),
    fg=ACCENT_COLOR,
    bg=BG_COLOR).pack()

Label(header,
    text="ลงทะเบียนบัตร NFC และเติมเงิน",
    font=("Arial", 10),
    fg="#7F8C8D",
    bg=BG_COLOR).pack(pady=(3, 0))

# ===================== MAIN CONTENT =====================
content_frame = Frame(root, bg=BG_COLOR)
content_frame.pack(padx=30, pady=(8, 12), fill=BOTH, expand=True)

# LEFT: Card info + status
left_frame = Frame(content_frame, bg=FRAME_COLOR, bd=1, relief=GROOVE)
left_frame.pack(side=LEFT, fill=BOTH, expand=True)

Label(left_frame,
    text="CARD INFO",
    font=("Arial", 13, "bold"),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).pack(anchor="w", padx=15, pady=(12, 4))

Label(left_frame,
    text="Card ID",
    font=("Arial", 12),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).pack(anchor="w", padx=15, pady=(4, 2))

Label(left_frame,
    textvariable=card_id_var,
    font=("Consolas", 14),
    bg="#F0F3F4",
    fg="#2980B9",
    width=24,
    anchor="w",
    padx=8).pack(anchor="w", padx=15, pady=(0, 12))

Label(left_frame,
    text="Balance",
    font=("Arial", 12),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).pack(anchor="w", padx=15, pady=(0, 2))

Label(left_frame,
    textvariable=balance_var,
    font=("Consolas", 14, "bold"),
    bg="#E9F7EF",
    fg="#27AE60",
    width=24,
    anchor="w",
    padx=8).pack(anchor="w", padx=15, pady=(0, 12))

Label(left_frame,
    text="STATUS",
    font=("Arial", 12),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).pack(anchor="w", padx=15, pady=(0, 2))

Label(left_frame,
    textvariable=status_var,
    font=("Arial", 12, "bold"),
    fg=ERROR_COLOR,
    bg=FRAME_COLOR).pack(anchor="w", padx=15, pady=(0, 16))

ttk.Button(left_frame,
         text="อ่านบัตรใหม่",
         command=reset_fields,
         style="Secondary.TButton",
         width=18).pack(anchor="w", padx=15, pady=(0, 16))

# RIGHT: Email, OTP, actions
right_frame = Frame(content_frame, bg=FRAME_COLOR, bd=1, relief=GROOVE)
right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(12, 0))

Label(right_frame,
    text="REGISTER & OTP",
    font=("Arial", 13, "bold"),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 8), sticky="w")

right_frame.columnconfigure(1, weight=1)

Label(right_frame,
    text="Email",
    font=("Arial", 12),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).grid(row=1, column=0, padx=15, pady=6, sticky="e")

Entry(right_frame,
    textvariable=email_var,
    font=("Arial", 12)).grid(row=1, column=1, padx=(0, 15), pady=6, sticky="we")

ttk.Button(right_frame,
         text="ส่ง OTP",
         command=send_otp,
         style="Primary.TButton",
         width=12).grid(row=2, column=1, padx=(0, 15), pady=(2, 10), sticky="e")

Label(right_frame,
    text="OTP Code",
    font=("Arial", 12),
    bg=FRAME_COLOR,
    fg=TEXT_COLOR).grid(row=3, column=0, padx=15, pady=6, sticky="e")

Entry(right_frame,
    textvariable=otp_var,
    font=("Arial", 12)).grid(row=3, column=1, padx=(0, 15), pady=6, sticky="we")

ttk.Button(right_frame,
         text="ยืนยัน OTP",
         command=confirm_otp,
         style="Secondary.TButton",
         width=12).grid(row=4, column=1, padx=(0, 15), pady=(2, 12), sticky="e")

actions_frame = Frame(right_frame, bg=FRAME_COLOR)
actions_frame.grid(row=5, column=0, columnspan=2, pady=(4, 12))

ttk.Button(actions_frame,
         text="เติมเงิน",
         command=open_top_up_window,
         style="Primary.TButton",
         width=14).pack(side=LEFT, padx=6)

ttk.Button(actions_frame,
         text="ออกจากระบบ",
         command=exit_app,
         style="Danger.TButton",
         width=14).pack(side=LEFT, padx=6)

reader = NFC_Reader()
card_id = reader.read_uid()
card_id_var.set(card_id)

# ดึงยอดเงินจาก FTP
ftp_data = download_json_from_ftp(card_id)
if ftp_data:
    balance = ftp_data.get("balance", 0)
    balance_var.set(f"{balance:.2f} ฿")
    status_var.set("ลงทะเบียนแล้ว")
else:
    balance_var.set("-")
    status_var.set("ยังไม่ลงทะเบียน")

# เริ่ม Sync Scheduler (ทุก 5 นาที)
start_sync_scheduler()

root.mainloop()
