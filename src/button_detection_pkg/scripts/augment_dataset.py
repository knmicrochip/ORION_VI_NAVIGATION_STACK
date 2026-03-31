#!/usr/bin/env python3
"""
Data augmentation pipeline for ERC 2026 Maintenance Panel detection.

Takes a small set of annotated images (YOLO format) and generates a larger
training dataset through geometric and photometric augmentations designed
for outdoor industrial-panel detection.

Usage:
    python3 augment_dataset.py \
        --input_dir  ../dataset/raw_annotated \
        --output_dir ../dataset/images/train \
        --labels_out ../dataset/labels/train \
        --count 500
"""

import argparse
import os
import random
import shutil
from pathlib import Path

import cv2
import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description="Augment panel detection dataset")
    p.add_argument(
        "--input_dir", required=True,
        help="Directory with source images (and matching .txt YOLO labels)",
    )
    p.add_argument("--output_dir", required=True, help="Augmented images dir")
    p.add_argument("--labels_out", required=True, help="Augmented labels dir")
    p.add_argument(
        "--count", type=int, default=500,
        help="Total augmented images to generate",
    )
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    return p.parse_args()


# ------------------------------------------------------------------ #
#  Augmentation functions                                             #
# ------------------------------------------------------------------ #

def random_brightness_contrast(img, alpha_range=(0.6, 1.4), beta_range=(-40, 40)):
    alpha = random.uniform(*alpha_range)
    beta = random.uniform(*beta_range)
    return np.clip(img.astype(np.float32) * alpha + beta, 0, 255).astype(np.uint8)


def random_hsv_jitter(img, h_gain=0.015, s_gain=0.5, v_gain=0.4):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 0] = (hsv[:, :, 0] + random.uniform(-h_gain, h_gain) * 180) % 180
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * random.uniform(1 - s_gain, 1 + s_gain), 0, 255)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * random.uniform(1 - v_gain, 1 + v_gain), 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def random_gaussian_blur(img, max_ksize=5):
    if random.random() < 0.3:
        k = random.choice([3, 5])
        return cv2.GaussianBlur(img, (k, k), 0)
    return img


def random_gaussian_noise(img, sigma_range=(5, 25)):
    if random.random() < 0.3:
        sigma = random.uniform(*sigma_range)
        noise = np.random.normal(0, sigma, img.shape).astype(np.float32)
        return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return img


def random_perspective(img, labels, strength=0.05):
    """
    Apply a random perspective warp to simulate oblique viewing angles.
    Returns the warped image and updated YOLO labels.
    """
    h, w = img.shape[:2]

    # Random perspective transform
    pts_src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    jitter = strength * min(w, h)
    pts_dst = pts_src + np.random.uniform(-jitter, jitter, (4, 2)).astype(np.float32)

    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    warped = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # Transform bounding boxes
    new_labels = []
    for label in labels:
        cls_id, cx, cy, bw, bh = label
        # Convert YOLO normalized to pixel coords
        x1 = (cx - bw / 2) * w
        y1 = (cy - bh / 2) * h
        x2 = (cx + bw / 2) * w
        y2 = (cy + bh / 2) * h

        corners = np.float32([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
        corners = corners.reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(corners, M).reshape(-1, 2)

        nx1 = max(0, transformed[:, 0].min())
        ny1 = max(0, transformed[:, 1].min())
        nx2 = min(w, transformed[:, 0].max())
        ny2 = min(h, transformed[:, 1].max())

        # Skip boxes that become too small or go out of frame
        new_w = nx2 - nx1
        new_h = ny2 - ny1
        if new_w < 8 or new_h < 8:
            continue

        # Back to YOLO normalized
        ncx = ((nx1 + nx2) / 2) / w
        ncy = ((ny1 + ny2) / 2) / h
        nbw = new_w / w
        nbh = new_h / h

        if 0 < ncx < 1 and 0 < ncy < 1:
            new_labels.append((cls_id, ncx, ncy, nbw, nbh))

    return warped, new_labels


def random_rotation(img, labels, max_angle=15):
    """Rotate image and update YOLO labels."""
    h, w = img.shape[:2]
    angle = random.uniform(-max_angle, max_angle)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    new_labels = []
    for label in labels:
        cls_id, cx, cy, bw, bh = label
        x1 = (cx - bw / 2) * w
        y1 = (cy - bh / 2) * h
        x2 = (cx + bw / 2) * w
        y2 = (cy + bh / 2) * h

        corners = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float32)
        ones = np.ones((4, 1), dtype=np.float32)
        corners_h = np.hstack([corners, ones])
        transformed = (M @ corners_h.T).T

        nx1 = max(0, transformed[:, 0].min())
        ny1 = max(0, transformed[:, 1].min())
        nx2 = min(w, transformed[:, 0].max())
        ny2 = min(h, transformed[:, 1].max())

        new_w = nx2 - nx1
        new_h = ny2 - ny1
        if new_w < 8 or new_h < 8:
            continue

        ncx = ((nx1 + nx2) / 2) / w
        ncy = ((ny1 + ny2) / 2) / h
        nbw = new_w / w
        nbh = new_h / h

        if 0 < ncx < 1 and 0 < ncy < 1:
            new_labels.append((cls_id, ncx, ncy, nbw, nbh))

    return rotated, new_labels


def random_crop_zoom(img, labels, scale_range=(0.7, 1.0)):
    """Random crop simulating zoom; updates labels."""
    h, w = img.shape[:2]
    scale = random.uniform(*scale_range)
    new_w = int(w * scale)
    new_h = int(h * scale)

    x_off = random.randint(0, w - new_w)
    y_off = random.randint(0, h - new_h)

    cropped = img[y_off:y_off + new_h, x_off:x_off + new_w]
    cropped = cv2.resize(cropped, (w, h))

    new_labels = []
    for label in labels:
        cls_id, cx, cy, bw, bh = label
        # Shift to crop coordinates
        ncx = (cx * w - x_off) / new_w
        ncy = (cy * h - y_off) / new_h
        nbw = bw * w / new_w
        nbh = bh * h / new_h

        # Clip
        x1 = max(0, ncx - nbw / 2)
        y1 = max(0, ncy - nbh / 2)
        x2 = min(1, ncx + nbw / 2)
        y2 = min(1, ncy + nbh / 2)

        clipped_w = x2 - x1
        clipped_h = y2 - y1
        if clipped_w < 0.01 or clipped_h < 0.01:
            continue

        new_labels.append((cls_id, (x1 + x2) / 2, (y1 + y2) / 2, clipped_w, clipped_h))

    return cropped, new_labels


# ------------------------------------------------------------------ #
#  Label I/O                                                          #
# ------------------------------------------------------------------ #

def read_yolo_labels(path):
    labels = []
    if not os.path.exists(path):
        return labels
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 5:
                labels.append((
                    int(parts[0]),
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3]),
                    float(parts[4]),
                ))
    return labels


def write_yolo_labels(path, labels):
    with open(path, "w") as f:
        for cls_id, cx, cy, w, h in labels:
            f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")


# ------------------------------------------------------------------ #
#  Main pipeline                                                      #
# ------------------------------------------------------------------ #

def augment_one(img, labels):
    """Apply a random combination of augmentations."""
    # Geometric (applied first so labels transform correctly)
    if random.random() < 0.5:
        img, labels = random_rotation(img, labels)
    if random.random() < 0.4:
        img, labels = random_perspective(img, labels)
    if random.random() < 0.3:
        img, labels = random_crop_zoom(img, labels)
    if random.random() < 0.5:
        img = cv2.flip(img, 1)
        labels = [(c, 1.0 - cx, cy, w, h) for c, cx, cy, w, h in labels]

    # Photometric
    img = random_brightness_contrast(img)
    if random.random() < 0.5:
        img = random_hsv_jitter(img)
    img = random_gaussian_blur(img)
    img = random_gaussian_noise(img)

    return img, labels


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    labels_out = Path(args.labels_out)
    output_dir.mkdir(parents=True, exist_ok=True)
    labels_out.mkdir(parents=True, exist_ok=True)

    # Collect source images
    image_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    sources = [
        f for f in input_dir.iterdir()
        if f.suffix.lower() in image_exts
    ]
    if not sources:
        print(f"No images found in {input_dir}")
        return

    print(f"Found {len(sources)} source image(s). Generating {args.count} augmented images...")

    # First copy originals
    idx = 0
    for src in sources:
        img = cv2.imread(str(src))
        if img is None:
            continue
        label_path = src.with_suffix(".txt")
        labels = read_yolo_labels(str(label_path))

        out_name = f"aug_{idx:05d}"
        cv2.imwrite(str(output_dir / f"{out_name}.jpg"), img)
        write_yolo_labels(str(labels_out / f"{out_name}.txt"), labels)
        idx += 1

    # Generate augmented copies
    while idx < args.count:
        src = random.choice(sources)
        img = cv2.imread(str(src))
        if img is None:
            continue
        label_path = src.with_suffix(".txt")
        labels = read_yolo_labels(str(label_path))

        aug_img, aug_labels = augment_one(img, labels)

        if not aug_labels:
            continue

        out_name = f"aug_{idx:05d}"
        cv2.imwrite(str(output_dir / f"{out_name}.jpg"), aug_img)
        write_yolo_labels(str(labels_out / f"{out_name}.txt"), aug_labels)
        idx += 1

        if idx % 100 == 0:
            print(f"  Generated {idx}/{args.count} images...")

    print(f"Done. {idx} images written to {output_dir}")


if __name__ == "__main__":
    main()
