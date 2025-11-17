"""
Download trained models from Google Colab/Drive.

Provides instructions and helper functions for downloading models
trained in Google Colab back to local machine.
"""

import argparse
from pathlib import Path
import json
from typing import Dict, List


def create_download_instructions(
	model_name: str,
	colab_path: str,
	local_path: Path,
) -> str:
	"""
	Create download instructions for Colab-trained models.
	
	Args:
		model_name: Name of the model
		colab_path: Path in Colab/Drive where model is saved
		local_path: Local path to save model
		
	Returns:
		Instructions string
	"""
	instructions = f"""# Download Instructions for {model_name}

## From Google Colab Notebook

After training completes, download the model:

```python
# In Colab notebook, after training
from google.colab import files

# Download best model
files.download('runs/pose/{model_name}/weights/best.pt')

# Or download entire training directory
!zip -r {model_name}_training.zip runs/pose/{model_name}/
files.download('{model_name}_training.zip')
```

## From Google Drive

If models are saved to Drive:

1. **Download via Colab:**
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   
   # Copy to Colab filesystem
   !cp '/content/drive/MyDrive/SHOOTRZ_Models/{model_name}/best.pt' /content/
   
   # Download
   from google.colab import files
   files.download('/content/best.pt')
   ```

2. **Download via Google Drive Web:**
   - Go to https://drive.google.com
   - Navigate to `SHOOTRZ_Models/{model_name}/`
   - Download `best.pt` or `last.pt`

## Local Setup

After downloading, place model in:
```
{local_path}
```

## Verify Model

```python
from ultralytics import YOLO
model = YOLO('{local_path / (model_name + ".pt")}')
# Should load without errors
```
"""
	
	return instructions


def create_download_script(
	models: List[Dict[str, str]],
	output_path: Path,
):
	"""
	Create a download script for multiple models.
	
	Args:
		models: List of model info dicts with 'name', 'colab_path', 'local_path'
		output_path: Path to save download script
	"""
	script_content = """#!/usr/bin/env python3
\"\"\"
Download models from Google Colab/Drive.

Run this script after training models in Colab to download them locally.
\"\"\"

import requests
from pathlib import Path
import json

# Model download configuration
MODELS = """ + json.dumps(models, indent=2) + """

def download_from_drive(drive_file_id: str, output_path: Path):
	\"\"\"
	Download file from Google Drive using file ID.
	
	Args:
		drive_file_id: Google Drive file ID
		output_path: Local path to save file
	\"\"\"
	url = f"https://drive.google.com/uc?export=download&id={drive_file_id}"
	
	response = requests.get(url, stream=True)
	response.raise_for_status()
	
	output_path.parent.mkdir(parents=True, exist_ok=True)
	
	with open(output_path, 'wb') as f:
		for chunk in response.iter_content(chunk_size=8192):
			f.write(chunk)
	
	print(f"Downloaded: {output_path}")

def main():
	\"\"\"Download all models.\"\"\"
	for model_info in MODELS:
		name = model_info['name']
		local_path = Path(model_info['local_path'])
		
		print(f"\\nDownloading {name}...")
		
		if 'drive_file_id' in model_info:
			download_from_drive(model_info['drive_file_id'], local_path)
		else:
			print(f"  Manual download required. See instructions for {name}")
			print(f"  Save to: {local_path}")

if __name__ == "__main__":
	main()
"""
	
	with open(output_path, 'w') as f:
		f.write(script_content)
	
	# Make executable (Unix)
	import os
	os.chmod(output_path, 0o755)


def main():
	parser = argparse.ArgumentParser(description="Create download instructions for Colab-trained models")
	parser.add_argument(
		"--output-dir",
		type=str,
		default="docs/colab",
		help="Directory to save download instructions",
	)
	
	args = parser.parse_args()
	
	output_dir = Path(args.output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)
	
	# Define models to download
	models = [
		{
			"name": "yolov8n_basketball_deepsport",
			"colab_path": "/content/runs/detect/yolov8n_basketball_deepsport/weights/best.pt",
			"local_path": "models/yolov8n_basketball_deepsport.pt",
		},
		{
			"name": "yolov8n_pose_basketball",
			"colab_path": "/content/runs/pose/yolov8n_pose_basketball/weights/best.pt",
			"local_path": "models/yolov8n_pose_basketball.pt",
		},
		{
			"name": "posemagic_basketball",
			"colab_path": "/content/checkpoints/posemagic_basketball_best.pth",
			"local_path": "models/posemagic_basketball.pth",
		},
	]
	
	# Create instructions for each model
	for model_info in models:
		instructions = create_download_instructions(
			model_name=model_info["name"],
			colab_path=model_info["colab_path"],
			local_path=Path(model_info["local_path"]),
		)
		
		instructions_path = output_dir / f"download_{model_info['name']}.md"
		with open(instructions_path, 'w') as f:
			f.write(instructions)
	
	# Create download script
	script_path = output_dir / "download_models.py"
	create_download_script(models, script_path)
	
	print(f"\n=== Download Instructions Created ===")
	print(f"Output directory: {output_dir}")
	print(f"Instructions: {len(models)} model download guides")
	print(f"Download script: {script_path}")


if __name__ == "__main__":
	main()

