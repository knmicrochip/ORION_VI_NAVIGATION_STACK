#KOnfiguracja raspberry pi na serwer mqtt

1. Zainstallować system na raspberry (może być bez gui albo z będzie działać i tak)
!! ważne nie instalować systemu na pendrive bo przy wyłączaniu może sie rozwalić - karta sd lepsza

2. Połączyć sie z internetem i pobrać mosquitto
```
sudo apt install mosquitto
```

3. Autostart mosquitto po uruhomieniu raspberry 
```
sudo systemctl enable mosquitto
```
aby uruchomic recznie 
```
sudo systemctl start mosquitto
```

4. Zmiana w pliku konfiguracyjnym (prawdopodobnie jest on w /etc/mosquitto/mosquitto.conf)
```
sudo nano  /etc/mosquitto/mosquitto.conf
```
Dopisać te 2 linijki (port i zezwolenie na anonimowych) do tego pliku:
```
listener 1883
allow_anonymous true
```
Zrestartuj żeby zobaczyć czy działa
(test czy dziala mosquitto po restarcie)
'''
systemctl status mosquitto
'''



