"""
FTP Server สำหรับ NFC Card System
รันด้วยคำสั่ง: python3 server/ftp_server.py
"""

import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root directory (parent of server folder)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# FTP Configuration from .env
FTP_HOST = os.getenv("FTP_HOST", "localhost")
FTP_PORT = int(os.getenv("FTP_PORT", 2121))
FTP_USER = os.getenv("FTP_USER", "peeraphatmg9")
FTP_PASS = os.getenv("FTP_PASS", "peeraphatmg9")

# Create data directory for storing card data (in the same folder as this script)
DATA_DIR = Path(__file__).parent / "ftp_data"
DATA_DIR.mkdir(exist_ok=True)

def main():
    # Create authorizer
    authorizer = DummyAuthorizer()
    
    # Add user with full permissions
    # "elradfmw" = read, write, delete, rename, list, mkdir, rmdir
    authorizer.add_user(FTP_USER, FTP_PASS, str(DATA_DIR), perm="elradfmw")
    
    # Create handler
    handler = FTPHandler
    handler.authorizer = authorizer
    handler.passive_ports = range(60000, 60100)
    
    # Create and start server
    server = FTPServer(("127.0.0.1", FTP_PORT), handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5
    
    print("=" * 50)
    print("🚀 FTP Server Starting...")
    print("=" * 50)
    print(f"📍 Host: 127.0.0.1")
    print(f"🔌 Port: {FTP_PORT}")
    print(f"👤 User: {FTP_USER}")
    print(f"📁 Data Directory: {DATA_DIR}")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        server.close_all()

if __name__ == "__main__":
    main()
