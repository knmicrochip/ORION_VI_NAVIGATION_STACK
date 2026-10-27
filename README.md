# Opis

This is a repository that hosts the navigation stack for Orion VI Rover. Other software are in diffrent repositories, under the github organization or in individual repositories.

### Software:

The rover will be using a ROS 2 based stack for localization, navigation and control. For SLAM we will be using Realsense cameras with RTAB-Map library. That data will be converted into costmap that is usable by NAV2 for path planning. Custom controller will issue commands over MQTT to execute that path. Gazebo simulator will be used to validate used algorithms.

Low-level electronics are build on ESP32 that communicates to ODrive via CAN bus and receives MQTT commands through ethernet via Mosquitto server run on Raspberry Pi. Traffic is directed to Jetson Orin NX that hosts the ROS stack, or to remote command center that we will host our laptops running variety of environments.

Command centre will have one universal app that will have all required operating modes in various tabs. It will have support for joystick or game pad input for direct rover control. It will communicate via direct MQTT or /cmd_vel ROS topic. It will also have rendering of telemetry required for successful operation.

We are also looking into adding YOLO based object detection for detecting switches and demo mode operated via steam deck, where operator can walk behind the rover without needing whole operation centre.

### Oprogramowanie:

Łazik będzie używał ROS™ 2 do lokalizacji, nawigacji i kontrolowania napędem. Aby uzyskać SLAM użyjemy biblioteki RTAB-Map z kamerami Realsense™. Uzyskane dane zostaną przekonwertowane w mapę kosztów która będzie użyta do planowania trasy. Napiszemy własny kontroler który będzie wysyłał komendy po MQTT do napędu aby dostać się do celu. Użyjemy symulatora Gazebo do walidacji naszych algorytmów.

# TODO

- [X]  launchfile
- [X]  Dockerfile
  - [X]  Podstawowy Dockerfile
  - [ ]  Budowa paczki w Dockerfile (`colcon`)
- [X]  Graf/schemat nawigacji
- [ ]  Konwersja mapy 3D na mapę kosztów
- [X]  Dobry SLAM to podstawa
- [ ]  Linter
- [X]  Wifi na szufladzie
- [ ]  ~~zamienić .e57 na jakiś normalny format~~
- [X]  Nav2 i jego pluginy
  - [X]  bringup
    - [ ]  kontroler
    - [X]  TFy
    - [ ]  behaviour tree
- [X]  Gazebo
  - [ ]  TFy
  - [ ]  UDRF i SDF do symulacji
  - [X]  filtry kalmana
  - [ ]  Odometria
  - [x]  Kamery
  - [ ]  behavior tree / state machine
  - [ ]  błędy
    - [x]  marsjard zaginął
    - [ ]  ROS_LOCALHOST_ONLY is deprecated but still honored if it is enabled. Use ROS_AUTOMATIC_DISCOVERY_RANGE and ROS_STATIC_PEERS instead.
    - [X]  Timed out waiting for transform from base_link to odom to become available, tf error: Invalid frame ID "odom" passed to canTransform argument target_frame - frame does not exist
    - [X]  lack of images from deapth camera
    - [ ]  rviz amdgpu fails in docker
    - [ ]  Failed to create a bridge for topic [/realsense_front/camera_info] with ROS2 type [sensor_msgs/msg/PointCloud2] to topic [/realsense_d435i/points] with Gazebo Transport type [gz.msgs.PointCloudPacked]: could not create publisher: create_publisher() called for existing topic name rt/realsense_front/camera_info with incompatible type sensor_msgs::msg::dds_::PointCloud2_, at ./src/publisher.cpp:145, at ./src/rcl/publisher.c:117
    - [ ]  zły topic kamery
    - [ ]  robot spawnuje się kilka razy
    - [ ]  centralny dyfer nie działa
    - [ ]  body nie jest statyczne
    - [ ]  kompilacja podczas budowania dockera
- [ ]  Rozbudowa apki do sterowania
  - [ ]  Podgląd kamer
- [ ]  Spisać hasła do różnych rzeczy sieciowych
- [ ]  Otworzyć ssh na rasberce
  - [ ]  Sprawdzić kolejkowanie
- [ ]  Node który zamienia odczyt z enkoderów na odometrię
- [X]  Detekcja arucomarkerów
  - [X]  Pre-definiowane kordynaty tych markerów
- [ ]  Empiricznie sprawdzić macierze do filtru kalmana
- [ ]  trzymadełko na kamerę
- [X]  rviz config
- [ ]  switch detection in camera (openCV/YOLO)
  - https://github.com/ros-perception/vision_msgs
- [X]  aruco/QR auto decode
- [X]  zainstalować system na steam decku
- [X]  ogarnąć sieć aby można było sterować steam deckiem poprzez wifi
- [ ]  test nvidia jetson
- [ ]  fix custom ros-controller
- [X]  fix realsense regression
- [X]  fix steamdeck input with guID
- [ ]  set up foxglove
- [ ]  nipisać funkcje w pythonie do walidacji i ograniczenia wektora prędkości
- [ ]  github actions
  - [ ]  gazebo
  - [ ]  bringup testing
  - [ ]  auto linter that screams on colcon build
- [ ]  

---

Must have:

- [ ]  odpalenie dockera na jetsonie
- [ ]  napisać własny ros-control
- [ ]  połączyć ros-control w dockera
- [ ]  End to End testing of comms
- [ ]  custom local planer/controler
- [ ]  jak ma się mapowanie do lokalizacji
- [ ]  dostrajanie parametrów
- [ ]  A way to specify the goal cordinates

Will make the 10x dev:

- [ ]  gazebo sim
- [ ]  ros bag

Good to have:

- [ ]  Documentation to show to people
- [ ]  apka do definiowania pozycji aruco na topicu?

PRs to make:

- [ ]  RtabMap aruco launch file
- [ ]  RtabMap librealsense regression

Next Year improvements:
-> DDS on ESP32
-> nixOS on jetson, NIX Packages and devenv.sh

# Sekcja ROS2

TODO

![](docs/PLAN.excalidraw.png)

# Sekcja Docker

patrz [DOCKER.md](./docs/DOCKER.md)

# Sekcja organizacja - skróty itp

Aby stworzyć środowisko developerskie patrz na [DEVELOPMENT.md](./docs/DEVELOPMENT.md)

jeśli nie działają TFy z powodu braku łazika wysyłającego dane telemetrii: Użyj  `ros2 run joint_state_publisher_gui joint_state_publisher_gui` aby stworzyć dane syntetyczne
## ROS2

- nazwa paczki {nazwa}_pkg
- nazwa węzła {nazwa}_node
- nazwa uruchamiacza {nazwa}_launch.py

## Xarco, Gazebo, Symulacja

By uruchomić w trybie symulacji użyj komendy:

```
colcon build
ros2 launch orion_vi_bringup_pkg simulation_launch.py
```

# PLAN na ERC

### Przed

- konwersja mapy .e57 do jakiejś używalnej

### Dzień przed

~~- test nawigacji na mapie od organizatorów~~
rtab-map nie obsługuje importu

- jeśli nie działa to robimy własną mapę

# Sieć

teleoperacja przez steamdecka
ssid: UBNT
hasło: 123456789

esp szuflada ip: ping 192.168.1.50

rasberrka ip:  ping 192.168.1.1
użytkownik: `test1`
hasło: `123`

router stół ip: ping 192.168.1.101

router szuflada ip: ping 192.168.1.102

ustawić manualnie ip na laptopie podłączonym do switcha na stole.

# Topiki

TODO

działają ale nie są dobrze udokumentowane, szukaj w innych repozytoriach

```
mosquitto_pub -h 192.168.1.1 -p 1883 -t "Power/cmd" -m '{"S_INNE": 0, "S_SCI": 0, "S_ELEK": 0,
 "S_RAM": 0, "S_W_R": 0, "S_W_L": 0, "FAN1_ON": 0}'
```
