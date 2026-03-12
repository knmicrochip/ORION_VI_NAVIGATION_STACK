#!/usr/bin/env python3
"""
RealSense D435i image capture utility for building a YOLO training dataset.

Captures synchronized RGB + depth frames and saves them with JSON metadata.
Designed for collecting images of the ERC 2026 Maintenance Task panel.

Usage:
    python3 capture_images.py --output_dir ../dataset/raw --interval 0.5
    python3 capture_images.py --output_dir ../dataset/raw --manual

Keys:
    SPACE  - capture frame (manual mode) or toggle pause (auto mode)
    S      - save current frame regardless of mode
    Q/ESC  - quit
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

try:
    import pyrealsense2 as rs
except ImportError:
    rs = None


def create_realsense_pipeline(width: int, height: int, fps: int):
    """Configure and start the RealSense D435i pipeline."""
    if rs is None:
        raise RuntimeError(
            "pyrealsense2 not installed. "
            "Install with: pip install pyrealsense2 or apt install python3-librealsense2"
        )

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
    config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)

    align = rs.align(rs.stream.color)
    profile = pipeline.start(config)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

    color_profile = profile.get_stream(rs.stream.color)
    intrinsics = color_profile.as_video_stream_profile().get_intrinsics()

    camera_info = {
        "width": intrinsics.width,
        "height": intrinsics.height,
        "fx": intrinsics.fx,
        "fy": intrinsics.fy,
        "ppx": intrinsics.ppx,
        "ppy": intrinsics.ppy,
        "model": str(intrinsics.model),
        "coeffs": intrinsics.coeffs,
        "depth_scale": depth_scale,
    }

    return pipeline, align, camera_info


def save_frame(
    output_dir: Path,
    color_image: np.ndarray,
    depth_image: np.ndarray,
    camera_info: dict,
    frame_idx: int,
):
    """Save an RGB frame, its depth map, and a metadata JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = f"frame_{frame_idx:05d}_{timestamp}"

    color_path = output_dir / "images" / f"{stem}.jpg"
    depth_path = output_dir / "depth" / f"{stem}_depth.png"
    meta_path = output_dir / "meta" / f"{stem}.json"

    cv2.imwrite(str(color_path), color_image)
    cv2.imwrite(str(depth_path), depth_image)

    metadata = {
        "frame_index": frame_idx,
        "timestamp": timestamp,
        "color_file": str(color_path.name),
        "depth_file": str(depth_path.name),
        "camera": camera_info,
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return stem


def run_capture(args):
    output_dir = Path(args.output_dir).resolve()
    for sub in ("images", "depth", "meta"):
        (output_dir / sub).mkdir(parents=True, exist_ok=True)

    pipeline, align, camera_info = create_realsense_pipeline(
        args.width, args.height, args.fps
    )

    camera_info_path = output_dir / "camera_info.json"
    with open(camera_info_path, "w") as f:
        json.dump(camera_info, f, indent=2)
    print(f"Camera intrinsics saved to {camera_info_path}")

    frame_idx = len(list((output_dir / "images").glob("*.jpg")))
    print(f"Starting from frame index {frame_idx}")

    paused = args.manual
    last_capture = 0.0

    mode_label = "MANUAL (SPACE to capture)" if args.manual else "AUTO"
    print(f"Mode: {mode_label} | Press Q/ESC to quit")

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned = align.process(frames)

            color_frame = aligned.get_color_frame()
            depth_frame = aligned.get_depth_frame()
            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET,
            )

            display = np.hstack((color_image, depth_colormap))

            status = "PAUSED" if paused else "RECORDING"
            cv2.putText(
                display, f"{status} | frames: {frame_idx}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
            )
            cv2.imshow("RealSense Capture", display)

            now = time.time()
            should_save = False

            if not paused and not args.manual:
                if now - last_capture >= args.interval:
                    should_save = True

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            elif key == ord(' '):
                if args.manual:
                    should_save = True
                else:
                    paused = not paused
            elif key == ord('s'):
                should_save = True

            if should_save:
                stem = save_frame(
                    output_dir, color_image, depth_image, camera_info, frame_idx
                )
                print(f"  Saved: {stem}")
                frame_idx += 1
                last_capture = now

    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        print(f"\nCapture complete. {frame_idx} total frames in {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="RealSense D435i capture for YOLO dataset creation"
    )
    parser.add_argument(
        "--output_dir", type=str, default="dataset/raw",
        help="Directory to save captured frames",
    )
    parser.add_argument(
        "--width", type=int, default=640,
        help="Frame width (default: 640)",
    )
    parser.add_argument(
        "--height", type=int, default=480,
        help="Frame height (default: 480)",
    )
    parser.add_argument(
        "--fps", type=int, default=30,
        help="Camera FPS (default: 30)",
    )
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="Seconds between auto-captures (default: 1.0)",
    )
    parser.add_argument(
        "--manual", action="store_true",
        help="Manual mode: press SPACE to capture each frame",
    )
    args = parser.parse_args()
    run_capture(args)


if __name__ == "__main__":
    main()
