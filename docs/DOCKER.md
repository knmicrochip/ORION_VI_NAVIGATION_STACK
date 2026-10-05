
# Containers 

I am using podman in my developement machine, this is the way I set up with docker file. To build you need to install some package (I don't remember)

`docker` might behave differently

if you are using distrobox I recommend setting up an alias `echo "alias podman=podman-remote" >> ~/.bashrc`


This container will run the navigation bringup


```
git clone https://github.com/knmicrochip/ORION_VI_NAVIGATION_STACK
cd ~/ORION_VI_NAVIGATION_STACK
```


build:
```
podman build -f new.Dockerfile -t orion-bringup .
```

run for testing: 
```
podman run --rm --name ORION_BRINGUP --privileged -it \
 --network host --ipc host --replace --group-add keep-groups localhost/orion-bringup:latest
```

for deployment we need persistent container that won't vanish into the aether

## Simulation Container

This step might take a long time (30 mins for the first build without cache)

```
cd ~/ORION_VI_NAVIGATION_STACK
podman build -f simulation.Dockerfile -t orion-sim .
```
To get the GUI working we need to pass a bunch of stuff 

>#### IMPORTANT!
>You need to run `xhost +local:` on your host machine every restart to connect X11 or xwayland to the container 
>To do it permamently add autostart script with:
```
mkdir -p ~/.config/autostart && printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Name=xhost local' 'Exec=xhost +local:' 'Terminal=false' 'X-GNOME-Autostart-enabled=true' > ~/.config/autostart/xhost-local.desktop
```



```
 podman run --rm --name ORION_SIM \
  -it --network host --ipc host\
  --device nvidia.com/gpu=all\
  -e WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
  -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  -e DISPLAY="$DISPLAY" \
  -v "/tmp/.X11-unix:/tmp/.X11-unix:ro" \
  -v "$XDG_RUNTIME_DIR:$XDG_RUNTIME_DIR" \
  localhost/orion-sim:latest
```



## RealSense from source container:

```
podman build -f build-rs.Dockerfile -t realsense-source .
podman run --rm --name REALSENSE-SOURCE --privileged -it \
 --network host --ipc host --replace --group-add keep-groups localhost/realsense-source:latest
```


---
## various less important and undocumented notes

`--replace --platform linux/arm64`
`--entrypoint /bin/bash` <- add this for debugging inside the container
`--group-add keep-groups`

```
podman-remote run --rm --name ORION_BIN \
  --privileged -it \
  --network host --ipc host \
  --entrypoint /bin/bash \
  -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
  -e XDG_RUNTIME_DIR=/tmp/runtime-dir \
  -v $XDG_RUNTIME_DIR:/tmp/runtime-dir \
  --device /dev/dri \
  localhost/realsense-build:latest
```
```

sudo apt install ros-jazzy-rqt-graph -y && source /ros_entrypoint.sh && QT_QPA_PLATFORM=wayland ros2 run rqt_graph rqt_graph
```

# TODO

- [ ] Swerve drive controller fails
- [x] Gazebo doesn't see a display
- [ ] bad robot description
- [x] realsense not found 
- [x] enable GPU acceleration