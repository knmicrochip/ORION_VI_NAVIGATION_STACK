from launch import LaunchDescription
from launch_ros.actions import Node,SetParameter

from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition

from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
	use_gazebo = LaunchConfiguration("use_gazebo")

	declare_use_gazebo_cmd = DeclareLaunchArgument(
		'use_gazebo', default_value='False', description='Whether is running in simulation mode'
	)



	ld = LaunchDescription(
		[
		


			 # Compute quaternion of the IMU
				Node(
			package='imu_filter_madgwick', executable='imu_filter_madgwick_node', output='screen',
			parameters=[{'use_mag': False, 
						 'world_frame':'enu', 
						 'publish_tf':False}],
			remappings=[('imu/data_raw', '/camera/imu')]),

		]
	)

	ld.add_action(declare_use_gazebo_cmd)
	# if not declare_use_gazebo_cmd:
	ld.add_action(
		IncludeLaunchDescription(
			PythonLaunchDescriptionSource([os.path.join(
				get_package_share_directory('realsense2_camera'), 'launch'),
				'/rs_launch.py']),
				condition=UnlessCondition(use_gazebo),
				launch_arguments={'camera_namespace': '',
								'enable_gyro': 'true',
								'enable_accel': 'true',
								'unite_imu_method': '2', # 2-linear_interpolation 
								'enable_infra1': 'true',
								'enable_infra2': 'true',
								'align_depth.enable': 'true',
								'enable_sync': 'true',
								'rgb_camera.color_profile': '640x360x30'}.items(),
				),
	)

	


	return ld
	