from launch import LaunchDescription
from launch_ros.actions import Node,SetParameter

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

	# IncludeLaunchDescription(
	# PythonLaunchDescriptionSource([os.path.join(
	# 	get_package_share_directory('realsense2_camera'), 'launch'),
	# 	'/rs_launch.py']),
	# 	launch_arguments={'camera_namespace': '',
	# 					'enable_gyro': 'true',
	# 					'enable_accel': 'true',
	# 					'unite_imu_method': '2', # 2-linear_interpolation 
	# 					'enable_infra1': 'true',
	# 					'enable_infra2': 'true',
	# 					'align_depth.enable': 'true',
	# 					'enable_sync': 'true',
	# 					'rgb_camera.profile': '640x360x30'}.items(),
	# 	),