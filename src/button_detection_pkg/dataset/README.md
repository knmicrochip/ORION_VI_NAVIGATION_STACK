# Dataset for ERC 2026 Maintenance Panel Detection

## Overview

This directory holds the YOLO-format dataset used to train the button/switch
detector for the ERC 2026 Maintenance Task panel.

## Expected directory layout

After annotation the directory tree should look like:

```
dataset/
  data.yaml              # class names + split paths (edit paths after setup)
  images/
    train/               # ~80% of annotated images (.jpg)
    val/                 # ~10%
    test/                # ~10%
  labels/
    train/               # matching YOLO .txt files
    val/
    test/
  raw/                   # output of capture_images.py (not used directly)
    images/
    depth/
    meta/
    camera_info.json
```

Each label `.txt` shares the same stem as its image and follows the YOLO
format — one row per object:

```
<class_id> <cx> <cy> <w> <h>
```

All values are normalised to [0, 1] relative to image dimensions.

## Class IDs

| ID | Name                 | Panel element                         |
|----|----------------------|---------------------------------------|
| 0  | main_switch_off      | Main power switch in OFF position     |
| 1  | main_switch_on       | Main power switch in ON position      |
| 2  | lever_switch_up      | Lever switch flipped UP               |
| 3  | lever_switch_down    | Lever switch flipped DOWN             |
| 4  | rotary_switch        | Rotary selector (any position)        |
| 5  | socket_empty         | IEC320 C14 socket — empty             |
| 6  | socket_plugged       | IEC320 C14 socket — plug inserted     |
| 7  | rotary_power_switch  | Rotary power switch (ON or OFF)       |
| 8  | indicator_off        | LED indicator — off                   |
| 9  | indicator_on         | LED indicator — lit                   |

## Step-by-step: collecting and annotating data

### 1. Capture images

Use the RealSense capture utility:

```bash
cd src/button_detection_pkg/scripts
python3 capture_images.py --output_dir ../dataset/raw --manual
```

Aim for 500–1000 frames from varying:
- Angles: 15–45 degrees relative to the panel normal
- Distances: 30–80 cm
- Lighting: bright, dim, side-lit
- Switch positions: randomly toggle switches between captures

### 2. Annotate with Roboflow (recommended)

1. Create a free account at <https://roboflow.com/> (10 000 images on free tier).
2. Create a new project → Object Detection.
3. Upload images from `dataset/raw/images/`.
4. Draw bounding boxes using the class names above.
5. Generate a dataset version with the **YOLOv8** export format.
6. Download and unzip into `dataset/` so the `images/` and `labels/` dirs
   are populated.

### 2b. Alternative: annotate with CVAT

1. Go to <https://app.cvat.ai/> (free, self-hostable).
2. Create a task, upload images, define labels matching the class list.
3. Annotate, then export as **YOLO 1.1** format.
4. Re-organise into `images/{train,val,test}` and `labels/{train,val,test}`.

### 3. Train

```bash
cd src/button_detection_pkg/scripts
python3 train.py --data ../dataset/data.yaml --epochs 100 --model yolov8n.pt
```

### 4. Export for deployment

```bash
python3 export_model.py --weights runs/detect/train/weights/best.pt --format onnx
```

Place the exported model into `models/` for the ROS 2 node.
