this are notes about rtabmap 

http://official-rtab-map-forum.206.s1.nabble.com/template/NamlServlet.jtp?macro=search_page&node=1&query=aruco

http://official-rtab-map-forum.206.s1.nabble.com/Aruco-Marker-Landmarks-error-in-Localisation-after-good-mapping-td9144.html#a9196

https://github.com/introlab/rtabmap/issues/377


rtabmap doesn't publish topic with detection


```
<?xml version="1.0"?>
<launch>
  <!-- Print on the file tag_bundle1.png (with GIMP: set size in Image Settings to 160x240mm) -->
  <!-- Definition of the tag bundle is tags.yaml, make sure the camera is calibrated or adjust the size of the tag if needed -->
  <!-- The TF published by apriltag_ros should match the point cloud created by the camera -->
  <!-- Change Optimizer/Strategy below between 1 (g2o) and 2 (GTSAM), and landmark_angular_variance between 0.005 (optimize rotation) and 9999 (optimize only tag's XYZ) -->

  <!-- $ roslaunch realsense2_camera rs_camera.launch align_depth:=true -->
  <!-- $ roslaunch rtabmap_examples test_apriltag_ros.launch rgb_topic:=/camera/color/image_raw camera_info_topic:=/camera/color/camera_info -->
  <!-- $ roslaunch rtabmap_launch rtabmap.launch depth_topic:=/camera/aligned_depth_to_color/image_raw rgb_topic:=/camera/color/image_raw camera_info_topic:=/camera/color/camera_info rviz:=true rtabmap_viz:=false args:="-d -Optimizer/Strategy 1" landmark_angular_variance:=9999 -->

  <arg name="camera_frame_id"         default="camera_color_optical_frame"/>
  <arg name="rgb_topic"               default="/camera/rgb/image_rect_color" />
  <arg name="camera_info_topic"       default="/camera/rgb/camera_info" />

  <!-- Set parameters -->
  <rosparam command="load" file="$(find rtabmap_examples)/launch/config/tag_settings.yaml" ns="apriltag_ros_continuous_node" />
  <rosparam command="load" file="$(find rtabmap_examples)/launch/config/tags.yaml" ns="apriltag_ros_continuous_node" />

  <node pkg="apriltag_ros" type="apriltag_ros_continuous_node" name="apriltag_ros_continuous_node" clear_params="true" output="screen">
    <remap from="image_rect" to="$(arg rgb_topic)" />
    <remap from="camera_info" to="$(arg camera_info_topic)" />

    <param name="camera_frame" type="str" value="$(arg camera_frame_id)" />
    <param name="publish_tag_detections_image" type="bool" value="true" />      <!-- default: false -->
  </node>
</launch>

```

```
# # Definitions of tags to detect
#
# ## General remarks
#
# - All length in meters
# - Ellipsis (...) signifies that the previous element can be repeated multiple times.
#
# ## Standalone tag definitions
# ### Remarks
#
# - name is optional
#
# ### Syntax
#
# standalone_tags:
#   [
#     {id: ID, size: SIZE, name: NAME},
#     ...
#   ]
standalone_tags:
  [
  ]
# ## Tag bundle definitions
# ### Remarks
#
# - name is optional
# - x, y, z have default values of 0 thus they are optional
# - qw has default value of 1 and qx, qy, qz have default values of 0 thus they are optional
#
# ### Syntax
#
# tag_bundles:
#   [
#     {
#       name: 'CUSTOM_BUNDLE_NAME',
#       layout:
#         [
#           {id: ID, size: SIZE, x: X_POS, y: Y_POS, z: Z_POS, qw: QUAT_W_VAL, qx: QUAT_X_VAL, qy: QUAT_Y_VAL, qz: QUAT_Z_VAL},
#           ...
#         ]
#     },
#     ...
#   ]
tag_bundles:
   [
     {
       name: 'tag_bundle1',
       layout:
         [
           # for a pixel = ~8mm
           {id: 1,   size: 0.0620, x: 0.0000, y:  0.0000, z: 0, qw: 1, qx: 0, qy: 0, qz: 0},
           {id: 2,   size: 0.0620, x: 0.0770, y:  0.0000, z: 0, qw: 1, qx: 0, qy: 0, qz: 0},
           {id: 25,  size: 0.0620, x: 0.0000, y: -0.0770, z: 0, qw: 1, qx: 0, qy: 0, qz: 0},
           {id: 26,  size: 0.0620, x: 0.0770, y: -0.0770, z: 0, qw: 1, qx: 0, qy: 0, qz: 0},
           {id: 49,  size: 0.0620, x: 0.0000, y: -0.1540, z: 0, qw: 1, qx: 0, qy: 0, qz: 0},
           {id: 50,  size: 0.0620, x: 0.0770, y: -0.1540, z: 0, qw: 1, qx: 0, qy: 0, qz: 0}
         ]
     },
   ]
```

## might be old

```
Note that a marker prior parameter has been added recently to do so.

rtabmap --params | grep Marker/Priors
Param: Marker/Priors = ""                                  [World prior locations of the markers. The map will be transformed in marker's
                                                            world frame when a tag is detected. Format is the marker's ID followed by its position 
                                                            (angles in rad), markers are separated by vertical line ("id1 x y z roll pitch yaw|id2 x y z
                                                             roll pitch yaw"). Example:  "1 0 0 1 0 0 0|2 1 0 1 0 0 1.57" (marker 2 is 1 meter forward
                                                             than marker 1 with 90 deg yaw rotation).]
Param: Marker/PriorsVarianceAngular = "0.001"              [Angular variance to set on marker priors.]
Param: Marker/PriorsVarianceLinear = "0.001"               [Linear variance to set on marker priors.]


In your case, setting this:

Marker/Priors="104 10 0 0 0 0 0"

will make the map translate so that landmark 104 is on absolute pose 10 meters in x. 

```

```
2) Forgot to mention that you need to set Optimizer/PriorsIgnored to false too, while also calling update_parameters service so that rtabmap actually read again the modified rosparam:

roslaunch rtabmap_l515_bag.launch use_sim_time:=true
roslaunch aruco_multiple.launch
rosparam set /rtabmap/rtabmap/Marker/Priors "104 0 0 0 0 0 0" 
rosparam set /rtabmap/rtabmap/Optimizer/PriorsIgnored false
rosservice call /rtabmap/update_parameters 
rosbag play --clock --pause l515_with_aruco_42_seconds.bag

```

`ros2 run rtabmap_slam rtabmap --params`

```
Param: Marker/CornerRefinementMethod = "0"                 [Corner refinement method (0: None, 1: Subpixel, 2:contour, 3: AprilTag2). For OpenCV <3.3.0, this is "doCornerRefinement" parameter: set 0 for false and 1 for true.]
Param: Marker/Dictionary = "0"                             [Dictionary to use: DICT_ARUCO_4X4_50=0, DICT_ARUCO_4X4_100=1, DICT_ARUCO_4X4_250=2, DICT_ARUCO_4X4_1000=3, DICT_ARUCO_5X5_50=4, DICT_ARUCO_5X5_100=5, DICT_ARUCO_5X5_250=6, DICT_ARUCO_5X5_1000=7, DICT_ARUCO_6X6_50=8, DICT_ARUCO_6X6_100=9, DICT_ARUCO_6X6_250=10, DICT_ARUCO_6X6_1000=11, DICT_ARUCO_7X7_50=12, DICT_ARUCO_7X7_100=13, DICT_ARUCO_7X7_250=14, DICT_ARUCO_7X7_1000=15, DICT_ARUCO_ORIGINAL = 16, DICT_APRILTAG_16h5=17, DICT_APRILTAG_25h9=18, DICT_APRILTAG_36h10=19, DICT_APRILTAG_36h11=20]
Param: Marker/Length = "0"                                 [The length (m) of the markers' side. 0 means automatic marker length estimation using the depth image (the camera should look at the marker perpendicularly for initialization).]
Param: Marker/MaxDepthError = "0.01"                       [Maximum depth error between all corners of a marker when estimating the marker length (when Marker/Length is 0). The smaller it is, the more perpendicular the camera should be toward the marker to initialize the length.]
Param: Marker/MaxRange = "0.0"                             [Maximum range in which markers will be detected. <=0 for unlimited range.]
Param: Marker/MinRange = "0.0"                             [Miniminum range in which markers will be detected. <=0 for unlimited range.]
Param: Marker/Priors = ""                                  [World prior locations of the markers. The map will be transformed in marker's world frame when a tag is detected. Format is the marker's ID followed by its position (angles in rad), markers are separated by vertical line ("id1 x y z roll pitch yaw|id2 x y z roll pitch yaw"). Example:  "1 0 0 1 0 0 0|2 1 0 1 0 0 1.57" (marker 2 is 1 meter forward than marker 1 with 90 deg yaw rotation).]
Param: Marker/PriorsVarianceAngular = "0.001"              [Angular variance to set on marker priors.]
Param: Marker/PriorsVarianceLinear = "0.001"               [Linear variance to set on marker priors.]
Param: Marker/VarianceAngular = "0.01"                     [Angular variance to set on marker detections. If Marker/VarianceOrientationIgnored is enabled, it is ignored with Optimizer/Strategy=1 (g2o) and it corresponds to bearing variance with Optimizer/Strategy=2 (GTSAM).]
Param: Marker/VarianceLinear = "0.001"                     [Linear variance to set on marker detections. If Marker/VarianceOrientationIgnored is enabled and Optimizer/Strategy=2 (GTSAM): it is the variance of the range factor, with 9999 to disable range factor and to do only bearing.]
Param: Marker/VarianceOrientationIgnored = "false" 
```
```
<launch>

    <arg name="rviz" default="true" />
    <param name="/use_sim_time" value="true" />

    <node pkg="tf" type="static_transform_publisher" name="base_to_d435_1_tf"
        args="0.375 -0.35 0.825 -0.52 0.0 3.14 /base_link /d435_1_link 200" />

    <node pkg="tf" type="static_transform_publisher" name="base_to_d435_2_tf"
        args="0.375 0.35 0.825 0.52 0.0 0.0 /base_link /d435_2_link 200" />

    <node pkg="tf" type="static_transform_publisher" name="base_to_t265_tf"
        args="0.36 0.0 0.95 0.0 0.0 0.0 /base_link /t265_link 200" />

    <node pkg="tf" type="static_transform_publisher" name="base_to_d415_tf"
        args="0.36 0.02 0.92 0.0 0.0 0.0 /base_link /d415_link 200" />

    <node pkg="tf" type="static_transform_publisher" name="base_to_vlp16_tf"
        args="0.0 0.0 1.254 1.57 0.0 0.0 /base_link /velodyne 200" />

    <group ns="rtabmap">
        <node name="rtabmap" pkg="rtabmap_ros" type="rtabmap" output="screen"
            args="--delete_db_on_start">
            <remap from="rgbd_image0" to="/d435_1/rgbd_image" />
            <remap from="rgbd_image1" to="/d435_2/rgbd_image" />
            <remap from="odom" to="/t265/odom/sample" />
            <remap from="scan_cloud" to="/velodyne_points" />

            <param name="subscribe_rgb" type="bool" value="false" />
            <param name="subscribe_depth" type="bool" value="false" />
            <param name="subscribe_rgbd" type="bool" value="true" />
            <param name="subscribe_scan_cloud" type="bool" value="true" />

            <param name="odom_topic" value="/t265/odom/sample" />
            <param name="scan_cloud_topic" value="/velodyne_points" />


            <param name="odom_frame_id" type="string" value="t265_odom_frame" />
            <param name="odom_tf_angular_variance" type="double" value="0.0005" />
            <param name="odom_tf_linear_variance" type="double" value="0.0001" />
            <param name="frame_id" type="string" value="base_link" />

            <param name="rgbd_cameras" type="int" value="2" />

            <param name="Grid/FromDepth" type="string" value="false" />
            <param name="Vis/EstimationType" type="string" value="0" />

            <param name="approx_sync" type="bool" value="true" />

            <param name="cloud_noise_filtering_radius" value="0.05" />
            <param name="cloud_noise_filtering_min_neighbors" value="2" />
            <param name="Reg/Force3DoF" value="true" />


            <param name="RGBD/NeighborLinkRefining" value="true" />
            <param name="Reg/Strategy" value="1" />

            <param name="Kp/MaxFeatures" type="string" value="10000" />
            <param name="RGBD/LoopClosureReextractFeatures" type="bool" value="true" />
            <param name="Optimizer/Strategy" type="string" value="1" />
            <param name="Optimizer/PriorsIgnored" type="bool" value="false" />
            <param name="Marker/Priors" type="string"
                value="1 -3.56 1.583 0.50 0 1.5708 0|2 -1.495 1.605 4.91 0 3.14159 0" />
            <param name="Icp/VoxelSize" type="string" value="0.5" />
            <param name="Icp/MaxCorrespondenceDistance" type="string" value="0.1" />
        </node>
    </group>

    <param name="robot_description" textfile="platform.urdf" />
    <node name="joint_state_publisher" pkg="joint_state_publisher" type="joint_state_publisher" />
    <node name="robot_state_publisher" pkg="robot_state_publisher" type="robot_state_publisher" />

    <node if="$(arg rviz)" pkg="rviz" type="rviz" name="rviz" output="screen"
        args="-d mapping_2d_edited.rviz" />

    <arg name="launch_prefix" default="" />
    <arg name="node_namespace" default="apriltag_ros_continuous_node" />
    <arg name="camera_name" default="/d415" />
    <arg name="camera_frame" default="d415_link" />
    <arg name="image_topic" default="/color/image_raw" />

    <rosparam command="load"
        file="$(find apriltag_ros)/config/settings.yaml" ns="$(arg node_namespace)" />
    <rosparam command="load" file="$(find apriltag_ros)/config/tags.yaml" ns="$(arg node_namespace)" />

    <node pkg="apriltag_ros" type="apriltag_ros_continuous_node" name="$(arg node_namespace)"
        clear_params="true" output="screen" launch-prefix="$(arg launch_prefix)">
        <remap from="image_rect" to="$(arg camera_name)/$(arg image_topic)" />
        <remap from="camera_info" to="$(arg camera_name)/camera_info" />

        <param name="camera_frame" type="str" value="$(arg camera_frame)" />
        <param name="publish_tag_detections_image" type="bool" value="true" />
    </node>

</launch>
```
to jest to rtabmap

```
<param name="Optimizer/PriorsIgnored" type="bool" value="false" />
            <param name="Marker/Priors" type="string"
                value="1 -3.56 1.583 0.50 0 1.5708 0|2 -1.495 1.605 4.91 0 3.14159 0" />
```
to jest do node-a do detekcji

```
<rosparam command="load"
        file="$(find apriltag_ros)/config/settings.yaml" ns="$(arg node_namespace)" />
    <rosparam command="load" file="$(find apriltag_ros)/config/tags.yaml" ns="$(arg node_namespace)" />

```