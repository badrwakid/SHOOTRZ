# Google Colab Training Guide

This guide explains how to train and fine-tune models for SHOOTRZ using Google Colab's free GPU resources.

## Prerequisites

1. **Google Account**: Sign in to [Google Colab](https://colab.research.google.com/)
2. **Google Drive**: For storing datasets and trained models
3. **Datasets**: Download and prepare datasets (see [TRAINING_GUIDE.md](./TRAINING_GUIDE.md))

## Setup

### 1. Upload Datasets to Google Drive

1. Create a folder in Google Drive: `SHOOTRZ_Datasets`
2. Upload your prepared datasets:
   - `deepsport_yolo.zip` - For YOLOv8 ball detection training
   - `basketball_pose_yolo.zip` - For YOLOv8-pose training
   - 3D pose datasets (Human3.6M, CMU MoCap) - For 3D lifting training

### 2. Open Colab Notebook

1. Go to [Google Colab](https://colab.research.google.com/)
2. Upload one of the training notebooks from `SHOOTRZ/notebooks/`:
   - `train_yolov8_ball_colab.ipynb` - Ball detection training
   - `train_yolov8_pose_colab.ipynb` - Pose estimation training
   - `train_posemagic_colab.ipynb` - 3D lifting training (when available)
   - `train_hybrik_colab.ipynb` - Alternative 3D lifting (when available)

### 3. Enable GPU

1. In Colab: `Runtime` → `Change runtime type`
2. Select `GPU` (T4 or better recommended)
3. Click `Save`

## Training Workflows

### YOLOv8 Ball Detection

1. **Mount Drive**:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```

2. **Extract Dataset**:
   ```python
   import zipfile
   dataset_zip = '/content/drive/MyDrive/SHOOTRZ_Datasets/deepsport_yolo.zip'
   with zipfile.ZipFile(dataset_zip, 'r') as zip_ref:
       zip_ref.extractall('/content/datasets')
   ```

3. **Install Dependencies**:
   ```python
   !pip install ultralytics -q
   ```

4. **Train Model**:
   ```python
   from ultralytics import YOLO
   model = YOLO('yolov8n.pt')
   results = model.train(
       data='/content/datasets/deepsport_yolo/data.yaml',
       epochs=100,
       imgsz=640,
       batch=32,
       device=0,
   )
   ```

5. **Download Model**:
   ```python
   from google.colab import files
   files.download('/content/runs/detect/yolov8n_basketball_deepsport/weights/best.pt')
   ```

### YOLOv8-Pose Training

Similar workflow, but use:
- Dataset: `basketball_pose_yolo.zip`
- Model: `yolov8n-pose.pt`
- Output: `yolov8n_pose_basketball.pt`

### 3D Pose Lifting (PoseMagic/HybrIK)

1. **Install PyTorch** (if not pre-installed):
   ```python
   !pip install torch torchvision -q
   ```

2. **Load 3D Dataset**:
   - Human3.6M or CMU MoCap sequences
   - Convert to format compatible with model

3. **Train Model**:
   - Follow model-specific training scripts
   - Monitor MPJPE (Mean Per Joint Position Error)

4. **Export Model**:
   - Save PyTorch checkpoint (`.pth`)
   - Optionally export to ONNX for faster inference

## Best Practices

### 1. Save Checkpoints Regularly

Colab sessions can timeout. Save checkpoints to Drive:
```python
import shutil
shutil.copy(
    '/content/runs/.../weights/best.pt',
    '/content/drive/MyDrive/SHOOTRZ_Models/best.pt'
)
```

### 2. Monitor Training

Use TensorBoard or built-in logging:
```python
# View training progress
%tensorboard --logdir /content/runs
```

### 3. Validate on Test Set

Always validate on held-out test set:
```python
metrics = model.val()
print(f"mAP@0.5: {metrics.box.map50:.4f}")
```

### 4. Export for Production

Export models in production-ready formats:
```python
# ONNX for faster inference
model.export(format='onnx', imgsz=640)

# TensorRT for GPU acceleration (optional)
model.export(format='engine', imgsz=640)
```

## Troubleshooting

### GPU Out of Memory

- Reduce batch size: `batch=16` or `batch=8`
- Reduce image size: `imgsz=416` instead of `640`
- Use gradient accumulation

### Session Timeout

- Save checkpoints frequently
- Use Colab Pro for longer sessions
- Resume training from last checkpoint

### Dataset Not Found

- Verify Drive is mounted correctly
- Check file paths match your Drive structure
- Re-upload dataset if corrupted

## Downloading Trained Models

After training completes:

1. **From Colab**:
   ```python
   from google.colab import files
   files.download('path/to/model.pt')
   ```

2. **From Google Drive**:
   - Navigate to `SHOOTRZ_Models/` folder
   - Download model files manually

3. **Place in Local Project**:
   - Copy to `SHOOTRZ/models/` directory
   - Models will be auto-detected by `ModelLoader`

## Next Steps

After training:

1. Download models to local `models/` directory
2. Test models using evaluation scripts
3. Integrate into production pipeline
4. Monitor performance on real videos

For more details, see:
- [TRAINING_GUIDE.md](./TRAINING_GUIDE.md) - Local training instructions
- [models/README.md](../models/README.md) - Model documentation

