from launch import LaunchDescription
from launch_ros.actions import Node,SetParameter

from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition, IfCondition

from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
	use_gazebo = LaunchConfiguration("use_gazebo")

	declare_use_gazebo_cmd = DeclareLaunchArgument(
		'use_gazebo', default_value='False', description='Whether is running in simulation mode'
	)

	declare_use_sim_time_cmd = DeclareLaunchArgument(
		'use_sim_time',
		default_value='false',
		description='Use simulation (Gazebo) clock if true',
	)

	vo_parameters={
		'frame_id':'base_link',
		'wait_imu_to_init':True}
		#add params to reset odom

	vo_remappings=[
		('imu', '/imu/data'),
		('left/image_rect', '/camera/infra1/image_rect_raw'),
		('left/camera_info', '/camera/infra1/camera_info'),
		('right/image_rect', '/camera/infra2/image_rect_raw'),
		('right/camera_info', '/camera/infra2/camera_info')]
	
	slam_parameters={
		'frame_id': 'base_link',
		'subscribe_depth':True,
		'subscribe_odom_info':True,
		'approx_sync':False,
		'map_filter_radius':0.0,
		'map_filter_angle':30.0,

		"landmark_linear_variance": 0.005, #FIX double 
		"landmark_angular_variance": 9999.0, #FIX double
		"Optimizer/PriorsIgnored": "False", #WTF! needs string 
		# "Marker/Priors":'1 -3.56 1.583 0.50 0 1.5708 0|2 -1.495 1.605 4.91 0 3.14159 0'
		# 1 0 0 1 0 0 0|2 1 0 1 0 0 1.57
		# "id1 x y z roll pitch yaw"
		"Marker/Priors":(
			'14 -1.2 0 0.1 0 0 0' + '|' +
			# '14 -1 0 2 0 0 0' 
			'12 0 0 0.1 0 0 0'
			+ '|' +
			# '12 -3.56 1.583 0.50 0 1.5708 0' + '|' +
			# '13 -1.495 1.605 4.91 0 3.14159 0' + '|' +
			f"13 {6*0.6 + 0.53 + 0.495} {-7*0.6 - 0.29} 0.1 0 0 1.5708"
		)
		}

	slam_remappings=[
		('imu', '/imu/data'),
		('rgb/image', '/camera/color/image_raw'),
		('rgb/camera_info', '/camera/color/camera_info'),
		('depth/image', '/camera/aligned_depth_to_color/image_raw'),
		# ("tag_detections", LaunchConfiguration('tag_topic')),  #FIX
		('aruco_opencv/detections', '/aruco_detections')
		]
		
	ld = LaunchDescription(
		[
			declare_use_gazebo_cmd,
			declare_use_sim_time_cmd,
			# SetParameter(name='unite_imu_method')

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
            IncludeLaunchDescription(
				PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("orion_vi_bringup_pkg"),'launch','camera_launch.py')
                ),
                condition=UnlessCondition(use_gazebo),
			),
		]
	)





	return ld
	