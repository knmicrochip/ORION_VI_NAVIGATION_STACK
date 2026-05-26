
# Containers 

I am using podman-remote in my developement machine, this is the way I set up with docker file. To build you need to install some package (I don't remember)

`docker` might behave differently

This container will run the navigation bringup

compile:
```
cd ~/orion-vi-navigation-stack
colcon build
```
build:
```
podman-remote build -f new.Dockerfile -t orion-bringup .
```

run for testing: 
```
podman-remote run --rm --name ORION-BRINGUP --privileged -it \
 --network host --ipc host --replace localhost/orion-bringup:latest
```

for deployment we need persistent container that won't vanish into the aether





---
## various less important and undocumented notes

`--replace --platform linux/arm64`
`--entrypoint /bin/bash` <- add this for debugging inside the container

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