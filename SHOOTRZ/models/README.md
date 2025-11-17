# Model Directory

This directory contains trained models for the SHOOTRZ basketball analysis system.

## Model Files

### YOLOv8 Basketball Detection Models

- **yolov8n_basketball_deepsport.pt**: Fine-tuned YOLOv8-nano model trained on DeepSport dataset
  - Classes: ball (0), player (1)
  - Training dataset: DeepSport Basketball-Instants
  - Usage: Ball and player detection in basketball videos
  - Fallback: If not found, system uses pretrained YOLOv8n with COCO classes

### Model Training

To train or retrain models:

1. **Prepare Dataset**:
   ```bash
   python scripts/convert_deepsport_to_yolo.py --deepsport-path data/pose/deepsport --output-path data/ball/deepsport_yolo
   ```

2. **Fine-tune YOLOv8**:
   ```bash
   python scripts/finetune_yolo_ball.py --dataset data/ball/deepsport_yolo/data.yaml --epochs 50 --device cpu
   ```

3. **Model will be saved to**: `models/yolov8n_basketball_deepsport.pt`

## Model Versioning

- **v1.0** (yolov8n_basketball_deepsport.pt): Initial fine-tuning on DeepSport dataset
  - Base model: YOLOv8-nano
  - Training date: 2025-01-XX
  - Dataset: DeepSport Basketball-Instants
  - Classes: 2 (ball, player)

## Model Usage

Models are automatically loaded by the backend pipeline:

- `backend/inference/ball_tracker.py` automatically detects and loads fine-tuned models
- Falls back to pretrained YOLOv8n if fine-tuned model not available
- Model path can be explicitly specified via `model_path` parameter

## Model Performance

### YOLOv8 Basketball Detection

- **mAP@0.5**: TBD (after training)
- **mAP@0.5:0.95**: TBD (after training)
- **Inference Speed**: ~30 FPS on CPU (YOLOv8n)

## Notes

- Models are not included in git (too large)
- Models should be trained on the target deployment environment when possible
- Fine-tuned models provide better accuracy for basketball-specific detection
- Pretrained models serve as fallback for development/testing

