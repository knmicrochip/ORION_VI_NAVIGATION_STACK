FROM docker.io/library/ros:jazzy-ros-base

ENV WS_DIR="/orion_ws"
WORKDIR ${WS_DIR}

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# ===========================
# INSTALL REALSENSE FROM REPO
# ===========================

# Create keyrings directory
# RUN mkdir -p /etc/apt/keyrings

# # Add Intel RealSense repository key
# RUN curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | \
#     gpg --dearmor -o /etc/apt/keyrings/librealsenseai.gpg

# # Add RealSense APT repository
# RUN echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] \
#     https://librealsense.realsenseai.com/Debian/apt-repo \
#     $(lsb_release -cs) main" \
#     > /etc/apt/sources.list.d/librealsense.list


# # Install librealsense utilities
# RUN apt-get update && apt-get install -y \
#     librealsense2-utils \
#     && rm -rf /var/lib/apt/lists/*

# ===========================
# INSTALL REALSENSE FROM SOURCE
# ===========================

RUN apt-get update && \
    apt-get install -y software-properties-common curl apt-transport-https \
    git make cmake libssl-dev libusb-1.0-0-dev \
    libudev-dev pkg-config libgtk-3-dev  \
    wget build-essential \
    libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev at nvidia-cuda-toolkit \
    gcc-12 g++-12

# RUN wget https://github.com/realsenseai/librealsense/archive/refs/tags/v2.55.1.tar.gz && tar -xf v2.55.1.tar.gz  && rm -fr v2.55.1.tar.gz &&\
#     mv librealsense-2.55.1/ librealsense &&\

RUN git clone https://github.com/realsenseai/librealsense.git &&\
    cd librealsense &&\
    mkdir build && cd build &&\
    cmake .. \
        #  -DBUILD_WITH_CUDA=true \
         -DFORCE_RSUSB_BACKEND=ON \
         -DCMAKE_BUILD_TYPE=release \
         -DBUILD_EXAMPLES=false \
         -DBUILD_GRAPHICAL_EXAMPLES=false \
         -DBUILD_CUDA_HOST_COMPILER=/usr/bin/g++-12 &&\
    cmake --build . --parallel $(nproc) &&\
    make &&\
    make install

# ===========================
# INSTALL ROS PACKAGES
# ===========================

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

# building the ROS2 package inside the docker 
RUN colcon build

ARG DEBIAN_FRONTEND=dialog

CMD ["/bin/bash", "-c", "source ${WS_DIR}/install/setup.bash && ros2 launch orion_vi_bringup_pkg bringup_launch.py" ]

# this dockerfile is for running the full navigation stack 
# see DOCKER.md for more information
