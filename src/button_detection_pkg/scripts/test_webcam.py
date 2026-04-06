#!/usr/bin/env python3
"""
Quick webcam test for the trained YOLOv8 panel detection model.

Usage:
    python3 test_webcam.py
    python3 test_webcam.py --model ../models/best.pt --camera 0
    python3 test_webcam.py --confidence 0.3

Keys:
    q  - quit
    s  - save screenshot
"""

import argparse
import sys
from pathlib import Path

import cv2


def main():
    parser = argparse.ArgumentParser(description="Test panel detection with webcam")
    parser.add_argument("--model", type=str, default="../models/best.pt",
                        help="Path to YOLO weights")
    parser.add_argument("--camera", type=int, default=0,
                        help="Camera index (0 = default webcam)")
    parser.add_argument("--confidence", type=float, default=0.5,
                        help="Detection confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Inference image size")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        # Try relative to script location
        model_path = Path(__file__).parent / args.model
    if not model_path.exists():
        print(f"Model not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Install ultralytics: pip install ultralytics", file=sys.stderr)
        sys.exit(1)

    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print(f"Cannot open camera {args.camera}", file=sys.stderr)
        sys.exit(1)

    print(f"Model: {model_path}")
    print(f"Camera: {args.camera}")
    print(f"Confidence: {args.confidence}")
    print("Press 'q' to quit, 's' to save screenshot")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=args.confidence, imgsz=args.imgsz,
                                verbose=False)
        annotated = results[0].plot()

        cv2.imshow("Panel Detection - Press Q to quit", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            fname = f"screenshot_{frame_count:04d}.jpg"
            cv2.imwrite(fname, annotated)
            print(f"Saved {fname}")
            frame_count += 1

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
