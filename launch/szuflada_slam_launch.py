from launch import LaunchDescription
from launch_ros.actions import Node,SetParameter

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
	vo_parameters={
		'frame_id':'camera_link',
		'wait_imu_to_init':True}
		#add params to reset odom

	vo_remappings=[
		('imu', '/imu/data'),
		('left/image_rect', '/camera/infra1/image_rect_raw'),
		('left/camera_info', '/camera/infra1/camera_info'),
		('right/image_rect', '/camera/infra2/image_rect_raw'),
		('right/camera_info', '/camera/infra2/camera_info')]
	
	slam_parameters={
		'frame_id':'camera_link',
		'subscribe_depth':True,
		'subscribe_odom_info':True,
		'approx_sync':False,
		'map_filter_radius':0.0,
		'map_filter_angle':30.0	
		}

	slam_remappings=[
		('imu', '/imu/data'),
		('rgb/image', '/camera/color/image_raw'),
		('rgb/camera_info', '/camera/color/camera_info'),
		('depth/image', '/camera/aligned_depth_to_color/image_raw')]
		
	ld = LaunchDescription(
		[
		
			# SetParameter(name='unite_imu_method')

			# NIE URUCHAMIAĆ podglądu kamer w rviz2

			IncludeLaunchDescription(
			PythonLaunchDescriptionSource([os.path.join(
				get_package_share_directory('realsense2_camera'), 'launch'),
				'/rs_launch.py']),
				launch_arguments={'camera_namespace': '',
								'enable_gyro': 'true',
								'enable_accel': 'true',
								'unite_imu_method': '2', # 2-linear_interpolation 
								'enable_infra1': 'true',
								'enable_infra2': 'true',
								'align_depth.enable': 'true',
								'enable_sync': 'true',
								'rgb_camera.profile': '640x360x30'}.items(),
				),
				Node(
			package='rtabmap_odom', executable='stereo_odometry', output='screen',
			parameters=[vo_parameters],
			arguments=[''],
			remappings=vo_remappings),

				Node(
			package='rtabmap_slam', executable='rtabmap', output='screen',
			parameters=[slam_parameters],
			remappings=slam_remappings,
			arguments=['-d']),

			 # Compute quaternion of the IMU
        		Node(
            package='imu_filter_madgwick', executable='imu_filter_madgwick_node', output='screen',
            parameters=[{'use_mag': False, 
                         'world_frame':'enu', 
                         'publish_tf':False}],
            remappings=[('imu/data_raw', '/camera/imu')]),

			Node(
				package='szuflada_pkg',
				namespace='szuflada',
				executable='slam_node',
				name='szuflada',
				arguments=['']
				)
			#
			# PÓKI NIE MAMY MACIERZY TO WYWALAMY EKF
			# I UŻYWAMY ODOM ZE SLAMU
			#
			# Node(
			# 	package='robot_localization',
			# 	executable='ekf_node',
			# 	name='ekf_filter_node',
			# 	output='screen',
			# 	parameters=[
			# 		'config/szuflada_ekf.yaml' #TODO zamienić na globalną ścieszkę
			# 	]
    		# )

		]
	)

	# nav2_bringup_launch = IncludeLaunchDescription(
	# 	PythonLaunchDescriptionSource(
	# 		#można to zrobić ładniej
	# 		os.path.join(FindPackageShare(package='nav2_bringup').find('nav2_bringup'),'launch','bringup_launch.py')),

	# 		launch_arguments={
	# 			#tmp
	# 		}
	# 	)
	

	# ld.add_action(nav2_bringup_launch)

	return ld
	