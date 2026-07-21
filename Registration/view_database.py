"""
View Database - ดูข้อมูลบัตรทั้งหมดจาก ftp_data แบบตาราง
รันด้วย: python3 Registration/view_database.py
"""

import os
import json
from pathlib import Path

# Path ของ ftp_data (อยู่ใน ../server/ftp_data)
FTP_DATA_PATH = Path(__file__).parent.parent / "server" / "ftp_data"

def load_all_cards():
    """โหลดข้อมูลบัตรทั้งหมดจาก ftp_data"""
    cards = []
    
    if not FTP_DATA_PATH.exists():
        print("❌ ไม่พบโฟลเดอร์ ftp_data")
        print(f"   ตรวจสอบที่: {FTP_DATA_PATH}")
        return cards
    
    for card_folder in FTP_DATA_PATH.iterdir():
        if card_folder.is_dir():
            json_file = card_folder / f"{card_folder.name}.json"
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cards.append(data)
    
    return cards

def print_separator(width=80):
    print("=" * width)

def print_cards_table(cards):
    """แสดงตารางข้อมูลบัตร"""
    print_separator()
    print("📋 ข้อมูลบัตรทั้งหมด")
    print_separator()
    
    if not cards:
        print("ไม่พบข้อมูลบัตร")
        return
    
    # Header
    print(f"{'Card ID':<25} {'Email':<30} {'Balance':>10}")
    print("-" * 80)
    
    # Data
    for card in cards:
        card_id = card.get('card_id', 'N/A')
        email = card.get('email', 'N/A')
        balance = card.get('balance', 0)
        print(f"{card_id:<25} {email:<30} {balance:>10.2f} บาท")
    
    print_separator()
    print(f"รวมทั้งหมด: {len(cards)} บัตร")

def print_top_up_history(cards):
    """แสดงประวัติเติมเงินทั้งหมด"""
    print("\n")
    print_separator()
    print("💰 ประวัติเติมเงินทั้งหมด")
    print_separator()
    
    print(f"{'Card ID':<25} {'Amount':>10} {'Time':<25}")
    print("-" * 80)
    
    count = 0
    for card in cards:
        card_id = card.get('card_id', 'N/A')
        top_ups = card.get('top_up_history', [])
        for top_up in top_ups:
            amount = top_up.get('amount', 0)
            time = top_up.get('time', 'N/A')
            print(f"{card_id:<25} {amount:>10.2f} {time:<25}")
            count += 1
    
    if count == 0:
        print("ไม่พบประวัติเติมเงิน")
    
    print_separator()
    print(f"รวมทั้งหมด: {count} รายการ")

def print_transactions(cards):
    """แสดงประวัติการใช้งานทางด่วน"""
    print("\n")
    print_separator()
    print("🚗 ประวัติการใช้งานทางด่วน")
    print_separator()
    
    print(f"{'Card ID':<20} {'Type':<8} {'Detail':<35} {'Time':<20}")
    print("-" * 90)
    
    count = 0
    for card in cards:
        card_id = card.get('card_id', 'N/A')
        transactions = card.get('transaction_log', [])
        for trans in transactions:
            trans_type = trans.get('type', 'N/A')
            detail = trans.get('detail', 'N/A')[:35]
            time = trans.get('time', 'N/A')
            print(f"{card_id:<20} {trans_type:<8} {detail:<35} {time:<20}")
            count += 1
    
    if count == 0:
        print("ไม่พบประวัติการใช้งาน")
    
    print_separator()
    print(f"รวมทั้งหมด: {count} รายการ")

def print_card_detail(card_id, cards):
    """แสดงรายละเอียดบัตรใดบัตรหนึ่ง"""
    card = None
    for c in cards:
        if c.get('card_id') == card_id:
            card = c
            break
    
    if not card:
        print(f"❌ ไม่พบบัตร: {card_id}")
        return
    
    print_separator()
    print(f"📋 รายละเอียดบัตร: {card_id}")
    print_separator()
    print(f"Card ID: {card.get('card_id')}")
    print(f"Email: {card.get('email')}")
    print(f"Balance: {card.get('balance', 0):.2f} บาท")
    
    print("\n💰 ประวัติเติมเงิน:")
    for top_up in card.get('top_up_history', []):
        print(f"  - {top_up.get('amount')} บาท ({top_up.get('time')})")
    
    print("\n🚗 ประวัติการใช้งาน:")
    for trans in card.get('transaction_log', []):
        print(f"  - [{trans.get('type')}] {trans.get('detail')} ({trans.get('time')})")
    
    print_separator()

def main_menu():
    """แสดงเมนูหลัก"""
    cards = load_all_cards()
    
    while True:
        print("\n")
        print_separator()
        print("🗄️  NFC Database Viewer")
        print_separator()
        print("1. ดูข้อมูลบัตรทั้งหมด")
        print("2. ดูประวัติเติมเงิน")
        print("3. ดูประวัติการใช้งานทางด่วน")
        print("4. ดูรายละเอียดบัตร (ระบุ Card ID)")
        print("5. รีโหลดข้อมูล")
        print("0. ออก")
        print_separator()
        
        choice = input("เลือกเมนู: ").strip()
        
        if choice == "1":
            print_cards_table(cards)
        elif choice == "2":
            print_top_up_history(cards)
        elif choice == "3":
            print_transactions(cards)
        elif choice == "4":
            card_id = input("กรอก Card ID: ").strip()
            print_card_detail(card_id, cards)
        elif choice == "5":
            cards = load_all_cards()
            print("✅ รีโหลดข้อมูลสำเร็จ!")
        elif choice == "0":
            print("👋 ออกจากโปรแกรม")
            break
        else:
            print("❌ เลือกไม่ถูกต้อง")

if __name__ == "__main__":
    main_menu()
