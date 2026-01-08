from machine import Pin, SPI
from mfrc522 import MFRC522
import time

class LecteurBadge:
    def __init__(self):
        # Configuration des pins SPI pour le lecteur RFID
        #self.spi = SPI(2, baudrate=100000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(18), miso=Pin(19))
        self.reader = MFRC522(sck=5, mosi=18, miso=19, rst=12, cs=33)

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
        
        # Modification: select_tag retourne maintenant aussi le SAK
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
                    self.reader.stop_crypto1() # Correction: stop_crypto1

        # --- ANDROID HCE / ISO-14443-4 (SAK = 0x20 souvent) ---
        elif (sak & 0x20):
            print("Téléphone Android détecté")
            # 1. Envoyer RATS (Request for Answer To Select)
            rats = [0xE0, 0x80] 
            rats += self.reader._crc(rats)
            (stat, recv, _) = self.reader._tocard(0x0C, rats)
            
            if stat == self.reader.OK:
                print("Select AID")
                # 2. Envoyer SELECT AID APDU
                # AID: F0010203040506 (Exemple a adapter cote Android)
                apdu = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00]
                
                # Encapsulation dans un I-Block ISO-DEP
                # PCB = 0x02 (Block number 0) ou 0x03 (Block nb 1) ?? 
                # Le standard dit initialement bloc 0 -> 0x02
                frame = [0x02] + apdu
                frame += self.reader._crc(frame)
                
                # Fonction interne pour envoyer des données et gérer le WTX (Waiting Time Extension)
                def send_and_wait(frame_data):
                    max_retries = 10
                    current_frame = frame_data
                    
                    while max_retries > 0:
                        (st, rc, _) = self.reader._tocard(0x0C, current_frame)
                        
                        if st != self.reader.OK:
                            return st, []
                        
                        # Check si S-Block WTX (PCB = 0xF2)
                        # Payload: [PCB=0xF2] [WTXM] [CRC1] [CRC2]
                        if len(rc) >= 1 and rc[0] == 0xF2:
                            print("S-Block WTX recu, en attente...")
                            # Repondre avec le meme WTX
                            wtx_frame = rc[0:-2] # Copier PCB et WTXM, sans CRC recu
                            wtx_frame += self.reader._crc(wtx_frame) # Recalcul du CRC
                            current_frame = wtx_frame
                            max_retries -= 1
                            continue
                        
                        return st, rc
                    return self.reader.ERR, []

                (stat, recv) = send_and_wait(frame)
                
                if stat == self.reader.OK and len(recv) > 3:
                    print("OK : extraction des données")
                    # Payload = [I-Block] [Data...] [CRC1] [CRC2]
                    # Note: mfrc522 retourne les données brutes, CRC inclu? 
                    # _tocard retourne recv qui sont les données lues du FIFO.
                    # MFRC522 vérifie CRC interne si configuré, mais ici on le fait nous meme?
                    # On assume recv contient [PCB] [Data...] [CRC1] [CRC2]
                    
                    print("Données reçues (hex):", [hex(b) for b in recv])
                    
                    response_payload = recv[1:-2] # Enlever PCB et CRC
                    if len(response_payload) >= 2:
                        sw1 = response_payload[-2]
                        sw2 = response_payload[-1]
                        
                        # Verification Succes (0x90 0x00)
                        if sw1 == 0x90 and sw2 == 0x00:
                            raw_id = response_payload[:-2] # Enlever SW1 SW2
                            badge_number = ""
                            for b in raw_id:
                                badge_number += chr(b)
        
        return badge_number