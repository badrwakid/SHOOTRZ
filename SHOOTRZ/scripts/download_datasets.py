"""
Dataset download script for SHOOTRZ training and evaluation.

Downloads and organizes:
- SportsPose (3D pose pretraining)
- AthletePose3D (high-speed athletic movements)
- DeepSport Basketball-Instants (ball/hoop detection)
- SportCenter EPFL (court calibration)
"""

import argparse
import os
import sys
from pathlib import Path
import zipfile
import requests
from typing import Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_directory_structure(base_path: Path):
	"""Create data directory structure."""
	directories = [
		base_path / "pose" / "sportspose",
		base_path / "pose" / "athletepose3d",
		base_path / "ball" / "basketball-instants",
		base_path / "ball" / "sportcenter",
		base_path / "ball" / "deepsportradar",
		base_path / "pilot" / "annotated_videos",
	]
	
	for directory in directories:
		directory.mkdir(parents=True, exist_ok=True)
	
	print(f"Created directory structure under {base_path}")


def download_file(url: str, output_path: Path, description: str = ""):
	"""
	Download a file with progress tracking.
	
	Args:
		url: URL to download from
		output_path: Path to save file
		description: Description for progress messages
	"""
	print(f"Downloading {description or url}...")
	
	response = requests.get(url, stream=True)
	response.raise_for_status()
	
	total_size = int(response.headers.get("content-length", 0))
	downloaded = 0
	
	output_path.parent.mkdir(parents=True, exist_ok=True)
	
	with open(output_path, "wb") as f:
		for chunk in response.iter_content(chunk_size=8192):
			if chunk:
				f.write(chunk)
				downloaded += len(chunk)
				if total_size > 0:
					progress = (downloaded / total_size) * 100
					print(f"\r  Progress: {progress:.1f}%", end="", flush=True)
	
	print(f"\n  Saved to: {output_path}")


def extract_archive(archive_path: Path, extract_to: Path):
	"""Extract zip/tar archive."""
	print(f"Extracting {archive_path.name}...")
	
	if archive_path.suffix == ".zip":
		with zipfile.ZipFile(archive_path, "r") as zip_ref:
			zip_ref.extractall(extract_to)
		print(f"  Extracted to: {extract_to}")
	else:
		print(f"  Unsupported archive format: {archive_path.suffix}")


def download_sportspose(base_path: Path):
	"""Download SportsPose dataset."""
	print("\n=== SportsPose Dataset ===")
	print("Note: SportsPose requires manual download from the research paper.")
	print("Please download from: https://github.com/sportspose/sportspose")
	print("After downloading, place files in:", base_path / "pose" / "sportspose")
	
	# Create placeholder instructions
	instructions_path = base_path / "pose" / "sportspose" / "README.md"
	instructions_path.write_text(
		"""# SportsPose Dataset

Download instructions:
1. Visit: https://github.com/sportspose/sportspose
2. Request access to the dataset
3. Download and extract to this directory

Dataset contains ~176,000 3D poses over 24 sports subjects.
"""
	)


def download_athletepose3d(base_path: Path):
	"""Download AthletePose3D dataset."""
	print("\n=== AthletePose3D Dataset ===")
	print("Note: AthletePose3D requires manual download.")
	print("Please download from: https://github.com/CHUNYUWANG/AthletePose3D")
	
	instructions_path = base_path / "pose" / "athletepose3d" / "README.md"
	instructions_path.write_text(
		"""# AthletePose3D Dataset

Download instructions:
1. Visit: https://github.com/CHUNYUWANG/AthletePose3D
2. Follow download instructions in repository
3. Extract to this directory

Dataset contains 1.3M frames with verified 3D joints for 12 sports.
"""
	)


def download_deepsport(base_path: Path, kaggle_credentials: Optional[dict] = None):
	"""Download DeepSport Basketball-Instants dataset."""
	print("\n=== DeepSport Basketball-Instants ===")
	
	if kaggle_credentials:
		print("Downloading from Kaggle...")
		try:
			import kaggle
			
			# Set Kaggle credentials
			os.environ["KAGGLE_USERNAME"] = kaggle_credentials.get("username", "")
			os.environ["KAGGLE_KEY"] = kaggle_credentials.get("key", "")
			
			# Download dataset
			kaggle.api.dataset_download_files(
				"dataset-name",  # Replace with actual dataset name
				path=str(base_path / "ball" / "basketball-instants"),
				unzip=True,
			)
			print("  Download complete")
		except ImportError:
			print("  Kaggle API not installed. Install with: pip install kaggle")
		except Exception as e:
			print(f"  Kaggle download failed: {e}")
	else:
		print("Kaggle credentials not provided.")
		print("To download:")
		print("1. Install Kaggle API: pip install kaggle")
		print("2. Set up credentials: ~/.kaggle/kaggle.json")
		print("3. Run: kaggle datasets download -d <dataset-name>")
	
	instructions_path = base_path / "ball" / "basketball-instants" / "README.md"
	instructions_path.write_text(
		"""# DeepSport Basketball-Instants

Large dataset of basketball videos with annotations for:
- Ball location
- Shot instants
- Player positions

Used for fine-tuning YOLOv8 ball/hoop detection.
"""
	)


def download_sportcenter(base_path: Path):
	"""Download SportCenter EPFL dataset."""
	print("\n=== SportCenter EPFL ===")
	print("Note: SportCenter requires access from EPFL.")
	print("Visit: https://www.epfl.ch/labs/cvlab/data/sport-center/")
	
	instructions_path = base_path / "ball" / "sportcenter" / "README.md"
	instructions_path.write_text(
		"""# SportCenter EPFL Dataset

Contains synchronized, calibrated videos of amateur basketball matches.
Used for:
- Court calibration
- Multi-view triangulation
- Homography computation

Download from: https://www.epfl.ch/labs/cvlab/data/sport-center/
"""
	)


def download_datasets(
	base_path: str = "data",
	datasets: Optional[list] = None,
	kaggle_username: Optional[str] = None,
	kaggle_key: Optional[str] = None,
):
	"""
	Download and organize all datasets.
	
	Args:
		base_path: Base directory for data storage
		datasets: List of datasets to download (None = all)
		kaggle_username: Kaggle username for authenticated downloads
		kaggle_key: Kaggle API key
	"""
	base = Path(base_path)
	create_directory_structure(base)
	
	kaggle_creds = None
	if kaggle_username and kaggle_key:
		kaggle_creds = {"username": kaggle_username, "key": kaggle_key}
	
	download_functions = {
		"sportspose": lambda: download_sportspose(base),
		"athletepose3d": lambda: download_athletepose3d(base),
		"deepsport": lambda: download_deepsport(base, kaggle_creds),
		"sportcenter": lambda: download_sportcenter(base),
	}
	
	if datasets:
		for dataset_name in datasets:
			if dataset_name in download_functions:
				download_functions[dataset_name]()
	else:
		# Download all
		for func in download_functions.values():
			func()
	
	print("\n=== Dataset Download Complete ===")
	print(f"Datasets organized in: {base}")
	print("\nNote: Some datasets require manual download due to access restrictions.")
	print("See README.md files in each dataset directory for instructions.")


def main():
	parser = argparse.ArgumentParser(description="Download datasets for SHOOTRZ")
	parser.add_argument(
		"--base-path",
		type=str,
		default="data",
		help="Base directory for data storage",
	)
	parser.add_argument(
		"--datasets",
		nargs="+",
		choices=["sportspose", "athletepose3d", "deepsport", "sportcenter"],
		help="Specific datasets to download (default: all)",
	)
	parser.add_argument(
		"--kaggle-username",
		type=str,
		help="Kaggle username for authenticated downloads",
	)
	parser.add_argument(
		"--kaggle-key",
		type=str,
		help="Kaggle API key",
	)
	
	args = parser.parse_args()
	
	download_datasets(
		base_path=args.base_path,
		datasets=args.datasets,
		kaggle_username=args.kaggle_username,
		kaggle_key=args.kaggle_key,
	)


if __name__ == "__main__":
	main()



