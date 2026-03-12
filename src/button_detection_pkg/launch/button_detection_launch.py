"""
Launch file for the ERC 2026 Maintenance Panel button detection pipeline.

Starts:
  1. RealSense D435i camera (via realsense2_camera, optional)
  2. Button detector node (YOLO inference)
  3. ArUco fusion node (panel localisation + 3D coordinates)

Usage:
    ros2 launch button_detection_pkg button_detection_launch.py
    ros2 launch button_detection_pkg button_detection_launch.py \
        model_path:=/abs/path/to/best.pt  enabled:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("button_detection_pkg")
    config_file = os.path.join(pkg_share, "config", "detection_config.yaml")

    declare_model_path = DeclareLaunchArgument(
        "model_path", default_value="models/best.pt",
        description="Path to YOLO .pt or .onnx weights",
    )
    declare_enabled = DeclareLaunchArgument(
        "enabled", default_value="false",
        description="Start detection immediately",
    )
    declare_launch_realsense = DeclareLaunchArgument(
        "launch_realsense", default_value="true",
        description="Also launch the RealSense camera driver",
    )

    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("realsense2_camera"),
                "launch",
            ),
            "/rs_launch.py",
        ]),
        launch_arguments={
            "camera_namespace": "",
            "enable_gyro": "true",
            "enable_accel": "true",
            "unite_imu_method": "2",
            "align_depth.enable": "true",
            "enable_sync": "true",
            "rgb_camera.profile": "640x480x30",
        }.items(),
        condition=IfCondition(LaunchConfiguration("launch_realsense")),
    )

    detector_node = Node(
        package="button_detection_pkg",
        executable="detector_node",
        name="button_detector",
        parameters=[
            config_file,
            {
                "model_path": LaunchConfiguration("model_path"),
                "enabled": LaunchConfiguration("enabled"),
            },
        ],
        output="screen",
    )

    aruco_fusion_node = Node(
        package="button_detection_pkg",
        executable="aruco_fusion_node",
        name="aruco_fusion",
        parameters=[config_file],
        output="screen",
    )

    return LaunchDescription([
        declare_model_path,
        declare_enabled,
        declare_launch_realsense,
        realsense_launch,
        detector_node,
        aruco_fusion_node,
    ])
