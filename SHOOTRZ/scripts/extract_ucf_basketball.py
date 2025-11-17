"""
Extract basketball-specific sequences from UCF Sports dataset.

Filters and organizes basketball action videos from UCF Sports dataset
for use in phase detection validation and benchmarking.
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Dict
import cv2
import json


def find_basketball_videos(ucf_path: Path) -> List[Path]:
	"""
	Find all basketball-related videos in UCF Sports dataset.
	
	Args:
		ucf_path: Path to UCF Sports dataset root
		
	Returns:
		List of video file paths
	"""
	basketball_videos = []
	
	# Basketball keywords to search for
	basketball_keywords = ['basketball', 'basket', 'ball']
	
	# Find all video files
	video_extensions = ['.avi', '.mp4', '.mov', '.mkv', '.flv']
	
	for ext in video_extensions:
		for video_file in ucf_path.rglob(f"*{ext}"):
			# Check filename and path
			path_str = str(video_file).lower()
			if any(keyword in path_str for keyword in basketball_keywords):
				basketball_videos.append(video_file)
	
	# Also check for Basketball directory
	basketball_dir = ucf_path / "Basketball"
	if basketball_dir.exists():
		for ext in video_extensions:
			basketball_videos.extend(basketball_dir.rglob(f"*{ext}"))
	
	# Note: UCF Sports may not have basketball category
	# In that case, we can use other sports actions for general motion analysis
	# For now, return empty list if no basketball videos found
	
	# Remove duplicates
	basketball_videos = list(set(basketball_videos))
	
	return basketball_videos


def extract_video_info(video_path: Path) -> Dict:
	"""
	Extract metadata from video file.
	
	Args:
		video_path: Path to video file
		
	Returns:
		Dict with video metadata
	"""
	info = {
		'path': str(video_path),
		'name': video_path.name,
		'frames': 0,
		'fps': 0,
		'duration': 0,
		'width': 0,
		'height': 0,
		'valid': False,
	}
	
	try:
		cap = cv2.VideoCapture(str(video_path))
		if cap.isOpened():
			info['frames'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
			info['fps'] = cap.get(cv2.CAP_PROP_FPS)
			info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
			info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
			
			if info['fps'] > 0:
				info['duration'] = info['frames'] / info['fps']
			
			info['valid'] = True
			cap.release()
	except Exception as e:
		print(f"Error reading {video_path}: {e}")
	
	return info


def copy_basketball_videos(
	ucf_path: Path,
	output_path: Path,
	max_videos: int = None,
	min_duration: float = 1.0,
	max_duration: float = 30.0,
):
	"""
	Copy basketball videos to output directory with metadata.
	
	Args:
		ucf_path: Path to UCF Sports dataset
		output_path: Path to output directory
		max_videos: Maximum number of videos to copy (None = all)
		min_duration: Minimum video duration in seconds
		max_duration: Maximum video duration in seconds
	"""
	print(f"Extracting basketball videos from {ucf_path}")
	
	# Find basketball videos
	basketball_videos = find_basketball_videos(ucf_path)
	print(f"Found {len(basketball_videos)} basketball videos")
	
	if not basketball_videos:
		print("No basketball videos found. Check dataset path.")
		return
	
	# Extract video info
	video_infos = []
	for video_path in basketball_videos:
		info = extract_video_info(video_path)
		if info['valid']:
			# Filter by duration
			if min_duration <= info['duration'] <= max_duration:
				video_infos.append(info)
	
	print(f"Filtered to {len(video_infos)} videos (duration: {min_duration}-{max_duration}s)")
	
	# Limit number of videos
	if max_videos and len(video_infos) > max_videos:
		video_infos = video_infos[:max_videos]
		print(f"Limited to {max_videos} videos")
	
	# Create output directory
	output_path.mkdir(parents=True, exist_ok=True)
	videos_dir = output_path / "videos"
	videos_dir.mkdir(exist_ok=True)
	
	# Copy videos and collect metadata
	metadata = {
		'source': str(ucf_path),
		'total_videos': len(video_infos),
		'videos': [],
	}
	
	for i, info in enumerate(video_infos):
		source_path = Path(info['path'])
		dest_path = videos_dir / source_path.name
		
		# Copy video
		try:
			shutil.copy2(source_path, dest_path)
			print(f"Copied {i+1}/{len(video_infos)}: {source_path.name}")
			
			# Add to metadata
			metadata['videos'].append({
				'filename': source_path.name,
				'frames': info['frames'],
				'fps': info['fps'],
				'duration': info['duration'],
				'width': info['width'],
				'height': info['height'],
			})
		except Exception as e:
			print(f"Error copying {source_path}: {e}")
	
	# Save metadata
	metadata_path = output_path / "metadata.json"
	with open(metadata_path, 'w') as f:
		json.dump(metadata, f, indent=2)
	
	print(f"\n=== Extraction Complete ===")
	print(f"Videos saved to: {videos_dir}")
	print(f"Metadata saved to: {metadata_path}")
	print(f"Total videos: {len(metadata['videos'])}")


def main():
	parser = argparse.ArgumentParser(description="Extract basketball sequences from UCF Sports dataset")
	parser.add_argument(
		"--ucf-path",
		type=str,
		default="data/pose/ucf_sports",
		help="Path to UCF Sports dataset root",
	)
	parser.add_argument(
		"--output-path",
		type=str,
		default="data/pose/ucf_sports/basketball",
		help="Path to output directory for basketball videos",
	)
	parser.add_argument(
		"--max-videos",
		type=int,
		default=None,
		help="Maximum number of videos to extract (None = all)",
	)
	parser.add_argument(
		"--min-duration",
		type=float,
		default=1.0,
		help="Minimum video duration in seconds",
	)
	parser.add_argument(
		"--max-duration",
		type=float,
		default=30.0,
		help="Maximum video duration in seconds",
	)
	
	args = parser.parse_args()
	
	ucf_path = Path(args.ucf_path)
	output_path = Path(args.output_path)
	
	if not ucf_path.exists():
		print(f"Error: UCF Sports path does not exist: {ucf_path}")
		return
	
	copy_basketball_videos(
		ucf_path=ucf_path,
		output_path=output_path,
		max_videos=args.max_videos,
		min_duration=args.min_duration,
		max_duration=args.max_duration,
	)


if __name__ == "__main__":
	main()

