#!/usr/bin/env bash
set -e

CONTAINER_NAME="ros-developement-experience"
IMAGE="docker.io/library/ros:jazzy-desktop"
ROS_DISTRO="jazzy"

echo "=== Creating Orion ROS2 Distrobox ==="

if ! distrobox list | grep -q "$CONTAINER_NAME"; then
    distrobox create \
        --image "$IMAGE" \
        --home ~/Distrobox/Orion \
        --nvidia \
        --name "$CONTAINER_NAME"
fi

echo "=== Entering container and installing dependencies ==="

distrobox enter "$CONTAINER_NAME" -- bash -c '
set -e

export ROS_DISTRO=jazzy

sudo apt update
sudo apt install -y \
    curl \
    apt-transport-https \
    software-properties-common \
    gnupg \
    lsb-release \
    git \
    fastfetch \
    ros-dev-tools

echo "=== Configuring ROS environment ==="

grep -qxF "source /opt/ros/jazzy/setup.bash" ~/.bashrc || \
    echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

grep -qxF "export ROS_DISTRO=jazzy" ~/.bashrc || \
    echo "export ROS_DISTRO=jazzy" >> ~/.bashrc

grep -qxF \
    '\''export PS1="\[\e[1;36m\]orion@ros-developement-experience\[\e[0m\]:\[\e[1;33m\]\w\[\e[0m\]\$ "'\'' \
    ~/.bashrc || \
    echo '\''export PS1="\[\e[1;36m\]orion@ros-developement-experience\[\e[0m\]:\[\e[1;33m\]\w\[\e[0m\]\$ "'\'' >> ~/.bashrc

echo "=== Installing VS Code ==="

sudo mkdir -p /etc/apt/keyrings

curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
    sudo gpg --dearmor --yes -o /etc/apt/keyrings/packages.microsoft.gpg

echo "deb [arch=amd64,arm64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | \
    sudo tee /etc/apt/sources.list.d/vscode.list

echo "=== Installing RealSense repository ==="

curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
    gpg --dearmor | \
    sudo tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null

echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/librealsense.list

sudo apt update

echo "=== Installing ROS2 and development packages ==="

sudo apt install -y \
    code \
    fastfetch \
    librealsense2-utils \
    ros-$ROS_DISTRO-rtabmap-ros \
    ros-$ROS_DISTRO-aruco-opencv \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-ros2-control \
    ros-$ROS_DISTRO-gz-ros2-control \
    ros-$ROS_DISTRO-rqt-tf-tree \
    ros-$ROS_DISTRO-rqt-image-view \
    ros-$ROS_DISTRO-rqt-graph \
    ros-$ROS_DISTRO-joint-state-publisher-gui

echo "=== Installing RealSense ROS packages ==="

sudo apt install -y "ros-$ROS_DISTRO-realsense2-*"

echo "=== Configuring aliases ==="

cat <<EOF >> ~/.bashrc

# Orion ROS2 aliases
alias rqt_graph="ros2 run rqt_graph rqt_graph"
alias rqt_tf_tree="ros2 run rqt_tf_tree rqt_tf_tree"
alias rqt_image_view="ros2 run rqt_image_view rqt_image_view"
EOF

echo "=== Cloning Orion navigation stack ==="

if [ ! -d ~/orion-vi-navigation-stack ]; then
    git clone https://github.com/knmicrochip/orion-vi-navigation-stack.git ~/
fi

echo "=== Exporting VS Code ==="

distrobox-export --app code

echo "=== Orion development environment ready! ==="

source /opt/ros/jazzy/setup.bash
fastfetch
'

echo "=== DONE ==="
echo "Enter environment using:"
echo "distrobox enter $CONTAINER_NAME"