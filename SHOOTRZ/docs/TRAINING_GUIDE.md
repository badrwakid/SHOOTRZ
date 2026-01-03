# Model Training Guide

This guide explains how to train and update models for the SHOOTRZ basketball analysis system.

## Prerequisites

- Python 3.8+
- PyTorch (for GPU training) or CPU-only setup
- Ultralytics YOLOv8
- DeepSport dataset converted to YOLO format

## Training YOLOv8 for Ball/Player Detection

### Step 1: Prepare Dataset

Convert DeepSport dataset to YOLO format:

```bash
cd SHOOTRZ
python scripts/convert_deepsport_to_yolo.py \
    --deepsport-path data/pose/deepsport \
    --output-path data/ball/deepsport_yolo \
    --train-ratio 0.7 \
    --val-ratio 0.2 \
    --test-ratio 0.1
```

This will:
- Parse DeepSport JSON annotations
- Convert player and ball positions to YOLO format
- Split dataset into train/val/test (70/20/10)
- Create `data.yaml` configuration file

### Step 2: Validate Dataset

Check dataset integrity:

```bash
python scripts/validate_datasets.py --yolo-path data/ball/deepsport_yolo
```

### Step 3: Train Model

Fine-tune YOLOv8 on the dataset:

```bash
python scripts/finetune_yolo_ball.py \
    --dataset data/ball/deepsport_yolo/data.yaml \
    --epochs 50 \
    --batch-size 16 \
    --image-size 640 \
    --model yolov8n \
    --device cpu
```

For GPU training, use `--device 0` (or GPU index).

### Step 4: Evaluate Model

After training, the model will be saved to `models/yolov8n_basketball_deepsport.pt`.

Validate performance:

```bash
python scripts/evaluate_on_datasets.py \
    --deepsport-path data/pose/deepsport \
    --ucf-path data/pose/ucf_sports/basketball
```

## Model Configuration

### YOLOv8 Training Parameters

- **Epochs**: 50-100 (adjust based on dataset size)
- **Batch Size**: 16 (reduce if out of memory)
- **Image Size**: 640 (standard YOLO input size)
- **Model**: yolov8n (nano, fastest) to yolov8x (largest, most accurate)

### Dataset Split

Recommended splits:
- **Train**: 70% (for learning)
- **Val**: 20% (for validation during training)
- **Test**: 10% (for final evaluation)

## Updating Models

### When to Retrain

- New dataset available
- Performance degradation detected
- New classes needed (e.g., hoop detection)
- Model accuracy improvements desired

### Retraining Process

1. **Collect New Data**: Add new annotated images to dataset
2. **Reconvert Dataset**: Run conversion script with updated data
3. **Retrain**: Run training script (can start from previous model)
4. **Validate**: Test on benchmark set
5. **Deploy**: Replace model file in `models/` directory

### Incremental Training

To continue training from existing model:

```python
from ultralytics import YOLO

# Load existing model
model = YOLO("models/yolov8n_basketball_deepsport.pt")

# Continue training
model.train(
    data="data/ball/deepsport_yolo/data.yaml",
    epochs=50,
    resume=True,  # Continue from checkpoint
)
```

## Model Deployment

### Automatic Loading

The backend automatically loads fine-tuned models:

- Checks for `models/yolov8n_basketball_deepsport.pt`
- Falls back to pretrained YOLOv8n if not found
- Model type is logged in detection results

### Manual Override

Specify model path explicitly:

```python
from backend.inference.ball_tracker import detect_and_track_ball

result = detect_and_track_ball(
    frames=frames,
    model_path="path/to/custom/model.pt",
)
```

## Performance Optimization

### Training Speed

- Use GPU if available (`--device 0`)
- Reduce batch size if memory limited
- Use smaller model (yolov8n) for faster training

### Model Accuracy

- Increase epochs for better convergence
- Use larger model (yolov8s, yolov8m) for accuracy
- Augment dataset with more diverse examples
- Fine-tune hyperparameters (learning rate, etc.)

## Troubleshooting

### Out of Memory

- Reduce batch size: `--batch-size 8`
- Use smaller model: `--model yolov8n`
- Reduce image size: `--image-size 416`

### Poor Performance

- Check dataset quality and annotations
- Increase training epochs
- Verify dataset split (enough training data)
- Check for class imbalance

### Model Not Loading

- Verify model file exists: `models/yolov8n_basketball_deepsport.pt`
- Check file permissions
- Ensure model format is compatible (YOLOv8 .pt)

## Best Practices

1. **Version Control**: Document model versions and training parameters
2. **Validation**: Always validate on separate test set
3. **Benchmarking**: Compare against baseline (pretrained model)
4. **Documentation**: Update `models/README.md` with model info
5. **Backup**: Keep previous model versions for rollback

## Next Steps

After training:
1. Run benchmark tests: `python -m pytest backend/tests/test_pipeline_benchmark.py`
2. Update model documentation in `models/README.md`
3. Test in production pipeline
4. Monitor performance metrics

