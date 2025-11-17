"""
Unified model loading system with automatic fallback handling.

Manages loading of fine-tuned models (YOLOv8, YOLOv8-pose, PoseMagic, HybrIK)
with automatic fallback to pretrained models if fine-tuned versions are unavailable.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import warnings


class ModelLoader:
	"""
	Unified model loader with fallback chain support.
	
	Automatically detects and loads fine-tuned models, falling back to
	pretrained models if fine-tuned versions are not available.
	"""
	
	def __init__(self, models_dir: Optional[str] = None):
		"""
		Initialize model loader.
		
		Args:
			models_dir: Base directory for models (default: project_root/models)
		"""
		if models_dir is None:
			project_root = Path(__file__).parent.parent.parent
			models_dir = project_root / "models"
		else:
			models_dir = Path(models_dir)
		
		self.models_dir = models_dir
		self.models_dir.mkdir(parents=True, exist_ok=True)
		
		# Model registry: maps model name to (fine-tuned_path, pretrained_name)
		self.model_registry: Dict[str, tuple] = {
			"yolov8_ball": (
				"yolov8n_basketball_deepsport.pt",
				"yolov8n.pt",  # Pretrained COCO
			),
			"yolov8_pose": (
				"yolov8n_pose_basketball.pt",
				"yolov8n-pose.pt",  # Pretrained COCO-pose
			),
			"posemagic": (
				"posemagic_basketball.pth",
				None,  # No pretrained available, uses heuristic
			),
			"hybrik": (
				"hybrik_basketball.pth",
				None,  # No pretrained available, uses heuristic
			),
		}
		
		# Cache loaded models
		self._model_cache: Dict[str, Any] = {}
	
	def get_model_path(
		self,
		model_name: str,
		prefer_finetuned: bool = True,
	) -> Optional[Path]:
		"""
		Get path to model file with fallback support.
		
		Args:
			model_name: Name of model ("yolov8_ball", "yolov8_pose", etc.)
			prefer_finetuned: Whether to prefer fine-tuned over pretrained
			
		Returns:
			Path to model file, or None if not found
		"""
		if model_name not in self.model_registry:
			warnings.warn(f"Unknown model name: {model_name}")
			return None
		
		finetuned_name, pretrained_name = self.model_registry[model_name]
		
		# Try fine-tuned first if preferred
		if prefer_finetuned:
			finetuned_path = self.models_dir / finetuned_name
			if finetuned_path.exists():
				return finetuned_path
		
		# Fallback to pretrained
		if pretrained_name:
			pretrained_path = self.models_dir / pretrained_name
			if pretrained_path.exists():
				return pretrained_path
			
			# For YOLOv8 models, ultralytics will download automatically
			if model_name.startswith("yolov8") and pretrained_name:
				return pretrained_name  # Return name for auto-download
		
		return None
	
	def load_yolov8_ball(
		self,
		prefer_finetuned: bool = True,
	) -> Optional[Any]:
		"""
		Load YOLOv8 ball detection model.
		
		Args:
			prefer_finetuned: Whether to prefer fine-tuned model
			
		Returns:
			YOLO model instance, or None if loading fails
		"""
		try:
			from ultralytics import YOLO
		except ImportError:
			warnings.warn("ultralytics not available. Cannot load YOLOv8 model.")
			return None
		
		# Check cache
		cache_key = f"yolov8_ball_{prefer_finetuned}"
		if cache_key in self._model_cache:
			return self._model_cache[cache_key]
		
		# Get model path
		model_path = self.get_model_path("yolov8_ball", prefer_finetuned)
		
		if model_path is None:
			warnings.warn("YOLOv8 ball model not found. Using default.")
			model_path = "yolov8n.pt"  # Will be downloaded by ultralytics
		
		try:
			model = YOLO(str(model_path))
			self._model_cache[cache_key] = model
			
			# Log which model was loaded
			if isinstance(model_path, Path) and "basketball" in model_path.name:
				print(f"✓ Loaded fine-tuned YOLOv8 ball model: {model_path.name}")
			else:
				print(f"✓ Loaded pretrained YOLOv8 ball model: {model_path}")
			
			return model
		except Exception as e:
			warnings.warn(f"Failed to load YOLOv8 ball model: {e}")
			return None
	
	def load_yolov8_pose(
		self,
		prefer_finetuned: bool = True,
	) -> Optional[Any]:
		"""
		Load YOLOv8-pose model.
		
		Args:
			prefer_finetuned: Whether to prefer fine-tuned model
			
		Returns:
			YOLO pose model instance, or None if loading fails
		"""
		try:
			from ultralytics import YOLO
		except ImportError:
			warnings.warn("ultralytics not available. Cannot load YOLOv8-pose model.")
			return None
		
		# Check cache
		cache_key = f"yolov8_pose_{prefer_finetuned}"
		if cache_key in self._model_cache:
			return self._model_cache[cache_key]
		
		# Get model path
		model_path = self.get_model_path("yolov8_pose", prefer_finetuned)
		
		if model_path is None:
			warnings.warn("YOLOv8-pose model not found. Using default.")
			model_path = "yolov8n-pose.pt"  # Will be downloaded by ultralytics
		
		try:
			model = YOLO(str(model_path))
			self._model_cache[cache_key] = model
			
			# Log which model was loaded
			if isinstance(model_path, Path) and "basketball" in model_path.name:
				print(f"✓ Loaded fine-tuned YOLOv8-pose model: {model_path.name}")
			else:
				print(f"✓ Loaded pretrained YOLOv8-pose model: {model_path}")
			
			return model
		except Exception as e:
			warnings.warn(f"Failed to load YOLOv8-pose model: {e}")
			return None
	
	def load_posemagic(
		self,
		prefer_finetuned: bool = True,
	) -> Optional[str]:
		"""
		Get path to PoseMagic model.
		
		Args:
			prefer_finetuned: Whether to prefer fine-tuned model
			
		Returns:
			Path to model file, or None if not found
		"""
		model_path = self.get_model_path("posemagic", prefer_finetuned)
		
		if model_path and model_path.exists():
			print(f"✓ Found PoseMagic model: {model_path.name}")
			return str(model_path)
		else:
			print("⚠ PoseMagic model not found. Using heuristic fallback.")
			return None
	
	def load_hybrik(
		self,
		prefer_finetuned: bool = True,
	) -> Optional[str]:
		"""
		Get path to HybrIK model.
		
		Args:
			prefer_finetuned: Whether to prefer fine-tuned model
			
		Returns:
			Path to model file, or None if not found
		"""
		model_path = self.get_model_path("hybrik", prefer_finetuned)
		
		if model_path and model_path.exists():
			print(f"✓ Found HybrIK model: {model_path.name}")
			return str(model_path)
		else:
			print("⚠ HybrIK model not found. Using heuristic fallback.")
			return None
	
	def list_available_models(self) -> Dict[str, List[str]]:
		"""
		List all available models (fine-tuned and pretrained).
		
		Returns:
			Dict mapping model names to lists of available files
		"""
		available = {}
		
		for model_name, (finetuned_name, pretrained_name) in self.model_registry.items():
			available[model_name] = []
			
			# Check fine-tuned
			finetuned_path = self.models_dir / finetuned_name
			if finetuned_path.exists():
				available[model_name].append(f"fine-tuned: {finetuned_name}")
			
			# Check pretrained
			if pretrained_name:
				pretrained_path = self.models_dir / pretrained_name
				if pretrained_path.exists():
					available[model_name].append(f"pretrained: {pretrained_name}")
				elif model_name.startswith("yolov8"):
					available[model_name].append(f"pretrained: {pretrained_name} (auto-download)")
		
		return available
	
	def clear_cache(self):
		"""Clear model cache."""
		self._model_cache.clear()


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader(models_dir: Optional[str] = None) -> ModelLoader:
	"""
	Get or create global model loader instance.
	
	Args:
		models_dir: Base directory for models
		
	Returns:
		ModelLoader instance
	"""
	global _model_loader
	
	if _model_loader is None:
		_model_loader = ModelLoader(models_dir=models_dir)
	
	return _model_loader

