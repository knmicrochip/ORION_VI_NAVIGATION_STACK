# orion-vi-navigation-stack
Navigation stack for orion VI rover

# create a dev enivroment

### create dev container
```
distrobox create --image docker.io/library/ubuntu:noble --home ~/Distrobox/Orion --nvidia --name ros-developement-experience && distrobox enter ros-developement-experience
```

### add repositories
```
sudo apt install software-properties-common -y && sudo add-apt-repository universe -y
```

```
sudo apt update && sudo apt install curl apt-transport-https -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

```
sudo apt update && sudo apt install ros-dev-tools ros-jazzy-desktop -y
```

```
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
```

```
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'

```

```
sudo add-apt-repository ppa:zhangsongcui3371/fastfetch -y 
```

### install VScode ROS2 and fastfetch

```
sudo apt update && sudo apt install code fastfetch ros-dev-tools ros-jazzy-desktop -y

```


```
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
```

```
distrobox-export --app code
```

```
git clone https://github.com/knmicrochip/orion-vi-navigation-stack.git
```

## Install dependencies 

install librealsense2
https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md

```
curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
gpg --dearmor | sudo tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null
```

```
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list
sudo apt-get update
```

```
sudo apt update && sudo apt install librealsense2-utils -y
```

bypass errors: (I have no idea what it's about)
```
sudo dpkg --configure librealsense2-udev-rules
```

```
sudo apt update && sudo apt install -y \
    ros-$ROS_DISTRO-rtabmap-ros \
    ros-$ROS_DISTRO-aruco-opencv \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-ros2-control \
    ros-$ROS_DISTRO-realsense2-* 
```



install ros wrapper for realsense
https://github.com/realsenseai/realsense-ros?tab=readme-ov-file#installation-on-ubuntu

install rtab-map 
https://deepwiki.com/introlab/rtabmap_ros/2-installation-and-setup



---
# Other stuff

### Gazebo

https://gazebosim.org/docs/harmonic/install_ubuntu/


### Dodatkowe fajne programy

`sudo apt install ros-$ROS_DISTRO-rqt-tf-tree ros-$ROS_DISTRO-rqt-image-view ros-$ROS_DISTRO-rqt-graph`

pokazuje nody i topiki

`ros2 run rqt_graph rqt_graph`

pokazuje TFy:

`ros2 run rqt_tf_tree`

pokazuje kamerę

`ros2 run rqt_image_view rqt_image_view`

Dodaj aliasy

```
echo 'alias rqt_graph="ros2 run rqt_graph rqt_graph"' >> ~/.bashrc
echo 'alias rqt_tf_tree="ros2 run rqt_tf_tree rqt_tf_tree"' >> ~/.bashrc
echo 'alias rqt_image_view="ros2 run rqt_image_view rqt_image_view"' >> ~/.bashrc
source ~/.bashrc
```

### alternative install for jetson (sudo apt update returns an error):

patch kernel before making distrobox

https://github.com/jetsonhacks/jetson-orin-librealsense


```
distrobox create --image docker.io/library/ros:jazzy-ros-base --home ~/Distrobox/Orion --nvidia --name ros-developement-experience && distrobox enter ros-developement-experience
```

```
sudo apt update && sudo apt install ros-dev-tools ros-jazzy-desktop -y
```

```
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo 'export PS1="\[\e[1;36m\]orion@ros-developement-experience\[\e[0m\]:\[\e[1;33m\]\w\[\e[0m\]\$ "' >> ~/.bashrc

source /opt/ros/jazzy/setup.bash
```
```
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
```
```
sudo apt update; sudo apt install code ros-dev-tools ros-jazzy-desktop -y
```

```
curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
gpg --dearmor | sudo tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null
```

```
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list
sudo apt-get update
```

```
sudo apt install librealsense2-utils -y
```
```
sudo apt install -y \
    ros-$ROS_DISTRO-rtabmap-ros \
    ros-$ROS_DISTRO-aruco-opencv \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-ros2-control \
    ros-$ROS_DISTRO-realsense2-* 
```
