from machine import Pin, SPI, I2C
from mfrc522 import MFRC522
import time
import ssd1306

# 1. Création du bus SPI explicite
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(18), miso=Pin(19))
led = Pin(27, Pin.OUT)

# Clé par défaut pour les badges neufs (6 octets FF)
KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
# Adresse du bloc où l'on veut écrire (Secteur 2, premier bloc)
BLOCK_ADDR = 8

i2c = I2C(0, scl=Pin(22), sda=Pin(23))
print(i2c.scan())#Juste pour vérifier que l'écran est bien détecté
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)

# 2. Initialisation du lecteur avec l'objet SPI
reader = MFRC522(spi=spi, gpioRst=14, gpioSda=33)

print("--- Test de communication ---")
# On essaie de lire le registre de version (adresse 0x37)
# La librairie a une méthode interne _rreg pour lire un registre
version = reader._rreg(0x37)

print("Version du firmware lue : 0x{:02x}".format(version))
oled.fill(0)
oled.text("Lecteur pret", 0, 0)
oled.text("Approchez un badge...", 0, 15)
oled.show()

while True:
    led.value(0)
    (statut, tag_type) = reader.request(reader.REQIDL)

    if statut == reader.OK:
        oled.fill(0)
        oled.text("Badge detecte!", 10, 10)
        oled.show()
        (statut, uid) = reader.anticoll()
        led.value(1)
        if statut == reader.OK:
            # Transformation de l'UID en chaine hexa
            print("UID:", uid)
            time.sleep(1)
            oled.fill(0)
            oled.text("Lecteur pret", 0, 0)
            oled.text("Approchez un badge...", 0, 15)
            oled.show()


