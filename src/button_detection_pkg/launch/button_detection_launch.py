"""
Launch file for the ERC 2026 Maintenance Panel button detection pipeline.

Starts:
  1. USB camera driver (via usb_cam, optional)
  2. RealSense D435i camera (via realsense2_camera, optional)
  3. Button detector node (YOLO inference)
  4. Panel mapper node (spatial identification + target tracking)
  5. ArUco fusion node (panel localisation + 3D coordinates)

Usage:
    # Default: USB camera + detector + panel_mapper
    ros2 launch button_detection_pkg button_detection_launch.py

    # With RealSense instead of USB camera:
    ros2 launch button_detection_pkg button_detection_launch.py \
        camera_mode:=realsense

    # Override model path and enable detection immediately:
    ros2 launch button_detection_pkg button_detection_launch.py \
        model_path:=/abs/path/to/best.pt  enabled:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, LaunchConfigurationEquals
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("button_detection_pkg")
    config_file = os.path.join(pkg_share, "config", "detection_config.yaml")
    layout_file = os.path.join(pkg_share, "config", "panel_layout.yaml")
    sequence_file = os.path.join(pkg_share, "config", "task_sequence.yaml")

    # -- Launch arguments --
    declare_model_path = DeclareLaunchArgument(
        "model_path", default_value="models/best.pt",
        description="Path to YOLO .pt or .onnx weights",
    )
    declare_enabled = DeclareLaunchArgument(
        "enabled", default_value="false",
        description="Start detection immediately",
    )
    declare_camera_mode = DeclareLaunchArgument(
        "camera_mode", default_value="usb_cam",
        description="Camera source: 'usb_cam' or 'realsense'",
    )
    declare_target_element = DeclareLaunchArgument(
        "target_element", default_value="",
        description="Initial target element to detect (e.g. 'main_switch')",
    )
    declare_video_device = DeclareLaunchArgument(
        "video_device", default_value="/dev/video0",
        description="USB camera device path",
    )

    # -- USB camera node --
    usb_cam_node = Node(
        package="usb_cam",
        executable="usb_cam_node_exe",
        name="panel_camera",
        namespace="",
        parameters=[{
            "video_device": LaunchConfiguration("video_device"),
            "image_width": 640,
            "image_height": 480,
            "framerate": 30.0,
            "pixel_format": "mjpeg2rgb",
            "camera_frame_id": "panel_camera_optical_frame",
        }],
        remappings=[
            ("image_raw", "/panel_camera/image_raw"),
            ("camera_info", "/panel_camera/camera_info"),
        ],
        output="screen",
        condition=LaunchConfigurationEquals("camera_mode", "usb_cam"),
    )

    # -- RealSense camera (fallback) --
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
        condition=LaunchConfigurationEquals("camera_mode", "realsense"),
    )

    # -- YOLO detector node --
    detector_node = Node(
        package="button_detection_pkg",
        executable="detector_node",
        name="button_detector",
        parameters=[
            config_file,
            {
                "model_path": LaunchConfiguration("model_path"),
                "enabled": LaunchConfiguration("enabled"),
                # USB camera mode: no depth by default
                "use_depth": PythonExpression([
                    "'", LaunchConfiguration("camera_mode"), "' == 'realsense'"
                ]),
            },
        ],
        output="screen",
    )

    # -- ArUco fusion node --
    aruco_fusion_node = Node(
        package="button_detection_pkg",
        executable="aruco_fusion_node",
        name="aruco_fusion",
        parameters=[config_file],
        output="screen",
    )

    # -- Panel mapper node (spatial identification + target tracking) --
    panel_mapper_node = Node(
        package="button_detection_pkg",
        executable="panel_mapper",
        name="panel_mapper",
        parameters=[
            config_file,
            {
                "panel_layout_file": layout_file,
                "task_sequence_file": sequence_file,
                "target_element": LaunchConfiguration("target_element"),
            },
        ],
        output="screen",
    )

    return LaunchDescription([
        declare_model_path,
        declare_enabled,
        declare_camera_mode,
        declare_target_element,
        declare_video_device,
        usb_cam_node,
        realsense_launch,
        detector_node,
        aruco_fusion_node,
        panel_mapper_node,
    ])
