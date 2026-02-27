# TODO

- [x] launchfile
- [x] Dockerfile
  - [x] Podstawowy Dockerfile
  - [ ] Budowa paczki w Dockerfile (`colcon`)
- [ ] Graf/schemat nawigacji
- [ ] Konwersja mapy 3D na mapę kosztów
- [ ] Dobry SLAM to podstawa
- [ ] Linter
- [x] Wifi na szufladzie
- [ ] ~~zamienić .e57 na jakiś normalny format~~
- [ ] Nav2 i jego pluginy
  - [ ] bringup
- [ ] Gazebo
  - [ ] TFy
  - [ ] UDRF i SDF do symulacji 
  - [x] filtry kalmana
  - [ ] Odometria
  - [ ] Kamery
  - [ ] behavior tree / state machine
- [ ] Rozbudowa apki do sterowania 
  - [ ] Podgląd kamer
- [ ] Spisać hasła do różnych rzeczy sieciowych 
- [ ] Otworzyć ssh na rasberce
  - [ ] Sprawdzić kolejkowanie
- [ ] Node który zamienia odczyt z enkoderów na odometrię
- [ ] Detekcja arucomarkerów
  - [ ] Pre-definiowane kordynaty tych markerów
- [ ] Empiricznie sprawdzić macierze do filtru kalmana
- [ ] trzymadełko na kamerę
- [ ] rviz config
- [ ] switch detection in camera (openCV/YOLO)
  - https://github.com/ros-perception/vision_msgs
- [ ] aruco/QR auto decode 

# Sekcja ROS2

- do rozważenia nav2 albo easymapping
- w ros2 launch rtabmap_examples realsense_d435i_color.launch.py 
wiadomość mapy topic /mapData

# Sekcja Docker
zbuduj paczkę:
```
source install/setup.bash
colcon build
```
zbuduj dockera:
```
docker build -f Dockerfile --tag orion
```
jeśli podman-remote jest używane to zamienić `docker` na `podmna-remote` (wskazówka: Użyj `alias` w `.bashrc`)


uruchom dockera:
```
docker run --rm -it  orion
```

# Sekcja organizacja - skróty itp

`sudo apt install ros-$ROS_DISTRO-image-view`
`ros2 run image_view image_view --ros-args -r image:=<image topic>`


## ROS2
- nazwa paczki {nazwa}_pkg
- nazwa węzła {nazwa}_node

## SDF

https://github.com/sdformat-editor/sdformat-editor

# PLAN na ERC

### Przed

 - konwersja mapy .e57 do jakiejś używalnej

### Dzień przed

 ~~- test nawigacji na mapie od organizatorów~~
  rtab-map nie obsługuje importu
    - jeśli nie działa to robimy własną mapę


# Sieć

esp szuflada ip: ping 192.168.1.50 

rasberrka ip:  ping 192.168.1.1

router stół ip: ping 192.168.1.101

router szuflada ip: ping 192.168.1.102

ustawić manualnie ip na laptopie podłączonym do switcha na stole.

