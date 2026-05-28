FROM docker.io/library/ros:jazzy-ros-base

ENV WS_DIR="/orion_ws"
WORKDIR ${WS_DIR}

RUN apt-get update && \
    apt-get install -y software-properties-common curl apt-transport-https \
    git make cmake libssl-dev libusb-1.0-0-dev \
    libudev-dev pkg-config libgtk-3-dev  \
    wget build-essential \
    libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev at nvidia-cuda-toolkit

# RUN wget https://github.com/realsenseai/librealsense/archive/refs/tags/v2.55.1.tar.gz && tar -xf v2.55.1.tar.gz  && rm -fr v2.55.1.tar.gz &&\
#     mv librealsense-2.55.1/ librealsense &&\

RUN git clone https://github.com/realsenseai/librealsense.git &&\
    cd librealsense &&\
    mkdir build && cd build &&\
    cmake .. -DBUILD_WITH_CUDA=true &&\
    cmake --build . &&\
    make &&\
    make install


CMD ["rs-enumerate-devices"]

# this dockerfile is for testing the build from source of librealsense of specific version so it can use CUDA on the nvidaia jetson 
# see DOCKER.md for more information