from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription([
        Node(
            package='aruco_opencv',
            executable='aruco_tracker_autostart',
            parameters=[{'cam_base_topic':'/camera/camera/color/image_raw',
                         'marker_size':0.15,
                         'marker_dict':"5X5_100"
                        }]
            )
    ])
    
    return ld
