from machine import Pin, SPI
from mfrc522 import MFRC522
import time

class LecteurBadge:
    def __init__(self):
        # Configuration des pins SPI pour le lecteur RFID
        self.spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(18), miso=Pin(19))
        self.reader = MFRC522(spi=self.spi, gpioRst=14, gpioSda=33)

    def lire(self):
        """
        Tente de lire un badge (Mifare Classic ou Android HCE).
        Retourne le numero du badge (string) si lu, sinon None.
        """
        (statut, tag_type) = self.reader.request(self.reader.REQIDL)

        if statut != self.reader.OK:
            return None

        (statut, uid) = self.reader.anticoll()
        if statut != self.reader.OK:
            return None

        (statut, sak) = self.reader.select_tag(uid)
        if statut != self.reader.OK:
            return None
        
        badge_number = None

        # --- MIFARE CLASSIC (SAK = 0x08 ou 0x18 ou 0x88 selon version) ---
        if (sak == 0x08) or (sak == 0x18) or (sak == 0x88):
            # Cle par defaut (Mifare Default Key)
            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            if self.reader.auth(self.reader.AUTHENT1A, 4, key, uid) == self.reader.OK:
                data = self.reader.read(4)
                if data:
                    badge_number = ""
                    for b in data:
                        if b != 0:
                            badge_number += chr(b)
                    self.reader.stop_crypto()

        # --- ANDROID HCE / ISO-14443-4 (SAK = 0x20 souvent) ---
        elif (sak & 0x20):
            # 1. Envoyer RATS
            rats = [0xE0, 0x80] 
            rats += self.reader._crc(rats)
            (stat, recv, _) = self.reader._tocard(0x0C, rats)
            
            if stat == self.reader.OK:
                # 2. Envoyer SELECT AID APDU
                # AID: F0010203040506
                apdu = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00]
                frame = [0x02] + apdu
                frame += self.reader._crc(frame)
                
                (stat, recv, _) = self.reader._tocard(0x0C, frame)
                
                if stat == self.reader.OK and len(recv) > 3:
                    # Payload = [I-Block] [Data...] [SW1] [SW2] [CRC1] [CRC2]
                    response_payload = recv[1:-2]
                    if len(response_payload) >= 2:
                        sw1 = response_payload[-2]
                        sw2 = response_payload[-1]
                        if sw1 == 0x90 and sw2 == 0x00:
                            raw_id = response_payload[:-2]
                            badge_number = ""
                            for b in raw_id:
                                badge_number += chr(b)
        
        return badge_number