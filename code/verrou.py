from machine import Pin
import time

def ouvrir_porte(led, ecran):
    #serrure.value(1) #Pour ouvrir la porte (il faudrait passer la serrure en paramètre de la fonction)
    led.value(1)
    ecran.fill(0)
    ecran.text("Acces autorise", 0, 15)
    ecran.show()
    time.sleep(3)

def fermer_porte(led, ecran):
    #serrure.value(0) #Pour fermer la porte (il faudrait passer serrure en paramètre de la fonction)
    led.value(0)
    ecran.fill(0)
    ecran.text("Bonjour!", 0, 15)
    ecran.show()

def refuser_acces(led, ecran, raison):
    ecran.fill(0)
    ecran.text("Acces refuse", 0, 10)
    ecran.text(raison, 0, 20)
    ecran.show()
    led.value(1)
    time.sleep_ms(100)
    led.value(0)
    time.sleep_ms(100)
    led.value(1)
    time.sleep_ms(100)
    led.value(0)
    time.sleep(3)

def porte_a():
    return "DOOR-MAIN-001"

def porte_b():
    return "DOOR-SERVER-001"

def porte_c():
    return "DOOR-OFFICE-201"