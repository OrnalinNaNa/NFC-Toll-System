"""
NFC Reader Module - ใช้สำหรับอ่าน UID จากบัตร NFC
เครื่องอ่าน: ACR122U
"""

import time
from smartcard.scard import *
from smartcard.util import toHexString

BLOCK_NUMBER = 0x04
AUTHENTICATE = [0xFF, 0x88, 0x00, BLOCK_NUMBER, 0x60, 0x00]
GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x04]

class NFC_Reader():
    def __init__(self, uid=""):
        self.uid = uid
        self.hresult, self.hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        self.hresult, self.readers = SCardListReaders(self.hcontext, [])
        assert len(self.readers) > 0
        self.reader = self.readers[0]
        print("NFC Reader Connected")

        self.hresult, self.hcard, self.dwActiveProtocol = SCardConnect(
            self.hcontext,
            self.reader,
            SCARD_SHARE_SHARED,
            SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)

    def send_command(self, command):
        try:
            self.hresult, self.response = SCardTransmit(self.hcard, self.dwActiveProtocol, command)
            value = toHexString(self.response)
            return self.response, value
        except:
            return None, None

    def read_uid(self):
        print("Waiting for card...")
        while True:
            try:
                response, uid = self.send_command(GET_UID)
                if response:
                    self.uid = uid
                    print("Card Found!")
                    return uid.replace(" ", "_")
            except:
                pass
    
            print("No Card Found")
            
            try:
                self.hresult, self.hcard, self.dwActiveProtocol = SCardConnect(
                    self.hcontext,
                    self.reader,
                    SCARD_SHARE_SHARED,
                    SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
            except:
                pass
    
            time.sleep(1)
