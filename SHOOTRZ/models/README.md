# Models

This directory contains references to the AI model architectures used in SHOOTRZ.

## Pose Estimation
- **MediaPipe Pose** — installed via `pip install mediapipe` (no local clone needed)
- HRNet reference: https://github.com/HRNet/deep-high-resolution-net.pytorch

## Ball Detection
- **YOLOv8** — installed via `pip install ultralytics` (no local clone needed)
- Ultralytics reference: https://github.com/ultralytics/ultralytics
- Pre-trained weights (`yolov8n.pt`) are downloaded automatically by ultralytics on first use

## Model Weights
Model weight files (`.pt`, `.pth`, `.onnx`) are excluded from git via `.gitignore`.
They are downloaded automatically by the `ultralytics` package or regenerated via training scripts.
