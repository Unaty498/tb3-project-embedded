# tb3-project-embedded

CONFIGURATION Lecteur RFID: SCK=5, MOSI=18, MISO=19, RST=14, CS(SDA)=33

# Problème technique avec la serrure

Le blocage technique repose sur une incompatibilité majeure entre les composants disponibles et la physique du circuit. Premièrement, le transistor que nous possédons (PH2907A) est de type PNP et conçu pour de faibles courants (max 600mA).Il risque donc de fondre sous la demande de la serrure (souvent >1A). Deplus, sa nature PNP rend son pilotage impossible ici : alimenté en 12V, il nécessiterait un signal de 12V pour s'éteindre, or l'ESP32 ne délivre que 3.3V, ce qui laisserait la serrure activée en permanence. Deuxièmement, l'absence de diode de roue libre (type 1N4007) est critique : une LED ou une simple résistance ne peuvent pas absorber la violente décharge électrique inverse (surtension) créée par la bobine de la serrure à l'extinction, et cela risquerait d'endommager fortement l'ESP32.

Voici un schéma du montage théorique :
![Circuit serrure](images/circuit_serrure.png)
