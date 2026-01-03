"""
Prepare 3D pose datasets for PoseMagic/HybrIK training.

Downloads and organizes 3D pose datasets (Human3.6M, CMU MoCap, etc.)
for training 3D pose lifting models.
"""

import argparse
from pathlib import Path
from typing import List, Dict
import json


def download_human36m_info(output_path: Path) -> Dict:
	"""
	Provide information about Human3.6M dataset download.
	
	Args:
		output_path: Path to save dataset
		
	Returns:
		Dict with download instructions
	"""
	info = {
		"dataset": "Human3.6M",
		"url": "http://vision.imar.ro/human3.6m/",
		"license": "Research use only",
		"size": "~50 GB",
		"format": "2D/3D keypoints, images, videos",
		"instructions": [
			"1. Register at http://vision.imar.ro/human3.6m/",
			"2. Request access to dataset",
			"3. Download and extract to: " + str(output_path / "human36m"),
			"4. Dataset includes 3D joint positions for various actions",
		],
	}
	
	readme_path = output_path / "human36m" / "README.md"
	readme_path.parent.mkdir(parents=True, exist_ok=True)
	
	with open(readme_path, 'w') as f:
		f.write(f"""# Human3.6M Dataset

{info['dataset']}

## Download Instructions

{chr(10).join(info['instructions'])}

## Dataset Information

- **URL**: {info['url']}
- **License**: {info['license']}
- **Size**: {info['size']}
- **Format**: {info['format']}

## Usage

This dataset is used for training 3D pose lifting models (PoseMagic, HybrIK).
The dataset contains 3D joint positions for various human actions.

## Citation

If you use this dataset, please cite the original paper.
""")
	
	return info


def download_cmu_mocap_info(output_path: Path) -> Dict:
	"""
	Provide information about CMU MoCap dataset download.
	
	Args:
		output_path: Path to save dataset
		
	Returns:
		Dict with download instructions
	"""
	info = {
		"dataset": "CMU Motion Capture Database",
		"url": "http://mocap.cs.cmu.edu/",
		"license": "Unrestricted (free for research)",
		"size": "~5-10 GB (selected sequences)",
		"format": "BVH files with 3D joint positions",
		"instructions": [
			"1. Visit http://mocap.cs.cmu.edu/",
			"2. Download basketball-related sequences:",
			"   - Subject 86 (basketball)",
			"   - Subject 87 (basketball)",
			"   - Other sports sequences as needed",
			"3. Extract to: " + str(output_path / "cmu_mocap"),
			"4. Convert BVH to keypoint format using conversion script",
		],
	}
	
	readme_path = output_path / "cmu_mocap" / "README.md"
	readme_path.parent.mkdir(parents=True, exist_ok=True)
	
	with open(readme_path, 'w') as f:
		f.write(f"""# CMU Motion Capture Database

{info['dataset']}

## Download Instructions

{chr(10).join(info['instructions'])}

## Dataset Information

- **URL**: {info['url']}
- **License**: {info['license']}
- **Size**: {info['size']}
- **Format**: {info['format']}

## Basketball Sequences

Recommended sequences for basketball training:
- Subject 86: Basketball motions
- Subject 87: Basketball motions
- Look for sequences with shooting, dribbling, jumping actions

## Usage

Convert BVH files to keypoint format for training 3D pose models.
""")
	
	return info


def create_dataset_structure(output_path: Path):
	"""
	Create directory structure for 3D pose datasets.
	
	Args:
		output_path: Base path for 3D pose datasets
	"""
	directories = [
		output_path / "human36m",
		output_path / "cmu_mocap",
		output_path / "processed" / "train",
		output_path / "processed" / "val",
		output_path / "processed" / "test",
	]
	
	for directory in directories:
		directory.mkdir(parents=True, exist_ok=True)
	
	print(f"Created directory structure under {output_path}")


def main():
	parser = argparse.ArgumentParser(description="Prepare 3D pose datasets for training")
	parser.add_argument(
		"--output-path",
		type=str,
		default="data/pose_3d",
		help="Path to output directory for 3D pose datasets",
	)
	
	args = parser.parse_args()
	
	output_path = Path(args.output_path)
	create_dataset_structure(output_path)
	
	print("\n=== 3D Pose Dataset Preparation ===")
	print(f"Output directory: {output_path}")
	
	# Generate download instructions
	human36m_info = download_human36m_info(output_path)
	cmu_info = download_cmu_mocap_info(output_path)
	
	print("\n=== Download Instructions ===")
	print(f"\n{human36m_info['dataset']}:")
	for instruction in human36m_info['instructions']:
		print(f"  {instruction}")
	
	print(f"\n{cmu_info['dataset']}:")
	for instruction in cmu_info['instructions']:
		print(f"  {instruction}")
	
	print(f"\nREADME files created in:")
	print(f"  - {output_path / 'human36m' / 'README.md'}")
	print(f"  - {output_path / 'cmu_mocap' / 'README.md'}")


if __name__ == "__main__":
	main()

