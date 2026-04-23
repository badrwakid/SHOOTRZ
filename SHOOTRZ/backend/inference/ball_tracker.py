"""Optional YOLO-based ball tracker.

Gated behind the ``SHOOTRZ_ENABLE_BALL=1`` environment variable because the
ultralytics import pulls torch + the YOLO weights, which we don't want in the
hot path for the default MVP flow.

Usage::

    from backend.inference.ball_tracker import detect_and_track_ball
    result = detect_and_track_ball(frames_rgb)  # RGB numpy arrays
    # -> {"trajectory": [...], "detections": [...], "fps_hint": None}

The returned ``trajectory`` is a list of dicts with normalized centres so
downstream code (``mvp/core/pipeline._release_angle_from_trajectory``) can
derive a release-angle metric without knowing about YOLO internals.

All failures are caught and surfaced as ``None`` — this module must never
take the pipeline down.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np


logger = logging.getLogger(__name__)

# YOLO's COCO class 32 is "sports ball" in the pretrained yolov8n.pt weights.
_BALL_CLASS_ID = int(os.getenv("SHOOTRZ_BALL_CLASS_ID", "32"))
_DEFAULT_CONF = float(os.getenv("SHOOTRZ_BALL_CONF", "0.25"))
_DEFAULT_IOU = 0.45
_DEFAULT_IMGSZ = int(os.getenv("SHOOTRZ_BALL_IMGSZ", "480"))

# Search order for the yolov8n weights: explicit env path -> backend dir -> repo root.
_WEIGHT_CANDIDATES = [
    os.getenv("SHOOTRZ_YOLO_WEIGHTS"),
    str(Path(__file__).resolve().parents[1] / "yolov8n.pt"),
    str(Path(__file__).resolve().parents[2] / "yolov8n.pt"),
    str(Path(__file__).resolve().parents[3] / "yolov8n.pt"),
    "yolov8n.pt",
]

_model_cache: Optional[Any] = None


def _resolve_weights() -> Optional[str]:
    for candidate in _WEIGHT_CANDIDATES:
        if not candidate:
            continue
        if Path(candidate).exists():
            return candidate
    return None


def _load_model():
    """Lazy-load the YOLO model. Returns ``None`` when unavailable."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    weights = _resolve_weights()
    if weights is None:
        logger.warning("yolov8n.pt not found; ball tracker disabled")
        return None
    try:
        from ultralytics import YOLO  # heavy import intentionally local
    except Exception as exc:
        logger.warning("ultralytics import failed: %s", exc)
        return None
    try:
        _model_cache = YOLO(weights)
    except Exception as exc:
        logger.warning("YOLO weights load failed: %s", exc)
        return None
    return _model_cache


def detect_and_track_ball(
    frames_rgb: List[np.ndarray],
    conf_threshold: float = _DEFAULT_CONF,
    imgsz: int = _DEFAULT_IMGSZ,
    ball_class_id: int = _BALL_CLASS_ID,
) -> Optional[Dict[str, Any]]:
    """Run batched YOLO predict over ``frames_rgb`` and return a trajectory dict.

    Args:
        frames_rgb: List of RGB frames (numpy uint8 arrays).
        conf_threshold: YOLO confidence threshold. Below this a detection is
            discarded per frame.
        imgsz: YOLO input size. 480 is a good speed/accuracy trade-off on CPU.
        ball_class_id: COCO class id for "sports ball" (32 in yolov8n.pt).

    Returns:
        ``{"trajectory": [...], "detections": [...], "fps_hint": None,
           "model_type": "pretrained"}`` or ``None`` when YOLO isn't available.
    """
    if not frames_rgb:
        return None
    model = _load_model()
    if model is None:
        return None

    # YOLO expects BGR numpy arrays when fed raw images.
    frames_bgr = [cv2.cvtColor(f, cv2.COLOR_RGB2BGR) for f in frames_rgb]
    try:
        preds = model.predict(
            frames_bgr,
            conf=float(conf_threshold),
            iou=_DEFAULT_IOU,
            imgsz=int(imgsz),
            verbose=False,
        )
    except Exception as exc:
        logger.warning("YOLO predict failed: %s", exc)
        return None

    trajectory: List[Dict[str, Any]] = []
    detections: List[Dict[str, Any]] = []

    for frame_idx, result in enumerate(preds):
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            continue
        try:
            classes = boxes.cls.int().cpu().tolist()
            confidences = boxes.conf.cpu().tolist()
            xyxy = boxes.xyxy.cpu().tolist()
        except Exception:
            continue

        best = None
        for i, (class_id, confidence) in enumerate(zip(classes, confidences)):
            if int(class_id) != int(ball_class_id) or float(confidence) < conf_threshold:
                continue
            if best is None or float(confidence) > best["confidence"]:
                x1, y1, x2, y2 = xyxy[i]
                frame_h, frame_w = frames_rgb[frame_idx].shape[:2]
                if frame_w <= 0 or frame_h <= 0:
                    continue
                best = {
                    "frame": int(frame_idx),
                    "track_id": int(frame_idx),  # proxy id — no ByteTrack in batched mode
                    "center": [
                        float((x1 + x2) / 2.0 / frame_w),
                        float((y1 + y2) / 2.0 / frame_h),
                        0.0,
                    ],
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "confidence": float(confidence),
                    "width": float(x2 - x1),
                    "height": float(y2 - y1),
                }
        if best is not None:
            trajectory.append(best)
            detections.append(best)

    return {
        "trajectory": trajectory,
        "detections": detections,
        "track_history": {},
        "model_type": "pretrained",
        "fps_hint": None,
    }
