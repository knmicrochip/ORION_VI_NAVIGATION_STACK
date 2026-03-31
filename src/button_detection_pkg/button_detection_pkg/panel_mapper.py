"""
ROS 2 node that spatially identifies panel elements and tracks mission targets.

Subscribes to YOLO detections from ``detector_node`` and a camera image.
Internally detects ArUco markers on the panel image to compute a
pixel-to-panel homography, then maps each YOLO detection to a named
element in ``panel_layout.yaml``.

Published topics:
    ~/identified_elements  (vision_msgs/Detection2DArray)
    ~/panel_status         (std_msgs/String)        — JSON status of all elements
    ~/target_status        (std_msgs/String)        — JSON for current target
    ~/rectified_panel      (sensor_msgs/Image)      — bird's-eye panel view
    ~/debug_panel          (sensor_msgs/Image)      — annotated overlay

Services:
    ~/set_target           (std_srvs/Trigger-style)
    ~/advance_target       (std_srvs/Trigger)
    ~/get_element_pose     (std_srvs/Trigger-style)
"""

import json
import math
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import yaml

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
)

from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber

from geometry_msgs.msg import Point, Pose, PoseStamped, Quaternion
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String
from std_srvs.srv import Trigger
from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)

import tf2_ros

SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)

# Maps YOLO class-name prefixes to panel_layout element types.
CLASS_TO_TYPE = {
    "main_switch_off": "main_switch",
    "main_switch_on": "main_switch",
    "breaker_off": "breaker",
    "breaker_on": "breaker",
    "rotary_switch": "rotary_switch",
    "socket_empty": "socket",
    "socket_plugged": "socket",
    "rotary_power_off": "rotary_power",
    "rotary_power_on": "rotary_power",
    "indicator_off": "indicator",
    "indicator_on": "indicator",
}

# Derive element state from YOLO class name.
CLASS_TO_STATE = {
    "main_switch_off": "off",
    "main_switch_on": "on",
    "breaker_off": "off",
    "breaker_on": "on",
    "rotary_switch": "unknown",
    "socket_empty": "empty",
    "socket_plugged": "plugged",
    "rotary_power_off": "off",
    "rotary_power_on": "on",
    "indicator_off": "off",
    "indicator_on": "on",
}

# ArUco dictionary name -> cv2 constant
ARUCO_DICT_MAP = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
}


class PanelElement:
    """Expected element on the panel (from layout YAML)."""

    def __init__(self, name: str, etype: str, x_mm: float, y_mm: float,
                 tolerance_mm: float):
        self.name = name
        self.etype = etype
        self.x_mm = x_mm
        self.y_mm = y_mm
        self.tolerance_mm = tolerance_mm


class PanelMapperNode(Node):
    """Spatial identification of panel elements via ArUco homography + YOLO."""

    def __init__(self):
        super().__init__("panel_mapper")

        # -- Parameters --
        self.declare_parameter("panel_layout_file", "")
        self.declare_parameter("task_sequence_file", "")
        self.declare_parameter("aruco_dictionary", "DICT_5X5_100")
        self.declare_parameter("marker_size_m", 0.05)
        self.declare_parameter("temporal_window", 5)
        self.declare_parameter("temporal_threshold", 4)
        self.declare_parameter("target_element", "")
        self.declare_parameter("color_topic", "/panel_camera/image_raw")
        self.declare_parameter("camera_info_topic", "/panel_camera/camera_info")
        self.declare_parameter("detection_topic", "/button_detector/detections")
        self.declare_parameter("camera_frame", "panel_camera_optical_frame")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("rectified_size", 660)

        layout_file = self._get_str("panel_layout_file")
        seq_file = self._get_str("task_sequence_file")
        dict_name = self._get_str("aruco_dictionary")
        self._marker_size = (
            self.get_parameter("marker_size_m")
            .get_parameter_value().double_value
        )
        self._temp_window = (
            self.get_parameter("temporal_window")
            .get_parameter_value().integer_value
        )
        self._temp_thresh = (
            self.get_parameter("temporal_threshold")
            .get_parameter_value().integer_value
        )
        self._target_element = self._get_str("target_element")
        self._camera_frame = self._get_str("camera_frame")
        self._base_frame = self._get_str("base_frame")
        self._rect_size = (
            self.get_parameter("rectified_size")
            .get_parameter_value().integer_value
        )

        # -- Load panel layout --
        self._panel_width_mm = 330.0
        self._panel_height_mm = 450.0
        self._aruco_positions: Dict[int, Tuple[float, float]] = {}
        self._elements: List[PanelElement] = []
        if layout_file:
            self._load_layout(layout_file)

        # -- Load task sequence --
        self._task_sequence: List[Dict[str, str]] = []
        self._task_index = 0
        if seq_file:
            self._load_sequence(seq_file)

        if self._task_sequence and not self._target_element:
            self._target_element = self._task_sequence[0]["element"]

        # -- ArUco detector (internal, for homography only) --
        aruco_dict_id = ARUCO_DICT_MAP.get(dict_name, cv2.aruco.DICT_5X5_100)
        self._aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
        params = cv2.aruco.DetectorParameters()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self._aruco_detector = cv2.aruco.ArucoDetector(
            self._aruco_dict, params
        )

        self._bridge = CvBridge()
        self._camera_matrix: Optional[np.ndarray] = None
        self._dist_coeffs: Optional[np.ndarray] = None

        # Temporal state buffers: element_name -> deque of state strings
        self._state_history: Dict[str, deque] = {
            e.name: deque(maxlen=self._temp_window) for e in self._elements
        }
        self._confirmed_states: Dict[str, str] = {
            e.name: "unknown" for e in self._elements
        }

        # -- TF --
        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        # -- Subscribers --
        color_topic = self._get_str("color_topic")
        detection_topic = self._get_str("detection_topic")
        camera_info_topic = self._get_str("camera_info_topic")

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
        self._pub_identified = self.create_publisher(
            Detection2DArray, "~/identified_elements", 10
        )
        self._pub_panel_status = self.create_publisher(
            String, "~/panel_status", 10
        )
        self._pub_target_status = self.create_publisher(
            String, "~/target_status", 10
        )
        self._pub_rectified = self.create_publisher(
            Image, "~/rectified_panel", 1
        )
        self._pub_debug = self.create_publisher(
            Image, "~/debug_panel", 1
        )

        # -- Services --
        self._srv_set_target = self.create_service(
            Trigger, "~/set_target", self._on_set_target
        )
        self._srv_advance = self.create_service(
            Trigger, "~/advance_target", self._on_advance_target
        )
        self._srv_get_pose = self.create_service(
            Trigger, "~/get_element_pose", self._on_get_element_pose
        )

        # Add a parameter callback so target_element can be changed at runtime
        self.add_on_set_parameters_callback(self._on_param_change)

        self.get_logger().info(
            f"PanelMapperNode ready — {len(self._elements)} elements loaded, "
            f"target='{self._target_element}'"
        )

    # ------------------------------------------------------------------ #
    #  Loading                                                            #
    # ------------------------------------------------------------------ #

    def _get_str(self, name: str) -> str:
        return self.get_parameter(name).get_parameter_value().string_value

    def _load_layout(self, path: str):
        p = Path(path)
        if not p.exists():
            self.get_logger().warn(f"Layout file not found: {path}")
            return
        with open(p) as f:
            data = yaml.safe_load(f)

        panel = data.get("panel", {})
        self._panel_width_mm = float(panel.get("width_mm", 330.0))
        self._panel_height_mm = float(panel.get("height_mm", 450.0))

        for mid_str, pos in panel.get("aruco_markers", {}).items():
            self._aruco_positions[int(mid_str)] = (
                float(pos["x_mm"]), float(pos["y_mm"])
            )

        for name, info in panel.get("elements", {}).items():
            self._elements.append(PanelElement(
                name=name,
                etype=info["type"],
                x_mm=float(info["x_mm"]),
                y_mm=float(info["y_mm"]),
                tolerance_mm=float(info.get("tolerance_mm", 20.0)),
            ))
        self.get_logger().info(
            f"Loaded layout: {len(self._aruco_positions)} markers, "
            f"{len(self._elements)} elements"
        )

    def _load_sequence(self, path: str):
        p = Path(path)
        if not p.exists():
            self.get_logger().warn(f"Sequence file not found: {path}")
            return
        with open(p) as f:
            data = yaml.safe_load(f)
        self._task_sequence = data.get("task_sequence", [])
        self.get_logger().info(
            f"Loaded task sequence: {len(self._task_sequence)} steps"
        )

    # ------------------------------------------------------------------ #
    #  Callbacks                                                          #
    # ------------------------------------------------------------------ #

    def _on_camera_info(self, msg: CameraInfo):
        if self._camera_matrix is not None:
            return
        self._camera_matrix = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self._dist_coeffs = np.array(msg.d, dtype=np.float64)
        self.get_logger().info("Camera calibration received for panel_mapper.")

    def _on_param_change(self, params):
        from rcl_interfaces.msg import SetParametersResult
        for p in params:
            if p.name == "target_element":
                self._target_element = p.value
                self.get_logger().info(
                    f"Target element changed to: '{self._target_element}'"
                )
        return SetParametersResult(successful=True)

    def _on_synced(self, color_msg: Image, det_msg: Detection2DArray):
        bgr = self._bridge.imgmsg_to_cv2(color_msg, desired_encoding="bgr8")
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE for outdoor lighting robustness
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # --- ArUco detection for homography ---
        homography, panel_rvec, panel_tvec = self._compute_homography(gray)

        # --- Publish rectified panel image ---
        if homography is not None:
            rect_w = self._rect_size
            rect_h = int(rect_w * self._panel_height_mm / self._panel_width_mm)
            scale = rect_w / self._panel_width_mm
            H_rect = homography.copy()
            # Scale from mm to pixels in rectified image
            S = np.array([
                [scale, 0, 0],
                [0, scale, 0],
                [0, 0, 1],
            ], dtype=np.float64)
            H_display = S @ homography
            rectified = cv2.warpPerspective(bgr, H_display, (rect_w, rect_h))
            rect_msg = self._bridge.cv2_to_imgmsg(rectified, encoding="bgr8")
            rect_msg.header = color_msg.header
            self._pub_rectified.publish(rect_msg)

        # --- Map YOLO detections to panel elements ---
        identified = []
        for det in det_msg.detections:
            if not det.results:
                continue
            hyp = det.results[0]
            class_name = hyp.hypothesis.class_id
            confidence = hyp.hypothesis.score

            # Get bbox center in pixels
            cx = det.bbox.center.position.x
            cy = det.bbox.center.position.y

            # Transform to panel coordinates via homography
            if homography is None:
                continue

            panel_pt = self._pixel_to_panel(homography, cx, cy)
            if panel_pt is None:
                continue

            px_mm, py_mm = panel_pt

            # Match to nearest layout element of compatible type
            elem_type = CLASS_TO_TYPE.get(class_name, "")
            state = CLASS_TO_STATE.get(class_name, "unknown")
            matched = self._match_element(px_mm, py_mm, elem_type)

            if matched is not None:
                # Update temporal state
                self._state_history[matched.name].append(state)
                confirmed = self._get_confirmed_state(matched.name)
                self._confirmed_states[matched.name] = confirmed

                # Compute 3D position
                point_3d = None
                if panel_rvec is not None and panel_tvec is not None:
                    point_3d = self._panel_to_3d(
                        matched.x_mm, matched.y_mm,
                        panel_rvec, panel_tvec
                    )

                identified.append({
                    "element": matched,
                    "class_name": class_name,
                    "state": confirmed,
                    "confidence": confidence,
                    "panel_x_mm": px_mm,
                    "panel_y_mm": py_mm,
                    "point_3d": point_3d,
                    "bbox": det.bbox,
                })

        # --- Publish identified elements ---
        id_msg = self._build_identified_msg(identified, color_msg.header)
        self._pub_identified.publish(id_msg)

        # --- Publish panel status (JSON) ---
        status = self._build_panel_status(identified)
        status_msg = String()
        status_msg.data = json.dumps(status)
        self._pub_panel_status.publish(status_msg)

        # --- Publish target status ---
        target_info = self._build_target_status(identified)
        target_msg = String()
        target_msg.data = json.dumps(target_info)
        self._pub_target_status.publish(target_msg)

        # --- Debug image ---
        debug_img = self._draw_debug(bgr, identified, homography)
        debug_msg = self._bridge.cv2_to_imgmsg(debug_img, encoding="bgr8")
        debug_msg.header = color_msg.header
        self._pub_debug.publish(debug_msg)

    # ------------------------------------------------------------------ #
    #  Services                                                           #
    # ------------------------------------------------------------------ #

    def _on_set_target(self, request, response):
        # Trigger service doesn't carry a string field, so we read the
        # target from the 'target_element' parameter which the caller
        # should set before calling.  Alternatively, the caller just sets
        # the parameter directly.
        name = self._get_str("target_element")
        known = {e.name for e in self._elements}
        if name in known:
            self._target_element = name
            response.success = True
            response.message = f"Target set to '{name}'"
        else:
            response.success = False
            response.message = (
                f"Unknown element '{name}'. "
                f"Known: {sorted(known)}"
            )
        return response

    def _on_advance_target(self, request, response):
        if not self._task_sequence:
            response.success = False
            response.message = "No task sequence loaded"
            return response

        self._task_index += 1
        if self._task_index >= len(self._task_sequence):
            self._target_element = ""
            response.success = True
            response.message = "Task sequence complete"
            self.get_logger().info("Task sequence complete!")
            return response

        step = self._task_sequence[self._task_index]
        self._target_element = step["element"]
        response.success = True
        response.message = (
            f"Advanced to step {self._task_index + 1}/"
            f"{len(self._task_sequence)}: {self._target_element}"
        )
        self.get_logger().info(response.message)
        return response

    def _on_get_element_pose(self, request, response):
        name = self._target_element
        if not name:
            response.success = False
            response.message = "No target element set"
            return response
        response.success = True
        response.message = (
            f"Use ~/target_status topic for real-time pose of '{name}'"
        )
        return response

    # ------------------------------------------------------------------ #
    #  Homography                                                         #
    # ------------------------------------------------------------------ #

    def _compute_homography(
        self, gray: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Detect ArUco markers, compute pixel->panel-mm homography.

        Returns (H, rvec, tvec) where H maps pixel coords to panel mm,
        and rvec/tvec give the panel pose in camera frame (for 3D projection).
        Returns (None, None, None) if fewer than 1 marker is found.
        """
        corners, ids, _ = self._aruco_detector.detectMarkers(gray)
        if ids is None:
            return None, None, None

        pixel_pts = []
        panel_pts = []

        for i, marker_id in enumerate(ids.flatten()):
            mid = int(marker_id)
            if mid not in self._aruco_positions:
                continue

            mx_mm, my_mm = self._aruco_positions[mid]
            marker_corners = corners[i][0]  # 4x2 array

            # ArUco corner order: top-left, top-right, bottom-right, bottom-left
            # Marker size in mm on the panel (approximate; we use centre offset)
            half = self._marker_size * 1000.0 / 2.0  # convert m to mm
            panel_corners = np.array([
                [mx_mm - half, my_mm - half],
                [mx_mm + half, my_mm - half],
                [mx_mm + half, my_mm + half],
                [mx_mm - half, my_mm + half],
            ], dtype=np.float64)

            for j in range(4):
                pixel_pts.append(marker_corners[j])
                panel_pts.append(panel_corners[j])

        if len(pixel_pts) < 4:
            return None, None, None

        pixel_pts = np.array(pixel_pts, dtype=np.float64)
        panel_pts = np.array(panel_pts, dtype=np.float64)

        H, mask = cv2.findHomography(pixel_pts, panel_pts, cv2.RANSAC, 5.0)
        if H is None:
            return None, None, None

        # Compute panel pose (rvec, tvec) for 3D projection
        rvec, tvec = None, None
        if self._camera_matrix is not None:
            # Build 3D points: panel elements lie on Z=0 plane in panel frame
            obj_pts = np.zeros((len(panel_pts), 3), dtype=np.float64)
            obj_pts[:, 0] = panel_pts[:, 0] / 1000.0  # mm -> m
            obj_pts[:, 1] = panel_pts[:, 1] / 1000.0

            success, rvec_out, tvec_out = cv2.solvePnP(
                obj_pts, pixel_pts,
                self._camera_matrix, self._dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            if success:
                rvec = rvec_out.flatten()
                tvec = tvec_out.flatten()

        return H, rvec, tvec

    @staticmethod
    def _pixel_to_panel(
        H: np.ndarray, px: float, py: float
    ) -> Optional[Tuple[float, float]]:
        """Transform a pixel coordinate to panel-space mm via homography."""
        pt = np.array([px, py, 1.0], dtype=np.float64)
        mapped = H @ pt
        if abs(mapped[2]) < 1e-8:
            return None
        return (mapped[0] / mapped[2], mapped[1] / mapped[2])

    def _panel_to_3d(
        self, x_mm: float, y_mm: float,
        rvec: np.ndarray, tvec: np.ndarray
    ) -> Optional[List[float]]:
        """Project a panel-space mm point to 3D in camera frame."""
        R, _ = cv2.Rodrigues(rvec)
        # Panel point in panel frame (Z=0 plane, units=metres)
        p_panel = np.array([x_mm / 1000.0, y_mm / 1000.0, 0.0])
        p_cam = R @ p_panel + tvec
        return [float(p_cam[0]), float(p_cam[1]), float(p_cam[2])]

    # ------------------------------------------------------------------ #
    #  Spatial matching                                                   #
    # ------------------------------------------------------------------ #

    def _match_element(
        self, px_mm: float, py_mm: float, elem_type: str
    ) -> Optional[PanelElement]:
        """Find the nearest layout element of the given type within tolerance."""
        best = None
        best_dist = float("inf")
        for elem in self._elements:
            if elem.etype != elem_type:
                continue
            dx = px_mm - elem.x_mm
            dy = py_mm - elem.y_mm
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < elem.tolerance_mm and dist < best_dist:
                best = elem
                best_dist = dist
        return best

    # ------------------------------------------------------------------ #
    #  Temporal state filtering                                           #
    # ------------------------------------------------------------------ #

    def _get_confirmed_state(self, name: str) -> str:
        history = self._state_history.get(name, deque())
        if len(history) < self._temp_thresh:
            return self._confirmed_states.get(name, "unknown")

        # Check if the most recent state appears >= threshold times
        from collections import Counter
        counts = Counter(history)
        most_common, count = counts.most_common(1)[0]
        if count >= self._temp_thresh:
            return most_common
        return self._confirmed_states.get(name, "unknown")

    # ------------------------------------------------------------------ #
    #  Message building                                                   #
    # ------------------------------------------------------------------ #

    def _build_identified_msg(
        self, identified: List[Dict], header
    ) -> Detection2DArray:
        msg = Detection2DArray()
        msg.header = header

        for item in identified:
            elem = item["element"]
            d = Detection2D()
            d.bbox = item["bbox"]

            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = elem.name
            hyp.hypothesis.score = item["confidence"]

            if item["point_3d"] is not None:
                hyp.pose.pose.position = Point(
                    x=item["point_3d"][0],
                    y=item["point_3d"][1],
                    z=item["point_3d"][2],
                )

            d.results.append(hyp)
            msg.detections.append(d)

        return msg

    def _build_panel_status(self, identified: List[Dict]) -> Dict[str, Any]:
        elements = {}
        detected_names = set()

        for item in identified:
            elem = item["element"]
            detected_names.add(elem.name)
            entry: Dict[str, Any] = {
                "detected": True,
                "state": item["state"],
                "confidence": round(item["confidence"], 3),
                "panel_x_mm": round(item["panel_x_mm"], 1),
                "panel_y_mm": round(item["panel_y_mm"], 1),
            }
            if item["point_3d"] is not None:
                entry["position_3d"] = [
                    round(v, 4) for v in item["point_3d"]
                ]
            elements[elem.name] = entry

        # Include undetected elements
        for elem in self._elements:
            if elem.name not in detected_names:
                elements[elem.name] = {
                    "detected": False,
                    "state": self._confirmed_states.get(elem.name, "unknown"),
                }

        return {
            "panel_detected": len(identified) > 0,
            "elements_detected": len(identified),
            "elements_total": len(self._elements),
            "target_element": self._target_element,
            "task_step": self._task_index + 1 if self._task_sequence else 0,
            "task_total": len(self._task_sequence),
            "elements": elements,
        }

    def _build_target_status(self, identified: List[Dict]) -> Dict[str, Any]:
        if not self._target_element:
            return {"target": "", "found": False}

        target_state = "unknown"
        if self._task_sequence and self._task_index < len(self._task_sequence):
            target_state = self._task_sequence[self._task_index].get(
                "target_state", "unknown"
            )

        for item in identified:
            if item["element"].name == self._target_element:
                result: Dict[str, Any] = {
                    "target": self._target_element,
                    "found": True,
                    "current_state": item["state"],
                    "target_state": target_state,
                    "state_reached": (
                        item["state"] == target_state
                        or target_state == "any"
                    ),
                    "confidence": round(item["confidence"], 3),
                    "panel_x_mm": round(item["panel_x_mm"], 1),
                    "panel_y_mm": round(item["panel_y_mm"], 1),
                }
                if item["point_3d"] is not None:
                    result["position_3d"] = [
                        round(v, 4) for v in item["point_3d"]
                    ]
                return result

        return {
            "target": self._target_element,
            "found": False,
            "target_state": target_state,
        }

    # ------------------------------------------------------------------ #
    #  Debug drawing                                                      #
    # ------------------------------------------------------------------ #

    def _draw_debug(
        self, bgr: np.ndarray, identified: List[Dict],
        homography: Optional[np.ndarray]
    ) -> np.ndarray:
        vis = bgr.copy()

        for item in identified:
            elem = item["element"]
            bbox = item["bbox"]
            cx = int(bbox.center.position.x)
            cy = int(bbox.center.position.y)
            hw = int(bbox.size_x / 2)
            hh = int(bbox.size_y / 2)

            is_target = (elem.name == self._target_element)
            color = (0, 255, 255) if is_target else (0, 255, 0)
            thickness = 3 if is_target else 2

            cv2.rectangle(
                vis, (cx - hw, cy - hh), (cx + hw, cy + hh),
                color, thickness
            )

            label = f"{elem.name}: {item['state']} ({item['confidence']:.0%})"
            (tw, th), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
            )
            cv2.rectangle(
                vis,
                (cx - hw, cy - hh - th - 8),
                (cx - hw + tw + 4, cy - hh),
                color, -1,
            )
            cv2.putText(
                vis, label,
                (cx - hw + 2, cy - hh - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1,
            )

        # Draw target indicator
        if self._target_element:
            cv2.putText(
                vis,
                f"TARGET: {self._target_element}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2,
            )

        # Draw task progress
        if self._task_sequence:
            progress = (
                f"Step {self._task_index + 1}/{len(self._task_sequence)}"
            )
            cv2.putText(
                vis, progress, (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
            )

        return vis


def main(args=None):
    rclpy.init(args=args)
    node = PanelMapperNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
