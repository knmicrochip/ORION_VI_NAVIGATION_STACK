#!/bin/bash

source /opt/ros/jazzy/setup.bash

source install/setup.bash

# ros2 launch some_stuff some_other_stuff.launch.py



# echo "hello world"

# ros2 topic list

# colcon build

# ros2 run szuflada_pkg slam_node 

# ros2 launch launch/szuflada_slam.py

ros2 launch orion_vi_bringup_pkg bringup_launch.py 