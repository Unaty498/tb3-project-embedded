from machine import Pin, I2C
import time
import ssd1306
import internet
import verrou
import lecteur

#Initialisation des variables pour la connexion internet
SSID = 'MefMD'
password = 'Mat2004Dau'
ip_request = "10.0.0.1"

#Initialisation de la Led
led = Pin(27, Pin.OUT)

#initialisation des boutons pour simuler le changement de porte
btn_a = Pin(15, Pin.IN, Pin.PULL_UP)
btn_b = Pin(32, Pin.IN, Pin.PULL_UP)
btn_c = Pin(14, Pin.IN, Pin.PULL_UP)


#Initialistion de la serrure (c'est en réalité avec le transistor qu'on communique)
#serrure = Pin(13, Pin.OUT)

#Initialisation de l'écran
i2c = I2C(0, scl=Pin(22), sda=Pin(23))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)

#Initialisation du lecteur
lecteur_badge = lecteur.LecteurBadge()

porte = "DOOR-MAIN-001"
def set_door(door):
    global porte
    porte = door
btn_a.irq(trigger=Pin.IRQ_FALLING, handler=lambda _: set_door(verrou.porte_a()))
btn_b.irq(trigger=Pin.IRQ_FALLING, handler=lambda _: set_door(verrou.porte_b()))
btn_c.irq(trigger=Pin.IRQ_FALLING, handler=lambda _: set_door(verrou.porte_c()))
    

if internet.connect_wifi(SSID, password):
    oled.fill(0)
    oled.text("Bonjour!", 0, 15)
    oled.show()

    while True:
        verrou.fermer_porte(led, oled)
        led.value(0)
        
        badge_number = lecteur_badge.lire()

        if badge_number:
            oled.fill(0)
            oled.text("Badge detecte!", 10, 10)
            oled.show()
            
            oled.fill(0)
            oled.text("Verif: " + badge_number, 0, 0)
            oled.show()
            
            resultat = internet.demander_acces(ip_request, badge_number, porte)
            if resultat == "GRANTED":
                verrou.ouvrir_porte(led, oled)
            else:
                verrou.refuser_acces(led, oled, resultat)
        
        # Petite pause pour ne pas surcharger le processeur
        time.sleep(0.1)

else :#Si on arrive pas à se connecter à internet, il sera de toute façon impossible de savoir si l'acces est autorisé
    oled.text("Erreur Wifi", 0, 0)
    oled.text("Arret...", 0, 12)
    oled.show()
    time.sleep(2)
    oled.fill(0)
