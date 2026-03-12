"""
YOLO wrapper for button/switch detection on the ERC 2026 Maintenance Panel.

Handles model loading (.pt / .onnx), inference, and post-processing.
Designed to be used by the ROS 2 detector_node but is framework-agnostic
so it can also be tested standalone.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


@dataclass
class Detection:
    """Single detected panel element."""
    class_id: int
    class_name: str
    confidence: float
    # Bounding box in pixel coordinates (x1, y1, x2, y2)
    x1: float
    y1: float
    x2: float
    y2: float
    # Depth at bbox centre (metres, NaN if unavailable)
    depth_m: float = float("nan")
    # 3D position in camera frame (metres, filled by fusion stage)
    point_3d: Optional[np.ndarray] = field(default=None, repr=False)

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1


CLASS_NAMES = [
    "main_switch_off",
    "main_switch_on",
    "lever_switch_up",
    "lever_switch_down",
    "rotary_switch",
    "socket_empty",
    "socket_plugged",
    "rotary_power_switch",
    "indicator_off",
    "indicator_on",
]


class PanelDetector:
    """Load a YOLO model and run inference on BGR images."""

    def __init__(
        self,
        model_path: str,
        confidence: float = 0.5,
        iou_threshold: float = 0.45,
        imgsz: int = 640,
        device: str = "",
        class_names: Optional[List[str]] = None,
    ):
        self._model_path = Path(model_path)
        if not self._model_path.exists():
            raise FileNotFoundError(f"Model not found: {self._model_path}")

        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.class_names = class_names or CLASS_NAMES

        from ultralytics import YOLO
        self._model = YOLO(str(self._model_path))
        if device:
            self._model.to(device)

    def detect(
        self,
        bgr_image: np.ndarray,
        depth_image: Optional[np.ndarray] = None,
        depth_scale: float = 0.001,
    ) -> List[Detection]:
        """
        Run detection on a single BGR image.

        Parameters
        ----------
        bgr_image : np.ndarray
            HxWx3 uint8 BGR image.
        depth_image : np.ndarray, optional
            HxW uint16 depth image aligned to color (raw RealSense output).
        depth_scale : float
            Multiplier to convert depth_image values to metres (D435i default 0.001).

        Returns
        -------
        List[Detection]
            Sorted by confidence descending.
        """
        results = self._model.predict(
            bgr_image,
            conf=self.confidence,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )

        detections: List[Detection] = []
        if not results or results[0].boxes is None:
            return detections

        boxes = results[0].boxes
        for box in boxes:
            xyxy = box.xyxy[0].cpu().numpy()
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())

            cls_name = (
                self.class_names[cls_id]
                if cls_id < len(self.class_names)
                else f"class_{cls_id}"
            )

            det = Detection(
                class_id=cls_id,
                class_name=cls_name,
                confidence=conf,
                x1=float(xyxy[0]),
                y1=float(xyxy[1]),
                x2=float(xyxy[2]),
                y2=float(xyxy[3]),
            )

            if depth_image is not None:
                det.depth_m = self._sample_depth(
                    depth_image, det.cx, det.cy, depth_scale
                )

            detections.append(det)

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections

    @staticmethod
    def _sample_depth(
        depth_image: np.ndarray,
        cx: float,
        cy: float,
        depth_scale: float,
        patch_radius: int = 3,
    ) -> float:
        """
        Sample depth around the bbox centre using a median patch
        to reduce noise from depth sensor.
        """
        h, w = depth_image.shape[:2]
        ix, iy = int(round(cx)), int(round(cy))

        x0 = max(0, ix - patch_radius)
        x1 = min(w, ix + patch_radius + 1)
        y0 = max(0, iy - patch_radius)
        y1 = min(h, iy + patch_radius + 1)

        patch = depth_image[y0:y1, x0:x1].astype(np.float64)
        valid = patch[patch > 0]
        if valid.size == 0:
            return float("nan")
        return float(np.median(valid) * depth_scale)

    def draw_detections(
        self,
        bgr_image: np.ndarray,
        detections: List[Detection],
    ) -> np.ndarray:
        """Draw bounding boxes and labels on a copy of the image."""
        vis = bgr_image.copy()
        for det in detections:
            color = self._class_color(det.class_id)
            pt1 = (int(det.x1), int(det.y1))
            pt2 = (int(det.x2), int(det.y2))
            cv2.rectangle(vis, pt1, pt2, color, 2)

            depth_str = f" {det.depth_m:.2f}m" if not np.isnan(det.depth_m) else ""
            label = f"{det.class_name} {det.confidence:.0%}{depth_str}"
            (tw, th), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                vis,
                (pt1[0], pt1[1] - th - 6),
                (pt1[0] + tw + 4, pt1[1]),
                color,
                -1,
            )
            cv2.putText(
                vis, label, (pt1[0] + 2, pt1[1] - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
            )
        return vis

    @staticmethod
    def _class_color(class_id: int) -> tuple:
        """Deterministic colour per class (BGR)."""
        palette = [
            (0, 0, 200),    # main_switch_off  — red
            (0, 200, 0),    # main_switch_on   — green
            (200, 100, 0),  # lever_switch_up   — teal
            (200, 0, 100),  # lever_switch_down — purple
            (0, 165, 255),  # rotary_switch     — orange
            (180, 180, 0),  # socket_empty      — cyan
            (0, 255, 255),  # socket_plugged    — yellow
            (255, 100, 50), # rotary_power      — light blue
            (100, 100, 100),# indicator_off     — grey
            (0, 255, 0),    # indicator_on      — bright green
        ]
        return palette[class_id % len(palette)]
