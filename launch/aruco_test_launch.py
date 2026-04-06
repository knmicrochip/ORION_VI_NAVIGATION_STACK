# from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node,SetParameter

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

import os
from ament_index_python.packages import get_package_share_directory

from launch.actions import (
	DeclareLaunchArgument,
	GroupAction,
	IncludeLaunchDescription
)

def generate_launch_description():

	bringup_dir = get_package_share_directory('orion_vi_bringup_pkg')
	bringup_launch_dir = os.path.join(bringup_dir, 'launch')

	namespace = LaunchConfiguration('namespace')

	declare_namespace_cmd = DeclareLaunchArgument(
		'namespace', default_value='', description='Top-level namespace'
	)

	camera_stack = GroupAction(
		[
			IncludeLaunchDescription(
				PythonLaunchDescriptionSource([os.path.join(
					get_package_share_directory('realsense2_camera'), 'launch'),
					'/rs_launch.py']),
					launch_arguments={'camera_namespace': 'camera', #TODO lepej zrobić topiki
									'enable_gyro': 'false',
									'enable_accel': 'false',
									'unite_imu_method': '0',
									'align_depth.enable': 'false',
									'enable_sync': 'true',
									'rgb_camera.profile': '640x360x30'}.items(),
			),
			IncludeLaunchDescription(
					PythonLaunchDescriptionSource(
						os.path.join(bringup_launch_dir, 'aruco_launch.py')
					),
					# condition=IfCondition(PythonExpression([slam, ' and ', use_localization])),
					# launch_arguments={
					# 	'namespace': namespace
					# }.items(),
			),
		]
	)

	ld = LaunchDescription()

	ld.add_action(camera_stack)

	return ld