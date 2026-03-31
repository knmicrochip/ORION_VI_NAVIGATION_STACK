#!/usr/bin/env python3
"""
Interactive panel calibration tool for the ERC 2026 competition prep window.

Opens a camera feed, detects ArUco markers on the maintenance panel, computes
the pixel-to-panel homography, and lets the user click on each element to
record its panel-space position.  Writes results to panel_layout.yaml.

Usage:
    python3 calibrate_panel.py \
        --camera 0 \
        --layout ../config/panel_layout.yaml \
        --aruco_dict DICT_5X5_100 \
        --marker_size 0.05

Controls:
    Left-click  — record an element position
    'n'         — advance to next element in the list
    's'         — save and exit
    'q'         — quit without saving
    'r'         — reset current element clicks
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

ARUCO_DICTS = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
}


def parse_args():
    p = argparse.ArgumentParser(description="Interactive panel calibration")
    p.add_argument("--camera", type=int, default=0, help="Camera index")
    p.add_argument(
        "--layout", required=True,
        help="Path to panel_layout.yaml (read and overwritten)",
    )
    p.add_argument("--aruco_dict", default="DICT_5X5_100")
    p.add_argument(
        "--marker_size", type=float, default=0.05,
        help="ArUco marker physical size in metres",
    )
    p.add_argument(
        "--panel_width", type=float, default=330.0,
        help="Panel width in mm",
    )
    p.add_argument(
        "--panel_height", type=float, default=450.0,
        help="Panel height in mm",
    )
    return p.parse_args()


class PanelCalibrator:
    def __init__(self, args):
        self.args = args
        self.layout_path = Path(args.layout)
        self.layout = self._load_layout()

        self.panel_w = args.panel_width
        self.panel_h = args.panel_height

        # ArUco
        dict_id = ARUCO_DICTS.get(args.aruco_dict, cv2.aruco.DICT_5X5_100)
        aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
        params = cv2.aruco.DetectorParameters()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, params)
        self.marker_half_mm = args.marker_size * 1000.0 / 2.0

        # ArUco positions from layout
        panel = self.layout.get("panel", {})
        self.aruco_positions = {}
        for mid_str, pos in panel.get("aruco_markers", {}).items():
            self.aruco_positions[int(mid_str)] = (
                float(pos["x_mm"]), float(pos["y_mm"])
            )

        # Element list to calibrate
        elements = panel.get("elements", {})
        self.element_names = list(elements.keys())
        self.element_data = elements
        self.current_idx = 0

        # Click storage
        self.click_px = None
        self.homography = None

    def _load_layout(self):
        if self.layout_path.exists():
            with open(self.layout_path) as f:
                return yaml.safe_load(f) or {}
        return {
            "panel": {
                "width_mm": 330.0,
                "height_mm": 450.0,
                "aruco_markers": {},
                "elements": {},
            }
        }

    def _save_layout(self):
        with open(self.layout_path, "w") as f:
            yaml.dump(self.layout, f, default_flow_style=False, sort_keys=False)
        print(f"Layout saved to {self.layout_path}")

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.click_px = (x, y)

    def _compute_homography(self, gray):
        corners, ids, _ = self.aruco_detector.detectMarkers(gray)
        if ids is None:
            return None, corners, ids

        pixel_pts = []
        panel_pts = []
        for i, marker_id in enumerate(ids.flatten()):
            mid = int(marker_id)
            if mid not in self.aruco_positions:
                continue
            mx, my = self.aruco_positions[mid]
            mc = corners[i][0]
            half = self.marker_half_mm
            pc = [
                [mx - half, my - half],
                [mx + half, my - half],
                [mx + half, my + half],
                [mx - half, my + half],
            ]
            for j in range(4):
                pixel_pts.append(mc[j])
                panel_pts.append(pc[j])

        if len(pixel_pts) < 4:
            return None, corners, ids

        H, _ = cv2.findHomography(
            np.array(pixel_pts, dtype=np.float64),
            np.array(panel_pts, dtype=np.float64),
            cv2.RANSAC, 5.0,
        )
        return H, corners, ids

    def _pixel_to_panel(self, H, px, py):
        pt = np.array([px, py, 1.0], dtype=np.float64)
        mapped = H @ pt
        if abs(mapped[2]) < 1e-8:
            return None
        return (mapped[0] / mapped[2], mapped[1] / mapped[2])

    def run(self):
        cap = cv2.VideoCapture(self.args.camera)
        if not cap.isOpened():
            print(f"Cannot open camera {self.args.camera}")
            sys.exit(1)

        cv2.namedWindow("Panel Calibration")
        cv2.setMouseCallback("Panel Calibration", self._mouse_callback)

        print("=== Panel Calibration Tool ===")
        print("Click on each element when prompted.")
        print("Keys: 'n' = next element, 's' = save & exit, 'q' = quit, 'r' = reset")
        print()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

            H, aruco_corners, aruco_ids = self._compute_homography(gray)
            self.homography = H

            vis = frame.copy()

            # Draw ArUco markers
            if aruco_ids is not None:
                cv2.aruco.drawDetectedMarkers(vis, aruco_corners, aruco_ids)

            # Draw panel outline if homography available
            if H is not None:
                H_inv = np.linalg.inv(H)
                panel_corners_mm = np.array([
                    [0, 0], [self.panel_w, 0],
                    [self.panel_w, self.panel_h], [0, self.panel_h],
                ], dtype=np.float64)
                panel_px = []
                for pc in panel_corners_mm:
                    pt = H_inv @ np.array([pc[0], pc[1], 1.0])
                    panel_px.append((int(pt[0] / pt[2]), int(pt[1] / pt[2])))
                for i in range(4):
                    cv2.line(vis, panel_px[i], panel_px[(i + 1) % 4], (0, 255, 0), 2)

                status = "HOMOGRAPHY OK"
                color = (0, 255, 0)
            else:
                status = "NO HOMOGRAPHY (need ArUco markers)"
                color = (0, 0, 255)

            cv2.putText(vis, status, (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Current element prompt
            if self.current_idx < len(self.element_names):
                elem_name = self.element_names[self.current_idx]
                elem = self.element_data.get(elem_name, {})
                prompt = f"Click on: {elem_name} (type: {elem.get('type', '?')})"
                cv2.putText(vis, prompt, (10, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # Show existing position if set
                if H is not None and "x_mm" in elem and "y_mm" in elem:
                    H_inv = np.linalg.inv(H)
                    pt = H_inv @ np.array([elem["x_mm"], elem["y_mm"], 1.0])
                    ex, ey = int(pt[0] / pt[2]), int(pt[1] / pt[2])
                    cv2.circle(vis, (ex, ey), 8, (0, 165, 255), 2)
                    cv2.putText(vis, elem_name, (ex + 10, ey - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
            else:
                cv2.putText(vis, "All elements calibrated! Press 's' to save.",
                            (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Draw progress
            progress = f"Element {self.current_idx + 1}/{len(self.element_names)}"
            cv2.putText(vis, progress, (10, vis.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Handle click
            if self.click_px is not None and H is not None:
                px, py = self.click_px
                panel_pt = self._pixel_to_panel(H, px, py)
                self.click_px = None

                if panel_pt and self.current_idx < len(self.element_names):
                    elem_name = self.element_names[self.current_idx]
                    x_mm, y_mm = panel_pt
                    print(
                        f"  {elem_name}: ({x_mm:.1f}, {y_mm:.1f}) mm"
                    )

                    # Update layout
                    elem = self.element_data.get(elem_name, {})
                    elem["x_mm"] = round(x_mm, 1)
                    elem["y_mm"] = round(y_mm, 1)
                    self.element_data[elem_name] = elem
                    self.layout["panel"]["elements"] = self.element_data

                    # Draw confirmation
                    cv2.circle(vis, (px, py), 10, (0, 255, 0), 3)

                    self.current_idx += 1

            cv2.imshow("Panel Calibration", vis)

            key = cv2.waitKey(30) & 0xFF
            if key == ord("q"):
                print("Quit without saving.")
                break
            elif key == ord("s"):
                self._save_layout()
                break
            elif key == ord("n"):
                if self.current_idx < len(self.element_names):
                    print(f"  Skipped: {self.element_names[self.current_idx]}")
                    self.current_idx += 1
            elif key == ord("r"):
                if self.current_idx > 0:
                    self.current_idx -= 1
                    print(f"  Reset to: {self.element_names[self.current_idx]}")

        cap.release()
        cv2.destroyAllWindows()


def main():
    args = parse_args()
    calibrator = PanelCalibrator(args)
    calibrator.run()


if __name__ == "__main__":
    main()
