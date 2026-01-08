from machine import Pin, I2C
import network
import time
import ntptime
import urequests
import json

def connect_wifi(SSID, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print('Connexion au réseau en cours...')
        wlan.connect(SSID, password)
        timeout = 10 #On attend de se connecter (pendant 10s max pour pas tout bloquer en cas d'échec)
        while not wlan.isconnected() and timeout>0:
            time.sleep(1)
            timeout -=1
    print('Connexion réussie')

    config = wlan.ifconfig()#ifconfig() renvoie un tuple : (IP, Masque, Passerelle, DNS)
    ip_esp32 = config[0]
    print(f"Adresse IP de l'ESP32 : {ip_esp32}")
    return True

def demander_acces(ip, badge_number, door_id):
    url = "http://"+ip+"/api/locks/verify-access"
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"badgeNumber": badge_number, "doorDeviceId": door_id})
    print(data)
    response = urequests.post(url, headers=headers, data=data) 
    print(response)
    donnees = response.json()
    return donnees['result']
