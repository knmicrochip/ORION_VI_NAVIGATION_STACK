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

RUN git clone --depth 1 https://github.com/realsenseai/librealsense.git &&\
    cd librealsense &&\
    mkdir -p build && cd build &&\
    cmake .. \
        #  -DBUILD_WITH_CUDA=true \
        #  -DBUILD_CUDA_HOST_COMPILER=/usr/bin/g++-12 \
         -DFORCE_RSUSB_BACKEND=ON \
         -DCMAKE_BUILD_TYPE=release \
         -DBUILD_EXAMPLES=false \
         -DBUILD_GRAPHICAL_EXAMPLES=false &&\
    cmake --build . --parallel $(nproc) &&\
    make &&\
    make install

# ===========================
# INSTALL GAZYEBO
# ===========================

RUN sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
RUN sudo apt-get update
RUN sudo apt-get install gz-harmonic


# ===========================
# INSTALL ROS PACKAGES
# ===========================

# install ros packages
RUN apt-get update && apt-get install -y \
    ros-$ROS_DISTRO-rtabmap-ros \
    ros-$ROS_DISTRO-aruco-opencv \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-ros2-control \
    ros-$ROS_DISTRO-gz-ros2-control \
    rm -rf /var/lib/apt/lists/*

# set environment variables so ros can talk to other machines on the network
ENV ROS_DOMAIN_ID=0
ENV ROS_LOCALHOST_ONLY=0

LABEL name='orion'

# copy the files, probably could be slimmed down
COPY . ${WS_DIR}

# building the ROS2 package inside the docker 
RUN colcon build --packages-select orion_vi_bringup_pkg
RUN colcon build --packages-select orion_vi_description
RUN colcon build --packages-select swerve_drive_controller

ARG DEBIAN_FRONTEND=dialog

CMD ["/bin/bash", "-c", "source ${WS_DIR}/install/setup.bash && ros2 launch orion_vi_bringup_pkg simulation_launch.py" ]

# this dockerfile is for running the full navigation stack with gazebo simulation
# see DOCKER.md for more information