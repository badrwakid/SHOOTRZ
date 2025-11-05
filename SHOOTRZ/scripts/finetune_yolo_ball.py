"""
Fine-tune YOLOv8 for basketball detection.

Trains YOLOv8-nano on DeepSport Basketball-Instants dataset for ball/hoop detection.
"""

import argparse
from pathlib import Path
from ultralytics import YOLO
import yaml


def prepare_dataset_config(dataset_path: Path, output_path: Path):
	"""
	Prepare YOLO dataset configuration.
	
	Args:
		dataset_path: Path to dataset directory
		output_path: Path to save data.yaml
	"""
	config = {
		"path": str(dataset_path.absolute()),
		"train": "images/train",
		"val": "images/val",
		"test": "images/test",
		"nc": 2,  # Number of classes: ball, hoop
		"names": ["ball", "hoop"],
	}
	
	with open(output_path, "w") as f:
		yaml.dump(config, f)
	
	print(f"Dataset config saved to: {output_path}")


def finetune_yolo(
	dataset_config: str,
	epochs: int = 50,
	batch_size: int = 16,
	image_size: int = 640,
	model_name: str = "yolov8n",
	output_dir: str = "models",
):
	"""
	Fine-tune YOLOv8 model on basketball dataset.
	
	Args:
		dataset_config: Path to dataset YAML config
		epochs: Number of training epochs
		batch_size: Batch size for training
		image_size: Input image size
		model_name: Base model name (yolov8n, yolov8s, etc.)
		output_dir: Directory to save trained model
	"""
	print(f"Fine-tuning {model_name} on basketball dataset...")
	print(f"Dataset config: {dataset_config}")
	print(f"Epochs: {epochs}, Batch size: {batch_size}, Image size: {image_size}")
	
	# Load pretrained model
	model = YOLO(f"{model_name}.pt")
	
	# Train
	results = model.train(
		data=dataset_config,
		epochs=epochs,
		imgsz=image_size,
		batch=batch_size,
		name=f"{model_name}_basketball",
		patience=10,  # Early stopping
		save=True,
		device=0,  # GPU (use "cpu" for CPU-only)
		project=output_dir,
	)
	
	# Validate
	print("\n=== Validation ===")
	metrics = model.val()
	print(f"mAP@0.5: {metrics.box.map50}")
	print(f"mAP@0.5:0.95: {metrics.box.map}")
	
	# Export trained model
	model_path = Path(output_dir) / f"{model_name}_basketball" / "weights" / "best.pt"
	if model_path.exists():
		# Copy to models directory
		import shutil
		final_path = Path(output_dir) / f"{model_name}_basketball.pt"
		shutil.copy(model_path, final_path)
		print(f"\nTrained model saved to: {final_path}")
	
	return results


def main():
	parser = argparse.ArgumentParser(description="Fine-tune YOLOv8 for basketball detection")
	parser.add_argument(
		"--dataset",
		type=str,
		required=True,
		help="Path to dataset YAML config file",
	)
	parser.add_argument(
		"--epochs",
		type=int,
		default=50,
		help="Number of training epochs",
	)
	parser.add_argument(
		"--batch-size",
		type=int,
		default=16,
		help="Batch size for training",
	)
	parser.add_argument(
		"--image-size",
		type=int,
		default=640,
		help="Input image size",
	)
	parser.add_argument(
		"--model",
		type=str,
		default="yolov8n",
		choices=["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"],
		help="Base YOLOv8 model",
	)
	parser.add_argument(
		"--output-dir",
		type=str,
		default="models",
		help="Output directory for trained model",
	)
	
	args = parser.parse_args()
	
	# Create output directory
	Path(args.output_dir).mkdir(parents=True, exist_ok=True)
	
	# Fine-tune
	finetune_yolo(
		dataset_config=args.dataset,
		epochs=args.epochs,
		batch_size=args.batch_size,
		image_size=args.image_size,
		model_name=args.model,
		output_dir=args.output_dir,
	)


if __name__ == "__main__":
	main()



