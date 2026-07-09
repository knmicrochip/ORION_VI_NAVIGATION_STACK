# How to choose navigation library

### target so far: nav2

`grid-map` mam paczkę ros2 jazzy
jest już nie wspierane

`elevation_mapping` nie ma paczki ros2
już nie jest wspierane

~~[Spatio-Temporal Voxel Layer](https://github.com/SteveMacenski/spatio_temporal_voxel_layer)
https://index.ros.org/p/spatio_temporal_voxel_layer/#jazzy
`sudo apt install ros-jazzy-spatio-temporal-voxel-layer`~~

Jak zrobić bringup:
https://docs.nav2.org/tuning/index.html#nav2-launch-options


AI SLOP:
```
 # Global costmap with STVL  
    global_costmap = Node(  
        package='nav2_costmap_2d',  
        executable='costmap_2d_node',  
        name='global_costmap',  
        output='screen',  
        parameters=[{  
            'use_sim_time': LaunchConfiguration('use_sim_time'),  
            'global_costmap': {  
                'robot_base_frame': 'base_link',  
                'global_frame': 'map',  
                'update_frequency': 5.0,  
                'publish_frequency': 2.0,  
                'width': 10.0,  
                'height': 10.0,  
                'resolution': 0.05,  
                'origin_x': -5.0,  
                'origin_y': -5.0,  
                'plugins': [  
                    {'name': 'static_layer', 'type': 'nav2_costmap_2d::StaticLayer'},  
                    {'name': 'obstacle_layer', 'type': 'spatio_temporal_voxel_layer::SpatioTemporalVoxelLayer'},  
                    {'name': 'inflation_layer', 'type': 'nav2_costmap_2d::InflationLayer'}  
                ],  
                **{f'obstacle_layer.{k}': v for k, v in stvl_params.items()},  
                'inflation_layer': {  
                    'inflation_radius': 0.55,  
                    'cost_scaling_factor': 3.0  
                }  
            }  
        }]  
    )  
      
    # Local costmap with STVL  
    local_costmap = Node(  
        package='nav2_costmap_2d',  
        executable='costmap_2d_node',  
        name='local_costmap',  
        output='screen',  
        parameters=[{  
            'use_sim_time': LaunchConfiguration('use_sim_time'),  
            'local_costmap': {  
                'robot_base_frame': 'base_link',  
                'global_frame': 'odom',  
                'update_frequency': 10.0,  
                'publish_frequency': 5.0,  
                'width': 5.0,  
                'height': 5.0,  
                'resolution': 0.05,  
                'plugins': [  
                    {'name': 'obstacle_layer', 'type': 'spatio_temporal_voxel_layer::SpatioTemporalVoxelLayer'},  
                    {'name': 'inflation_layer', 'type': 'nav2_costmap_2d::InflationLayer'}  
                ],  
                **{f'obstacle_layer.{k}': v for k, v in stvl_params.items()},  
                'inflation_layer': {  
                    'inflation_radius': 0.55,  
                    'cost_scaling_factor': 3.0  
                }  
            }  
        }]  
    )  
      
```