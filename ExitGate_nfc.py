"""
Exit Gate NFC - ระบบออกด่านทางด่วน
รันด้วย: python3 ExitGate_nfc.py
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
def update_transaction_log(card_data, entry_point, exit_point, cost):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    card_data["transaction_log"].append({
        "type": "exit",
        "time": timestamp,
        "detail": f"Exited from {exit_point} (entered at {entry_point}), cost {cost}"
    })
    return card_data

# ===================== GUI COLOR THEME =====================
BG_COLOR = "#F5F5F5"
FRAME_COLOR = "white"
TEXT_COLOR = "#2C3E50"
ACCENT_COLOR = "#E74C3C"  # สีแดงสำหรับ Exit
SUCCESS_COLOR = "#27AE60"
ERROR_COLOR = "#E74C3C"

# ===================== GUI =====================
root = Tk()
root.title("Exit Gate - NFC Toll System")
root.geometry("520x450")
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use("clam")
style.configure("Primary.TButton", font=("Arial", 11, "bold"), padding=8,
            background=ACCENT_COLOR, foreground="white")
style.map("Primary.TButton", background=[("active", "#C0392B")])

style.configure("Secondary.TButton", font=("Arial", 11), padding=8,
            background="#BDC3C7", foreground="#2C3E50")
style.map("Secondary.TButton", background=[("active", "#D5D8DC")])

style.configure("Danger.TButton", font=("Arial", 11), padding=8,
            background="#95A5A6", foreground="white")
style.map("Danger.TButton", background=[("active", "#7F8C8D")])

# ===================== HEADER =====================
header = Frame(root, bg=BG_COLOR)
header.pack(fill=X, pady=(15, 5))

Label(header,
    text="🚙 EXIT GATE",
    font=("Arial", 20, "bold"),
    fg=ACCENT_COLOR,
    bg=BG_COLOR).pack()

Label(header,
    text="แตะบัตรเพื่อออกด่าน (หักค่าทางด่วน)",
    font=("Arial", 11),
    fg="#7F8C8D",
    bg=BG_COLOR).pack(pady=(3, 0))

# ===================== MAIN FRAME =====================
main_frame = Frame(root, bg=FRAME_COLOR, bd=1, relief=GROOVE)
main_frame.pack(padx=30, pady=(8, 6), fill=X)

# ===================== DATA VARIABLES =====================
card_id_var = StringVar()
entry_var = StringVar(value="-")  # จะอ่านจาก local อัตโนมัติ
exit_var = StringVar(value="Gate B")
balance_var = StringVar(value="0.00")
cost_var = StringVar(value="0")
signal_status = StringVar(value="READY")

exit_options = ["Gate A", "Gate B", "Gate C"]

# ตารางค่าทางด่วน
TOLL_TABLE = {
    ("Gate A", "Gate B"): 100,
    ("Gate A", "Gate C"): 200,
    ("Gate B", "Gate C"): 100
}

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

# ----- Cost -----
Label(main_frame, text="Cost (฿)", font=("Arial", 12),
    bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, padx=18, pady=6, sticky="e")
Label(main_frame, textvariable=cost_var,
    font=("Consolas", 13),
    bg="#FDEDEC", fg=ERROR_COLOR,
    anchor="w", padx=10,
    width=24).grid(row=2, column=1, pady=6, sticky="we")

# ----- Entry Gate (แสดงด่านเข้าที่อ่านจาก local - แก้ไขไม่ได้) -----
Label(main_frame, text="Entry Gate", font=("Arial", 12),
    bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=3, column=0, padx=18, pady=6, sticky="e")
Label(main_frame, textvariable=entry_var,
    font=("Consolas", 13),
    bg="#FEF9E7", fg="#F39C12",
    anchor="w", padx=10,
    width=24).grid(row=3, column=1, pady=6, sticky="we")

# ----- Exit Gate (เลือกด่านออก) -----
Label(main_frame, text="Exit Gate", font=("Arial", 12),
    bg=FRAME_COLOR, fg=TEXT_COLOR).grid(row=4, column=0, padx=18, pady=6, sticky="e")

exit_combo = ttk.Combobox(main_frame, textvariable=exit_var,
                   values=exit_options, width=15, state="readonly")
exit_combo.grid(row=4, column=1, padx=18, pady=6, sticky="w")

# ----- Status -----
signal_label = Label(
    main_frame,
    textvariable=signal_status,
    font=("Arial", 16, "bold"),
    fg=SUCCESS_COLOR,
    bg=FRAME_COLOR
)
signal_label.grid(row=5, column=0, columnspan=2, pady=(16, 12))

# ===================== BUTTONS =====================
btn_frame = Frame(root, bg=BG_COLOR)
btn_frame.pack(pady=(4, 10))

ttk.Button(btn_frame, text="แตะบัตร", command=lambda: threading.Thread(target=process_exit, daemon=True).start(),
         style="Primary.TButton", width=14).pack(side=LEFT, padx=8)
ttk.Button(btn_frame, text="อ่านบัตรใหม่", command=lambda: reset_fields(),
         style="Secondary.TButton", width=12).pack(side=LEFT, padx=8)
ttk.Button(btn_frame, text="ปิดโปรแกรม", command=root.destroy,
         style="Danger.TButton", width=10).pack(side=LEFT, padx=8)

# ===================== TOLL TABLE DISPLAY =====================
toll_frame = Frame(root, bg=BG_COLOR)
toll_frame.pack(pady=(5, 10))

Label(toll_frame, text="ตารางค่าทางด่วน:", font=("Arial", 10, "bold"),
    fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor="w")
Label(toll_frame, text="A→B: 100฿  |  A→C: 200฿  |  B→C: 100฿",
    font=("Arial", 9), fg="#7F8C8D", bg=BG_COLOR).pack(anchor="w")
Label(toll_frame, text="* Entry Gate จะแสดงอัตโนมัติจากข้อมูลตอนเข้าด่าน",
    font=("Arial", 9), fg="#95A5A6", bg=BG_COLOR).pack(anchor="w", pady=(3,0))

# ===================== FUNCTIONS =====================
def calculate_cost(entry, exit_gate):
    """
    สูตรคำนวณค่าทางด่วน:
    - Gate A → B: 100 บาท (ระยะทาง 10 กม.)
    - Gate A → C: 200 บาท (ระยะทาง 25 กม.)  
    - Gate B → C: 100 บาท (ระยะทาง 15 กม.)
    - ด่านเดียวกัน: 0 บาท
    - อื่นๆ: 50 บาท (ค่าเริ่มต้น)
    """
    if entry == exit_gate:
        return 0
    return TOLL_TABLE.get((entry, exit_gate)) or TOLL_TABLE.get((exit_gate, entry), 50)

def get_entry_gate_from_local(card_id):
    """อ่านข้อมูลด่านเข้าจาก local (ที่ EntryGate บันทึกไว้)"""
    local_data_dir = Path(__file__).parent / "local_entry_data"
    local_file = local_data_dir / f"{card_id}_entry.json"
    
    if local_file.exists():
        with open(local_file, 'r', encoding='utf-8') as f:
            entry_data = json.load(f)
            print(f"อ่านข้อมูลด่านเข้าจาก local_entry_data/{card_id}_entry.json")
            return entry_data.get("entry_gate", None)
    return None

def save_exit_to_local(card_id, entry_point, exit_point, cost, new_balance):
    """D. บันทึกด่านที่ออก ยอดเงินที่ใช้ ลงในเครื่อง NFC Reader (local)"""
    local_data_dir = Path(__file__).parent / "local_exit_data"
    local_data_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exit_record = {
        "card_id": card_id,
        "entry_gate": entry_point,
        "exit_gate": exit_point,
        "exit_time": timestamp,
        "toll_cost": cost,
        "balance_after": new_balance
    }
    
    local_file = local_data_dir / f"{card_id}_exit.json"
    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(exit_record, f, ensure_ascii=False, indent=4)
    
    print(f"บันทึกข้อมูลด่านออกลง local_exit_data/{card_id}_exit.json")
    return exit_record

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
        entry_var.set("-")
        return
    
    # อ่านด่านเข้าจาก local (อัตโนมัติ)
    local_entry = get_entry_gate_from_local(card_id)
    if local_entry:
        entry_var.set(local_entry)
        print(f"ตั้งค่าด่านเข้าจาก local: {local_entry}")
    else:
        entry_var.set("ไม่พบข้อมูล")
        print("ไม่พบข้อมูลด่านเข้า กรุณาเข้าด่านก่อน")
        
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
        print("Please register first")

def update_signal(can_pass):
    """B. ส่งสัญญาณไปเปิดไม้กั้น"""
    if can_pass:
        signal_status.set("✓ PASS - เปิดไม้กั้น")
        signal_label.configure(fg=SUCCESS_COLOR)
        print("ส่งสัญญาณเปิดไม้กั้น")
    else:
        signal_status.set("✗ NOT PASS - ยอดเงินไม่พอ")
        signal_label.configure(fg=ERROR_COLOR)
        print("ไม่ส่งสัญญาณเปิดไม้กั้น")

def thread_ab(card_data, entry_point, exit_point, balance):
    """
    Thread A,B:
    A. ตรวจสอบด่านเข้า + คำนวณค่าทางด่วน
    B. ส่งสัญญาณเปิดไม้กั้น
    """
    print("Thread A,B: ตรวจสอบและคำนวณค่าทางด่วน...")
    
    # A. คำนวณค่าทางด่วนจากด่านทางออก
    cost = calculate_cost(entry_point, exit_point)
    cost_var.set(str(cost))
    print(f"คำนวณค่าทางด่วน: {entry_point} → {exit_point} = {cost} บาท")
    
    balance_var.set(f"{balance:.2f}")
    
    if balance >= cost:
        # B. ส่งสัญญาณเปิดไม้กั้น
        update_signal(True)
        print(f"ยอดเงินเพียงพอ ({balance:.2f} >= {cost})")
        return True, cost
    else:
        update_signal(False)
        print(f"ยอดเงินไม่เพียงพอ ({balance:.2f} < {cost})")
        return False, cost

def thread_cd(card_id, card_data, entry_point, exit_point, cost, balance):
    """
    Thread C,D:
    C. หักยอดค่าทางด่วนออกจากยอดเงินคงเหลือ
    D. บันทึกด่านที่ออก ยอดเงินที่ใช้ ลง local + ส่งไป FTP
    """
    print("Thread C,D: หักเงินและบันทึกข้อมูล...")
    
    # C. หักยอดค่าทางด่วน
    new_balance = balance - cost
    card_data["balance"] = new_balance
    balance_var.set(f"{new_balance:.2f}")
    print(f"หักเงิน: {balance:.2f} - {cost} = {new_balance:.2f} บาท")
    
    # D.1 บันทึกด่านที่ออก ลง local
    save_exit_to_local(card_id, entry_point, exit_point, cost, new_balance)
    
    # D.2 บันทึก transaction log
    update_transaction_log(card_data, entry_point=entry_point, exit_point=exit_point, cost=cost)
    
    # D.3 ส่งข้อมูลไป FTP Server
    generate_and_upload_json(card_id, card_data)
    print(f"ส่งข้อมูลไป FTP Server สำเร็จ")

def process_exit():
    """Process exit gate tap - แยกการทำงานเป็น 2 threads (A,B กับ C,D)"""
    print("\n--- EXIT GATE ---")
    
    card_id = card_id_var.get()
    exit_point = exit_var.get()
    
    card_data = download_card_data(card_id)
    if card_data is None:
        print("ไม่พบข้อมูลการ์ดใน FTP")
        update_signal(False)
        return
    
    balance = float(card_data.get("balance", 0))
    
    # A. ตรวจสอบว่าเข้ามาที่ด่านใด (อ่านจาก local)
    local_entry = get_entry_gate_from_local(card_id)
    if local_entry:
        entry_point = local_entry
        entry_var.set(local_entry)
        print(f"พบข้อมูลด่านเข้าจาก local_entry_data/{card_id}_entry.json")
    else:
        # ไม่พบข้อมูลด่านเข้า - ไม่อนุญาตให้ออก
        entry_var.set("ไม่พบข้อมูล")
        signal_status.set("✗ กรุณาเข้าด่านก่อน")
        signal_label.configure(fg=ERROR_COLOR)
        print("ไม่พบข้อมูลด่านเข้า กรุณาเข้าด่านก่อนออก")
        return
    
    # Thread A,B: ตรวจสอบ + คำนวณ + ส่งสัญญาณไม้กั้น
    can_pass, cost = thread_ab(card_data, entry_point, exit_point, balance)
    
    # Thread C,D: หักเงิน + บันทึกข้อมูล (ทำงานแยก thread)
    if can_pass:
        t = threading.Thread(target=thread_cd, args=(card_id, card_data, entry_point, exit_point, cost, balance), daemon=True)
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
    entry_var.set("-")
else:
    # อ่านด่านเข้าจาก local (อัตโนมัติ)
    local_entry = get_entry_gate_from_local(card_id)
    if local_entry:
        entry_var.set(local_entry)
        print(f"ตั้งค่าด่านเข้าจาก local_entry_data/{card_id}_entry.json")
    else:
        entry_var.set("ไม่พบข้อมูล")
        print("ไม่พบข้อมูลด่านเข้า กรุณาเข้าด่านก่อน")
    
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
