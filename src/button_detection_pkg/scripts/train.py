#!/usr/bin/env python3
"""
Training script for the ERC 2026 Maintenance Panel button detector.

Wraps Ultralytics YOLOv8/v11 with sensible defaults for a small,
panel-mounted switch detection dataset.

Usage:
    python3 train.py --data ../dataset/data.yaml
    python3 train.py --data ../dataset/data.yaml --model yolov8s.pt --epochs 200 --imgsz 640
"""

import argparse
import sys
from pathlib import Path


def train(args):
    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            "ultralytics is not installed.\n"
            "Install with:  pip install ultralytics",
            file=sys.stderr,
        )
        sys.exit(1)

    data_path = Path(args.data).resolve()
    if not data_path.exists():
        print(f"Dataset config not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    model = YOLO(args.model)

    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        exist_ok=True,
        # Augmentation tuned for close-up industrial panel images
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.3,
        degrees=15.0,
        translate=0.1,
        scale=0.3,
        flipud=0.0,       # panel is never upside-down
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        perspective=0.0005,
    )

    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"\nTraining complete. Best weights: {best_weights}")
    print(f"Copy to models/ for the ROS 2 node:\n  cp {best_weights} ../models/best.pt")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 for ERC 2026 panel button detection"
    )
    parser.add_argument(
        "--data", type=str, default="../dataset/data.yaml",
        help="Path to data.yaml",
    )
    parser.add_argument(
        "--model", type=str, default="yolov8n.pt",
        help="Pretrained model to fine-tune (yolov8n/s/m/l/x.pt)",
    )
    parser.add_argument(
        "--epochs", type=int, default=100,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--imgsz", type=int, default=640,
        help="Training image size",
    )
    parser.add_argument(
        "--batch", type=int, default=-1,
        help="Batch size (-1 = auto)",
    )
    parser.add_argument(
        "--patience", type=int, default=20,
        help="Early-stopping patience (epochs without improvement)",
    )
    parser.add_argument(
        "--device", type=str, default="",
        help="Device: '', '0', 'cpu', '0,1', etc.",
    )
    parser.add_argument(
        "--workers", type=int, default=4,
        help="Dataloader workers",
    )
    parser.add_argument(
        "--project", type=str, default="runs/detect",
        help="Project directory for results",
    )
    parser.add_argument(
        "--name", type=str, default="train",
        help="Run name inside project dir",
    )
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
