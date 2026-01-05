from machine import Pin, SPI, I2C
from mfrc522 import MFRC522
import time
import ssd1306
import internet
import verrou

#Initialisation des variables pour la connexion internet
SSID = 'MefMD'
password = 'Mat2004Dau'

#Initialisation de la Led
led = Pin(27, Pin.OUT)

#Initialistion de la serrure (c'est en réalité avec le transistor qu'on communique)
#serrure = Pin(13, Pin.OUT)

#Initialisation de l'écran
i2c = I2C(0, scl=Pin(22), sda=Pin(23))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)

#Initialisation du lecteur
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(18), miso=Pin(19))
reader = MFRC522(spi=spi, gpioRst=14, gpioSda=33)

version = reader._rreg(0x37)

porte = 1

if internet.connect_wifi(SSID, password):
    oled.fill(0)
    oled.text("Bonjour!", 0, 15)
    oled.show()

    while True:
        verrou.fermer_porte(led, oled)
        led.value(0)
        (statut, tag_type) = reader.request(reader.REQIDL)

        if statut == reader.OK:
            (statut, uid) = reader.anticoll()
            if statut == reader.OK:
                acces = internet.demander_acces(uid, porte)
                if acces:#Si l'acces est autorisé, on ouvre la porte, on affiche un message d'accès et on allume la led
                    verrou.ouvrir_porte(led, oled)
                else :#Si l'accès est refusé, on affiche un message de refus et on fait clignoter la led
                    verrou.refuser_acces(led, oled)
                    
else :#Si on arrive pas à se connecter à internet, il sera de toute façon impossible de savoir si l'acces est autorisé
    oled.text("Erreur Wifi", 0, 0)
    oled.text("Arret...", 0, 12)
    oled.show()
    time.sleep(2)
    oled.fill(0)
