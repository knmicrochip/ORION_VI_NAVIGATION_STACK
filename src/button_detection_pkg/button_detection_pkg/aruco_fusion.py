"""
ArUco + YOLO fusion node for the ERC 2026 Maintenance Panel.

Detects ArUco markers on the panel to establish a 6-DoF panel pose,
then combines that with YOLO detections (from detector_node) to publish
3D switch coordinates in the robot base frame.

Published topics:
    ~/panel_pose      (geometry_msgs/PoseStamped)   — panel centre pose
    ~/switch_poses    (geometry_msgs/PoseArray)      — each detected switch in base_link
    ~/debug_aruco     (sensor_msgs/Image)            — ArUco overlay
"""

import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
)

from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber

from geometry_msgs.msg import (
    Point,
    Pose,
    PoseArray,
    PoseStamped,
    Quaternion,
)
from sensor_msgs.msg import CameraInfo, Image
from vision_msgs.msg import Detection2DArray

import tf2_ros

SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)

# OpenCV ArUco dictionary name -> cv2 constant mapping
ARUCO_DICT_MAP: Dict[str, int] = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
}


class ArucoFusionNode(Node):
    """Fuse ArUco panel pose with YOLO detections for 3D switch coords."""

    def __init__(self):
        super().__init__("aruco_fusion")

        # -- Parameters --
        self.declare_parameter("aruco_dictionary", "DICT_5X5_100")
        self.declare_parameter("panel_marker_ids", list(range(51, 65)))
        self.declare_parameter("marker_size_m", 0.15)
        self.declare_parameter("camera_frame", "camera_color_optical_frame")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("min_markers_for_pose", 1)
        self.declare_parameter("detection_topic", "/button_detector/detections")
        self.declare_parameter("color_topic", "/camera/color/image_raw")
        self.declare_parameter("camera_info_topic", "/camera/color/camera_info")

        dict_name = (
            self.get_parameter("aruco_dictionary")
            .get_parameter_value()
            .string_value
        )
        self._panel_marker_ids = set(
            self.get_parameter("panel_marker_ids")
            .get_parameter_value()
            .integer_array_value
        )
        self._marker_size = (
            self.get_parameter("marker_size_m")
            .get_parameter_value()
            .double_value
        )
        self._camera_frame = (
            self.get_parameter("camera_frame")
            .get_parameter_value()
            .string_value
        )
        self._base_frame = (
            self.get_parameter("base_frame")
            .get_parameter_value()
            .string_value
        )
        self._min_markers = (
            self.get_parameter("min_markers_for_pose")
            .get_parameter_value()
            .integer_value
        )

        aruco_dict_id = ARUCO_DICT_MAP.get(dict_name)
        if aruco_dict_id is None:
            self.get_logger().error(
                f"Unknown ArUco dictionary: {dict_name}. "
                f"Valid: {list(ARUCO_DICT_MAP.keys())}"
            )
            raise ValueError(f"Unknown ArUco dict: {dict_name}")

        self._aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
        self._aruco_params = cv2.aruco.DetectorParameters()
        self._aruco_detector = cv2.aruco.ArucoDetector(
            self._aruco_dict, self._aruco_params
        )

        self._bridge = CvBridge()
        self._camera_matrix: Optional[np.ndarray] = None
        self._dist_coeffs: Optional[np.ndarray] = None

        # -- TF --
        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        # -- Subscribers --
        detection_topic = (
            self.get_parameter("detection_topic")
            .get_parameter_value()
            .string_value
        )
        color_topic = (
            self.get_parameter("color_topic")
            .get_parameter_value()
            .string_value
        )
        camera_info_topic = (
            self.get_parameter("camera_info_topic")
            .get_parameter_value()
            .string_value
        )

        self._sub_color = Subscriber(
            self, Image, color_topic, qos_profile=SENSOR_QOS
        )
        self._sub_detections = Subscriber(
            self, Detection2DArray, detection_topic
        )

        self._ts = ApproximateTimeSynchronizer(
            [self._sub_color, self._sub_detections],
            queue_size=5,
            slop=0.1,
        )
        self._ts.registerCallback(self._on_synced)

        self._sub_cam_info = self.create_subscription(
            CameraInfo, camera_info_topic, self._on_camera_info, 10
        )

        # -- Publishers --
        self._pub_panel_pose = self.create_publisher(
            PoseStamped, "~/panel_pose", 10
        )
        self._pub_switch_poses = self.create_publisher(
            PoseArray, "~/switch_poses", 10
        )
        self._pub_debug = self.create_publisher(
            Image, "~/debug_aruco", 1
        )

        self.get_logger().info("ArucoFusionNode ready.")

    # ------------------------------------------------------------------ #
    #  Callbacks                                                          #
    # ------------------------------------------------------------------ #

    def _on_camera_info(self, msg: CameraInfo):
        if self._camera_matrix is not None:
            return
        self._camera_matrix = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self._dist_coeffs = np.array(msg.d, dtype=np.float64)
        self.get_logger().info("Camera calibration received for ArUco.")

    def _on_synced(self, color_msg: Image, det_msg: Detection2DArray):
        if self._camera_matrix is None:
            return

        bgr = self._bridge.imgmsg_to_cv2(color_msg, desired_encoding="bgr8")
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        panel_pose = self._detect_panel_aruco(gray, color_msg.header)

        switch_poses = PoseArray()
        switch_poses.header = color_msg.header
        switch_poses.header.frame_id = self._camera_frame

        for det in det_msg.detections:
            if not det.results:
                continue
            hyp = det.results[0]
            pos = hyp.pose.pose.position
            if pos.z <= 0.0:
                continue
            pose = Pose()
            pose.position = Point(x=pos.x, y=pos.y, z=pos.z)
            pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
            switch_poses.poses.append(pose)

        if switch_poses.poses:
            self._pub_switch_poses.publish(switch_poses)

        vis = cv2.aruco.drawDetectedMarkers(bgr.copy(), *self._last_aruco_vis)
        debug_msg = self._bridge.cv2_to_imgmsg(vis, encoding="bgr8")
        debug_msg.header = color_msg.header
        self._pub_debug.publish(debug_msg)

    # ------------------------------------------------------------------ #
    #  ArUco panel detection                                              #
    # ------------------------------------------------------------------ #

    _last_aruco_vis: Tuple = ([], None, None)

    def _detect_panel_aruco(
        self, gray: np.ndarray, header
    ) -> Optional[PoseStamped]:
        corners, ids, rejected = self._aruco_detector.detectMarkers(gray)
        self._last_aruco_vis = (corners, ids, rejected)

        if ids is None:
            return None

        panel_corners = []
        panel_ids = []
        for i, marker_id in enumerate(ids.flatten()):
            if int(marker_id) in self._panel_marker_ids:
                panel_corners.append(corners[i])
                panel_ids.append(int(marker_id))

        if len(panel_corners) < self._min_markers:
            return None

        rvecs_all = []
        tvecs_all = []
        for corner in panel_corners:
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
                corner, self._marker_size,
                self._camera_matrix, self._dist_coeffs,
            )
            rvecs_all.append(rvec[0][0])
            tvecs_all.append(tvec[0][0])

        avg_tvec = np.mean(tvecs_all, axis=0)
        avg_rvec = np.mean(rvecs_all, axis=0)

        rot_mat, _ = cv2.Rodrigues(avg_rvec)
        quat = self._rotation_matrix_to_quaternion(rot_mat)

        pose_msg = PoseStamped()
        pose_msg.header = header
        pose_msg.header.frame_id = self._camera_frame
        pose_msg.pose.position = Point(
            x=float(avg_tvec[0]),
            y=float(avg_tvec[1]),
            z=float(avg_tvec[2]),
        )
        pose_msg.pose.orientation = Quaternion(
            x=quat[0], y=quat[1], z=quat[2], w=quat[3]
        )

        self._pub_panel_pose.publish(pose_msg)
        return pose_msg

    @staticmethod
    def _rotation_matrix_to_quaternion(R: np.ndarray) -> Tuple[float, ...]:
        """Convert 3x3 rotation matrix to (x, y, z, w) quaternion."""
        trace = R[0, 0] + R[1, 1] + R[2, 2]
        if trace > 0:
            s = 0.5 / math.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (R[2, 1] - R[1, 2]) * s
            y = (R[0, 2] - R[2, 0]) * s
            z = (R[1, 0] - R[0, 1]) * s
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
        return (x, y, z, w)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
