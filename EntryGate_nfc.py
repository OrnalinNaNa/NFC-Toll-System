"""
Entry Gate NFC - ระบบเข้าด่านทางด่วน
รันด้วย: python3 EntryGate_nfc.py
"""

import datetime
import json
import os
import threading
from ftplib import FTP
from tkinter import *
from tkinter import ttk
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from nfc_reader import NFC_Reader

# Load environment variables from root directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ===================== FTP CONFIG =====================
ftp_host = os.getenv("FTP_HOST", "localhost")
ftp_port = int(os.getenv("FTP_PORT", 2121))
ftp_user = os.getenv("FTP_USER", "peeraphatmg9")
ftp_pass = os.getenv("FTP_PASS", "peeraphatmg9")

# ===================== อัปโหลดไฟล์ JSON ไป FTP =====================
def generate_and_upload_json(card_id, card_data):
    local_filename = f"{card_id}.json"
    remote_filename = f"{card_id}.json"

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
            ftp.storbinary(f'STOR {remote_filename}', f)
        ftp.quit()
    except Exception as e:
        print("FTP Error:", e)
        try:
            ftp.quit()
        except:
            pass

    try:
        os.remove(local_filename)
    except:
        pass

# ===================== ดาวน์โหลดข้อมูลจาก FTP =====================
def download_card_data(card_id):
    try:
        ftp = FTP()
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        ftp.cwd(card_id)
        filename = f"{card_id}.json"
        bio = BytesIO()
        ftp.retrbinary(f'RETR {filename}', bio.write)
        ftp.quit()
        bio.seek(0)
        data = bio.read().decode("utf-8")
        return json.loads(data)
    except Exception as e:
        print("Download Error:", e)
        return None

# ===================== บันทึก transaction log =====================
def update_transaction_log(card_data, entry_point):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    card_data["transaction_log"].append({
        "type": "entry",
        "time": timestamp,
        "detail": f"Entered at {entry_point}"
    })
    return card_data

# ===================== GUI COLOR THEME =====================
BG_COLOR = "#F5F5F5"
FRAME_COLOR = "white"
TEXT_COLOR = "#2C3E50"
ACCENT_COLOR = "#27AE60"  # สีเขียวสำหรับ Entry
SUCCESS_COLOR = "#27AE60"
ERROR_COLOR = "#E74C3C"

# ===================== GUI =====================
root = Tk()
root.title("Entry Gate - NFC Toll System")
root.geometry("500x380")
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use("clam")
style.configure("Primary.TButton", font=("Arial", 11, "bold"), padding=8,
            background=ACCENT_COLOR, foreground="white")
style.map("Primary.TButton", background=[("active", "#2ECC71")])

style.configure("Secondary.TButton", font=("Arial", 11), padding=8,
            background="#BDC3C7", foreground="#2C3E50")
style.map("Secondary.TButton", background=[("active", "#D5D8DC")])

style.configure("Danger.TButton", font=("Arial", 11), padding=8,
            background=ERROR_COLOR, foreground="white")
style.map("Danger.TButton", background=[("active", "#C0392B")])

# ===================== HEADER =====================
header = Frame(root, bg=BG_COLOR)
header.pack(fill=X, pady=(15, 5))

Label(header,
    text="🚗 ENTRY GATE",
    font=("Arial", 20, "bold"),
    fg=ACCENT_COLOR,
    bg=BG_COLOR).pack()

Label(header,
    text="แตะบัตรเพื่อเข้าด่าน",
    font=("Arial", 11),
    fg="#7F8C8D",
    bg=BG_COLOR).pack(pady=(3, 0))

# ===================== MAIN FRAME =====================
main_frame = Frame(root, bg=FRAME_COLOR, bd=1, relief=GROOVE)
main_frame.pack(padx=30, pady=(8, 6), fill=X)

# ===================== DATA VARIABLES =====================
card_id_var = StringVar()
entry_var = StringVar(value="Gate A")
balance_var = StringVar(value="0.00")
signal_status = StringVar(value="READY")

entry_options = ["Gate A", "Gate B", "Gate C"]
MIN_BALANCE = 200  # ยอดขั้นต่ำสำหรับเข้าด่าน

main_frame.columnconfigure(1, weight=1)

# ----- Card ID -----
Label(main_frame, text="Card ID", font=("Arial", 12),
    bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, padx=18, pady=(18, 6), sticky="e")
Label(main_frame, textvariable=card_id_var,
    font=("Consolas", 13),
    bg="#F0F3F4", fg="#2980B9",
    anchor="w", padx=10,
    width=24).grid(row=0, column=1, pady=(18, 6), sticky="we")

# ----- Balance -----
Label(main_frame, text="Balance (฿)", font=("Arial", 12),
    bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, padx=18, pady=6, sticky="e")
Label(main_frame, textvariable=balance_var,
    font=("Consolas", 13),
    bg="#E9F7EF", fg=SUCCESS_COLOR,
    anchor="w", padx=10,
    width=24).grid(row=1, column=1, pady=6, sticky="we")

# ----- Entry Gate -----
Label(main_frame, text="Entry Gate", font=("Arial", 11),
    bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, padx=18, pady=(14, 4), sticky="e")

entry_combo = ttk.Combobox(main_frame, textvariable=entry_var,
                    values=entry_options, width=15, state="readonly")
entry_combo.grid(row=2, column=1, padx=18, pady=(10, 4), sticky="w")

# ----- Min Balance Info -----
Label(main_frame, text=f"* ต้องมียอดขั้นต่ำ {MIN_BALANCE} บาท",
    font=("Arial", 10), fg="#7F8C8D",
    bg=FRAME_COLOR).grid(row=3, column=1, padx=18, pady=(2, 6), sticky="w")

# ----- Status -----
signal_label = Label(
    main_frame,
    textvariable=signal_status,
    font=("Arial", 16, "bold"),
    fg=SUCCESS_COLOR,
    bg=FRAME_COLOR
)
signal_label.grid(row=4, column=0, columnspan=2, pady=(16, 12))

# ===================== BUTTONS =====================
btn_frame = Frame(root, bg=BG_COLOR)
btn_frame.pack(pady=(4, 10))

ttk.Button(btn_frame, text="แตะบัตร", command=lambda: threading.Thread(target=process_entry, daemon=True).start(),
         style="Primary.TButton", width=14).pack(side=LEFT, padx=8)
ttk.Button(btn_frame, text="อ่านบัตรใหม่", command=lambda: reset_fields(),
         style="Secondary.TButton", width=12).pack(side=LEFT, padx=8)
ttk.Button(btn_frame, text="ปิดโปรแกรม", command=root.destroy,
         style="Danger.TButton", width=10).pack(side=LEFT, padx=8)

# ===================== FUNCTIONS =====================
def reset_fields():
    signal_status.set("SCANNING...")
    signal_label.configure(fg="#3498DB")
    root.update()

    reader = NFC_Reader()
    card_id = reader.read_uid().replace(" ", "_")
    
    card_id_var.set(card_id)
    card_data = download_card_data(card_id)
    
    if card_data is None:
        print("ไม่พบข้อมูลการ์ดใน FTP")
        signal_status.set("NOT FOUND")
        signal_label.configure(fg="#E74C3C")
        return
        
    try:
        balance = float(card_data.get("balance", 0))
        balance_var.set(f"{balance:.2f}")
        signal_status.set("READY")
        signal_label.configure(fg="#27AE60")
        print("Card id:", card_id)
    except:
        balance_var.set("0.00")
        signal_status.set("NO DATA")
        signal_label.configure(fg="#E67E22")
        print("Please register!!")

def update_signal(can_pass):
    """Thread A,B: แสดงผลและส่งสัญญาณไม้กั้น"""
    if can_pass:
        signal_status.set("✓ PASS - เปิดไม้กั้น")
        signal_label.configure(fg=SUCCESS_COLOR)
        print("ส่งสัญญาณเปิดไม้กั้น")
    else:
        signal_status.set("✗ NOT PASS - ยอดเงินไม่พอ")
        signal_label.configure(fg=ERROR_COLOR)
        print("ไม่ส่งสัญญาณเปิดไม้กั้น")

def save_entry_to_local(card_id, entry_point, balance):
    """บันทึกข้อมูลด่านที่เข้าลงในเครื่อง NFC Reader (local)"""
    local_data_dir = Path(__file__).parent / "local_entry_data"
    local_data_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_record = {
        "card_id": card_id,
        "entry_gate": entry_point,
        "entry_time": timestamp,
        "balance_at_entry": balance
    }
    
    local_file = local_data_dir / f"{card_id}_entry.json"
    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(entry_record, f, ensure_ascii=False, indent=4)
    
    print(f"บันทึกข้อมูลด่านเข้าลง local: {local_file}")
    return entry_record

def thread_ab(card_data, balance):
    """Thread A,B: ตรวจสอบยอดเงิน + แสดงผล + ส่งสัญญาณไม้กั้น"""
    print("Thread A,B: ตรวจสอบยอดเงินและแสดงผล...")
    
    balance_var.set(f"{balance:.2f}")
    
    if balance < MIN_BALANCE:
        print(f"ยอดเงินไม่เพียงพอ ({balance:.2f} < {MIN_BALANCE})")
        update_signal(False)
        return False
    else:
        print(f"ยอดเงินเพียงพอ ({balance:.2f} >= {MIN_BALANCE})")
        update_signal(True)
        return True

def thread_c(card_id, card_data, entry_point, balance):
    """Thread C: บันทึกด่านที่เข้าลงในเครื่อง NFC Reader และส่งข้อมูลไปยัง FTP Server"""
    print("Thread C: บันทึกข้อมูลด่านเข้า...")
    
    # C.1 บันทึกด่านที่เข้าลง local
    save_entry_to_local(card_id, entry_point, balance)
    
    # C.2 บันทึก transaction log
    update_transaction_log(card_data, entry_point=entry_point)
    
    # C.3 ส่งข้อมูลไป FTP Server
    generate_and_upload_json(card_id, card_data)
    print(f"ส่งข้อมูลไป FTP Server สำเร็จ")

def process_entry():
    """Process entry gate tap - แยกการทำงานเป็น 2 threads"""
    print("\n--- ENTRY GATE ---")
    
    card_id = card_id_var.get()
    entry_point = entry_var.get()

    card_data = download_card_data(card_id)
    if card_data is None:
        print("ไม่พบข้อมูลการ์ดใน FTP")
        update_signal(False)
        return
    
    balance = float(card_data.get("balance", 0))
    
    # Thread A,B: ตรวจสอบยอดเงิน + ส่งสัญญาณไม้กั้น
    can_pass = thread_ab(card_data, balance)
    
    # Thread C: บันทึกข้อมูล (ทำงานแยก thread)
    if can_pass:
        t = threading.Thread(target=thread_c, args=(card_id, card_data, entry_point, balance), daemon=True)
        t.start()
    
    print("------------------\n")

# ===================== INITIALIZE =====================
reader = NFC_Reader()
card_id = reader.read_uid()
card_id_var.set(card_id)

card_data = download_card_data(card_id)
if card_data is None:
    print("ไม่พบข้อมูลการ์ดใน FTP")
    signal_status.set("NOT FOUND")
    signal_label.configure(fg="#FF7675")
else:
    try:
        balance = float(card_data.get("balance", 0))
        balance_var.set(f"{balance:.2f}")
        signal_status.set("READY")
        print("Card id:", card_id)
    except:
        print("กรุณาลงทะเบียนก่อน")
        balance_var.set("0.00")
        signal_status.set("NO DATA")

root.mainloop()
