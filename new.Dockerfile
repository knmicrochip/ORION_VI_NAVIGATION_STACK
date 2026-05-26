FROM docker.io/library/ros:jazzy-ros-base

ENV WS_DIR="/orion_ws"
WORKDIR ${WS_DIR}

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Create keyrings directory
RUN mkdir -p /etc/apt/keyrings

# Add Intel RealSense repository key
RUN curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
    gpg --dearmor -o /etc/apt/keyrings/librealsenseai.gpg

# Add RealSense APT repository
RUN echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] \
    https://librealsense.realsenseai.com/Debian/apt-repo \
    $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/librealsense.list


# Install librealsense utilities
RUN apt-get update && apt-get install -y \
    librealsense2-utils \
    && rm -rf /var/lib/apt/lists/*

# install ros packages
RUN apt-get update && apt-get install -y \
    ros-$ROS_DISTRO-rtabmap-ros \
    ros-$ROS_DISTRO-aruco-opencv \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-realsense2-* &&\
    rm -rf /var/lib/apt/lists/*

# set environment variables so ros can talk to other machines on the network
ENV ROS_DOMAIN_ID=0
ENV ROS_LOCALHOST_ONLY=0

LABEL name='orion'

# copy the files, probably could be slimmed down
COPY . ${WS_DIR}

ARG DEBIAN_FRONTEND=dialog

CMD ["/bin/bash", "-c", "source ${WS_DIR}/install/setup.bash && ros2 launch orion_vi_bringup_pkg bringup_launch.py" ]

# this dockerfile is for running the full navigation stack 
# see DOCKER.md for more information
