"""
ROS 2 node for real-time button/switch detection on the ERC 2026 Maintenance Panel.

Subscribes to RealSense D435i color + aligned-depth topics, runs YOLO
inference, and publishes Detection2DArray results plus a debug visualisation.

The node can be enabled/disabled via a ``std_srvs/SetBool`` service
(``~/enable``) so it only runs when the rover switches to ``button_detect``
mode.
"""

import math
from typing import Optional

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

from sensor_msgs.msg import Image, CameraInfo
from std_srvs.srv import SetBool
from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)
from geometry_msgs.msg import Point

from button_detection_pkg.model_inference import PanelDetector, Detection


SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)


class DetectorNode(Node):
    """YOLO-based panel element detector with depth integration."""

    def __init__(self):
        super().__init__("button_detector")

        # -- Parameters --
        self.declare_parameter("model_path", "models/best.pt")
        self.declare_parameter("confidence", 0.5)
        self.declare_parameter("iou_threshold", 0.45)
        self.declare_parameter("imgsz", 640)
        self.declare_parameter("device", "")
        self.declare_parameter("depth_scale", 0.001)
        self.declare_parameter("enabled", True)
        self.declare_parameter(
            "color_topic", "/camera/color/image_raw"
        )
        self.declare_parameter(
            "depth_topic", "/camera/aligned_depth_to_color/image_raw"
        )
        self.declare_parameter(
            "camera_info_topic", "/camera/color/camera_info"
        )
        self.declare_parameter("publish_debug_image", True)

        model_path = (
            self.get_parameter("model_path").get_parameter_value().string_value
        )
        confidence = (
            self.get_parameter("confidence").get_parameter_value().double_value
        )
        iou_threshold = (
            self.get_parameter("iou_threshold")
            .get_parameter_value()
            .double_value
        )
        imgsz = (
            self.get_parameter("imgsz").get_parameter_value().integer_value
        )
        device = (
            self.get_parameter("device").get_parameter_value().string_value
        )
        self._depth_scale = (
            self.get_parameter("depth_scale")
            .get_parameter_value()
            .double_value
        )
        self._enabled = (
            self.get_parameter("enabled").get_parameter_value().bool_value
        )
        self._publish_debug = (
            self.get_parameter("publish_debug_image")
            .get_parameter_value()
            .bool_value
        )

        # -- Model --
        self.get_logger().info(f"Loading model from {model_path} ...")
        try:
            self._detector = PanelDetector(
                model_path=model_path,
                confidence=confidence,
                iou_threshold=iou_threshold,
                imgsz=imgsz,
                device=device,
            )
            self.get_logger().info("Model loaded successfully.")
        except FileNotFoundError:
            self.get_logger().warn(
                f"Model file not found at '{model_path}'. "
                "Node will start but detections require a valid model. "
                "Train a model and update the model_path parameter."
            )
            self._detector = None

        self._bridge = CvBridge()
        self._camera_intrinsics: Optional[CameraIntrinsics] = None

        # -- Subscribers (message_filters for time-sync) --
        color_topic = (
            self.get_parameter("color_topic")
            .get_parameter_value()
            .string_value
        )
        depth_topic = (
            self.get_parameter("depth_topic")
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
        self._sub_depth = Subscriber(
            self, Image, depth_topic, qos_profile=SENSOR_QOS
        )

        self._ts = ApproximateTimeSynchronizer(
            [self._sub_color, self._sub_depth],
            queue_size=5,
            slop=0.05,
        )
        self._ts.registerCallback(self._on_images)

        self._sub_cam_info = self.create_subscription(
            CameraInfo,
            camera_info_topic,
            self._on_camera_info,
            10,
        )

        # -- Publishers --
        self._pub_detections = self.create_publisher(
            Detection2DArray, "~/detections", 10
        )
        self._pub_debug = self.create_publisher(
            Image, "~/debug_image", 1
        )

        # -- Enable/disable service --
        self._srv_enable = self.create_service(
            SetBool, "~/enable", self._on_enable
        )

        self.get_logger().info(
            f"DetectorNode ready (enabled={self._enabled})."
        )

    # ------------------------------------------------------------------ #
    #  Callbacks                                                          #
    # ------------------------------------------------------------------ #

    def _on_camera_info(self, msg: CameraInfo):
        if self._camera_intrinsics is not None:
            return
        self._camera_intrinsics = CameraIntrinsics(
            fx=msg.k[0], fy=msg.k[4],
            cx=msg.k[2], cy=msg.k[5],
            width=msg.width, height=msg.height,
        )
        self.get_logger().info(
            f"Camera intrinsics received: "
            f"{self._camera_intrinsics.width}x{self._camera_intrinsics.height} "
            f"fx={self._camera_intrinsics.fx:.1f}"
        )

    def _on_images(self, color_msg: Image, depth_msg: Image):
        if not self._enabled or self._detector is None:
            return

        bgr = self._bridge.imgmsg_to_cv2(color_msg, desired_encoding="bgr8")
        depth = self._bridge.imgmsg_to_cv2(
            depth_msg, desired_encoding="passthrough"
        )

        detections = self._detector.detect(
            bgr, depth_image=depth, depth_scale=self._depth_scale
        )

        if self._camera_intrinsics is not None:
            for det in detections:
                if not math.isnan(det.depth_m):
                    det.point_3d = self._camera_intrinsics.project(
                        det.cx, det.cy, det.depth_m
                    )

        det_msg = self._build_detection_msg(detections, color_msg.header)
        self._pub_detections.publish(det_msg)

        if self._publish_debug:
            vis = self._detector.draw_detections(bgr, detections)
            debug_msg = self._bridge.cv2_to_imgmsg(vis, encoding="bgr8")
            debug_msg.header = color_msg.header
            self._pub_debug.publish(debug_msg)

    def _on_enable(self, request: SetBool.Request, response: SetBool.Response):
        self._enabled = request.data
        state = "ENABLED" if self._enabled else "DISABLED"
        self.get_logger().info(f"Detection {state}")
        response.success = True
        response.message = state
        return response

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_detection_msg(
        detections: list, header
    ) -> Detection2DArray:
        msg = Detection2DArray()
        msg.header = header

        for det in detections:
            d = Detection2D()
            d.bbox.center.position.x = det.cx
            d.bbox.center.position.y = det.cy
            d.bbox.size_x = det.width
            d.bbox.size_y = det.height

            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = str(det.class_id)
            hyp.hypothesis.score = det.confidence

            if det.point_3d is not None:
                hyp.pose.pose.position = Point(
                    x=float(det.point_3d[0]),
                    y=float(det.point_3d[1]),
                    z=float(det.point_3d[2]),
                )

            d.results.append(hyp)
            msg.detections.append(d)

        return msg


class CameraIntrinsics:
    """Pinhole camera model for pixel -> 3D projection."""

    def __init__(self, fx: float, fy: float, cx: float, cy: float,
                 width: int, height: int):
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.width = width
        self.height = height

    def project(self, px: float, py: float, depth_m: float) -> np.ndarray:
        """
        Back-project a pixel + depth to a 3D point in camera frame.

        Returns [X, Y, Z] in metres following the optical frame convention
        (Z forward, X right, Y down).
        """
        x = (px - self.cx) * depth_m / self.fx
        y = (py - self.cy) * depth_m / self.fy
        z = depth_m
        return np.array([x, y, z], dtype=np.float64)


def main(args=None):
    rclpy.init(args=args)
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
