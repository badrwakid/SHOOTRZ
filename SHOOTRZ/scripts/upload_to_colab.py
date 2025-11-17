"""
Upload datasets to Google Drive for Colab training.

Helps prepare datasets for Google Colab training by uploading to Google Drive
or providing instructions for manual upload.
"""

import argparse
from pathlib import Path
import zipfile
import shutil
from typing import List


def zip_directory(source_dir: Path, output_zip: Path):
	"""
	Create a zip archive of a directory.
	
	Args:
		source_dir: Directory to zip
		output_zip: Path to output zip file
	"""
	print(f"Creating zip archive: {output_zip}")
	
	with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for file_path in source_dir.rglob('*'):
			if file_path.is_file():
				# Get relative path for archive
				arcname = file_path.relative_to(source_dir)
				zipf.write(file_path, arcname)
	
	print(f"Zip created: {output_zip} ({output_zip.stat().st_size / (1024*1024):.1f} MB)")


def prepare_for_colab(
	dataset_path: Path,
	output_dir: Path,
	create_zip: bool = True,
):
	"""
	Prepare dataset for Colab upload.
	
	Args:
		dataset_path: Path to dataset directory
		output_dir: Directory to save prepared files
		create_zip: Whether to create zip archive
	"""
	output_dir.mkdir(parents=True, exist_ok=True)
	
	if not dataset_path.exists():
		print(f"Error: Dataset path does not exist: {dataset_path}")
		return
	
	# Create zip if requested
	if create_zip:
		zip_name = dataset_path.name + ".zip"
		zip_path = output_dir / zip_name
		zip_directory(dataset_path, zip_path)
	
	# Create upload instructions
	instructions = f"""# Upload Instructions for {dataset_path.name}

## Option 1: Google Drive Upload (Recommended)

1. Upload the zip file to Google Drive:
   - Go to https://drive.google.com
   - Create folder: `SHOOTRZ_Datasets`
   - Upload: `{dataset_path.name}.zip`

2. In Colab notebook:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   
   # Extract dataset
   import zipfile
   zip_path = '/content/drive/MyDrive/SHOOTRZ_Datasets/{dataset_path.name}.zip'
   extract_path = '/content/datasets'
   with zipfile.ZipFile(zip_path, 'r') as zip_ref:
       zip_ref.extractall(extract_path)
   ```

## Option 2: Direct Upload to Colab

1. In Colab notebook, use file upload:
   ```python
   from google.colab import files
   uploaded = files.upload()  # Select {dataset_path.name}.zip
   
   # Extract
   import zipfile
   with zipfile.ZipFile('{dataset_path.name}.zip', 'r') as zip_ref:
       zip_ref.extractall('/content/datasets')
   ```

## Option 3: GitHub (for smaller datasets)

1. Push dataset to GitHub (if <100MB)
2. Clone in Colab:
   ```python
   !git clone https://github.com/yourusername/shootrz-datasets.git
   ```

## Dataset Information

- **Path**: {dataset_path}
- **Size**: {sum(f.stat().st_size for f in dataset_path.rglob('*') if f.is_file()) / (1024*1024):.1f} MB
- **Files**: {len(list(dataset_path.rglob('*')))}
"""
	
	instructions_path = output_dir / f"{dataset_path.name}_upload_instructions.md"
	with open(instructions_path, 'w') as f:
		f.write(instructions)
	
	print(f"\n=== Preparation Complete ===")
	print(f"Output directory: {output_dir}")
	if create_zip:
		print(f"Zip file: {output_dir / (dataset_path.name + '.zip')}")
	print(f"Instructions: {instructions_path}")


def main():
	parser = argparse.ArgumentParser(description="Prepare datasets for Google Colab upload")
	parser.add_argument(
		"--dataset-path",
		type=str,
		required=True,
		help="Path to dataset directory to upload",
	)
	parser.add_argument(
		"--output-dir",
		type=str,
		default="colab_uploads",
		help="Directory to save zip files and instructions",
	)
	parser.add_argument(
		"--no-zip",
		action="store_true",
		help="Skip creating zip archive",
	)
	
	args = parser.parse_args()
	
	dataset_path = Path(args.dataset_path)
	output_dir = Path(args.output_dir)
	
	if not dataset_path.exists():
		print(f"Error: Dataset path does not exist: {dataset_path}")
		return
	
	prepare_for_colab(
		dataset_path=dataset_path,
		output_dir=output_dir,
		create_zip=not args.no_zip,
	)


if __name__ == "__main__":
	main()

