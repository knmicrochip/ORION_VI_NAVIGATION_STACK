#!/usr/bin/env python3
"""
Export a trained YOLO model to ONNX or TensorRT for deployment on the rover.

Usage:
    python3 export_model.py --weights runs/detect/train/weights/best.pt --format onnx
    python3 export_model.py --weights ../models/best.pt --format engine --half
"""

import argparse
import shutil
import sys
from pathlib import Path


SUPPORTED_FORMATS = ("onnx", "engine", "torchscript", "openvino")


def export(args):
    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            "ultralytics is not installed.\n"
            "Install with:  pip install ultralytics",
            file=sys.stderr,
        )
        sys.exit(1)

    weights_path = Path(args.weights).resolve()
    if not weights_path.exists():
        print(f"Weights file not found: {weights_path}", file=sys.stderr)
        sys.exit(1)

    if args.format not in SUPPORTED_FORMATS:
        print(
            f"Unsupported format '{args.format}'. "
            f"Choose from: {SUPPORTED_FORMATS}",
            file=sys.stderr,
        )
        sys.exit(1)

    model = YOLO(str(weights_path))

    export_kwargs = {
        "format": args.format,
        "imgsz": args.imgsz,
        "half": args.half,
        "simplify": args.simplify,
        "dynamic": args.dynamic,
    }
    if args.format == "engine":
        export_kwargs["device"] = args.device or "0"

    exported_path = model.export(**export_kwargs)
    print(f"\nExported model: {exported_path}")

    if args.output:
        dest = Path(args.output).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(exported_path, dest)
        print(f"Copied to: {dest}")


def main():
    parser = argparse.ArgumentParser(
        description="Export YOLO model for rover deployment"
    )
    parser.add_argument(
        "--weights", type=str, required=True,
        help="Path to trained .pt weights",
    )
    parser.add_argument(
        "--format", type=str, default="onnx",
        choices=SUPPORTED_FORMATS,
        help="Export format (default: onnx)",
    )
    parser.add_argument(
        "--imgsz", type=int, default=640,
        help="Inference image size (default: 640)",
    )
    parser.add_argument(
        "--half", action="store_true",
        help="FP16 quantisation (reduces size, needs GPU support)",
    )
    parser.add_argument(
        "--simplify", action="store_true", default=True,
        help="Simplify ONNX graph (default: True)",
    )
    parser.add_argument(
        "--dynamic", action="store_true",
        help="Dynamic input shapes (ONNX only)",
    )
    parser.add_argument(
        "--device", type=str, default="",
        help="Device for TensorRT export (e.g. '0')",
    )
    parser.add_argument(
        "--output", type=str, default="",
        help="Copy exported file to this path (e.g. ../models/best.onnx)",
    )
    args = parser.parse_args()
    export(args)


if __name__ == "__main__":
    main()
