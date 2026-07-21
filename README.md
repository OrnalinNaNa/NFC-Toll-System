# NFC Card System - ระบบชำระค่าทางด่วน

## Project Overview
โปรเจกต์นี้เป็นระบบจัดการบัตร NFC สำหรับชำระค่าทางด่วน โดยมีการเชื่อมต่อกับเครื่องอ่านบัตร NFC, ระบบลงทะเบียนบัตร, ระบบตรวจสอบการเข้า-ออกด่าน และเซิร์ฟเวอร์ FTP สำหรับจัดเก็บข้อมูลแบบรวมศูนย์ ระบบถูกออกแบบมาเพื่อให้การชำระค่าทางด่วนเป็นไปอย่างรวดเร็ว ถูกต้อง และมีประสิทธิภาพ

## Features
- ระบบลงทะเบียนบัตร NFC พร้อมการเติมเงิน
- ระบบยืนยันตัวตนผ่าน OTP โดยใช้อีเมล
- ระบบด่านเข้าและด่านออกสำหรับตรวจสอบการผ่านด่าน
- ระบบหักค่าผ่านทางอัตโนมัติตามเส้นทาง
- ระบบบันทึกข้อมูลลงไฟล์ JSON และส่งข้อมูลไปยัง FTP Server
- รองรับการดูข้อมูลบัตรทั้งหมดจากระบบจัดการฐานข้อมูล

## Tech Stack

- **Language:** Python 3
- **GUI:** Tkinter
- **NFC Communication:** PySCard
- **FTP Server:** pyftpdlib
- **Configuration:** python-dotenv
- **Email Service:** SMTP (Gmail)
- **Data Storage:** JSON

## Team Members
- OrnalinNaNa
- peeraphat29

## How to Run
### 1. สิ่งที่ต้องมี
- ติดตั้ง Python 3 (แนะนำ 3.9 ขึ้นไป)
- ติดตั้งแพ็กเกจที่จำเป็นด้วยคำสั่งต่อไปนี้

```bash
pip3 install pyscard pyftpdlib python-dotenv
```

- มีเครื่องอ่านบัตร NFC รุ่น ACR122U และติดตั้ง Driver/PC/SC เรียบร้อย
- มีบัญชีอีเมลสำหรับรับ OTP

### 2. ตั้งค่าไฟล์ .env
สร้างไฟล์ .env และกำหนดค่าต่าง ๆ ดังนี้

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FTP_HOST=localhost
FTP_PORT=2121
FTP_USER=peeraphatmg9
FTP_PASS=peeraphatmg9
```

### 3. เปิด FTP Server
รันคำสั่งต่อไปนี้ใน Terminal แรก

```bash
python3 server/ftp_server.py
```

### 4. ลงทะเบียนบัตรและเติมเงิน
รันคำสั่งต่อไปนี้ใน Terminal ที่สอง

```bash
python3 Registration/CardRegis_system.py
```

ขั้นตอนการใช้งาน:
1. วางบัตร NFC บนเครื่องอ่าน
2. กรอกอีเมลเพื่อรับ OTP
3. ใส่ OTP ที่ได้รับแล้วยืนยัน
4. กดปุ่มเติมเงินเพื่อเพิ่มยอดเงินในระบบ

### 5. ใช้งานระบบด่านเข้า
```bash
python3 EntryGate_nfc.py
```

### 6. ใช้งานระบบด่านออก
```bash
python3 ExitGate_nfc.py
```

### 7. ดูข้อมูลบัตรทั้งหมด
```bash
python3 Registration/view_database.py
```

---

## โครงสร้างโปรเจค
```text
Network-Project-main/
├── nfc_reader.py
├── EntryGate_nfc.py
├── ExitGate_nfc.py
├── Registration/
│   ├── CardRegis_system.py
│   └── view_database.py
├── server/
│   ├── ftp_server.py
│   └── ftp_data/
├── README.md
└── .env
```

## หมายเหตุ
- ยอดเงินขั้นต่ำสำหรับเข้าใช้ระบบด่านคือ 200 บาท
- ค่าธรรมเนียมการผ่านทางจะขึ้นอยู่กับเส้นทางที่เลือก
- หากพบปัญหาเกี่ยวกับ NFC Reader หรือ FTP Connection ควรตรวจสอบ Driver และสถานะเซิร์ฟเวอร์ก่อน
