from machine import Pin
import time

def ouvrir_porte(led, ecran):
    led.value(1)
    ecran.fill(0)
    ecran.text("Acces autorise", 0, 15)
    ecran.show()
    time.sleep(3)

def fermer_porte(led, ecran):
    led.value(0)
    ecran.fill(0)
    ecran.text("Bonjour!", 0, 15)
    ecran.show()

def refuser_acces(led, ecran):
    ecran.fill(0)
    ecran.text("Acces refuse", 0, 15)
    ecran.show()
    led.value(1)
    time.sleep_ms(100)
    led.value(0)
    time.sleep_ms(100)
    led.value(1)
    time.sleep_ms(100)
    led.value(0)
