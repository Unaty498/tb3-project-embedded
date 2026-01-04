from machine import Pin, I2C
import time
import ssd1306

def gestion_bouton_b(Pin):
    global ouvert
    ouvert = True

led = Pin(27, Pin.OUT)

i2c = I2C(0, scl=Pin(22), sda=Pin(23))
print(i2c.scan())#Juste pour vérifier que l'écran est bien détecté
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.text("Bonjour!", 15, 15)
oled.show()

btn_b = Pin(32, Pin.IN, Pin.PULL_UP)
btn_b.irq(trigger=Pin.IRQ_FALLING, handler=gestion_bouton_b)
ouvert = False
    
led.value(0)
while True :
    oled.fill(0)
    oled.text("Porte fermee.", 15, 15)
    oled.show()
    if ouvert:
        oled.fill(0)
        oled.text("Bienvenue !", 15, 15)
        oled.show()
        led.value(1)
        time.sleep(2.5)
        led.value(0)
        ouvert = False

