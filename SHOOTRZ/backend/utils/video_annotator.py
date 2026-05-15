"""Overlay renderer: skeleton + phase ribbon + angle HUD + key-frame markers.

The pre-2026-04-23 implementation indexed ``pose_results[frame_idx]`` as a
list while ``pose_results`` only contained pose-filtered (sampled) frames.
That put the skeleton on the wrong frame every time stride > 1. This
rewrite keys by ``frame_idx`` explicitly and linearly interpolates between
sampled neighbours for source frames that were skipped by the stride.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


logger = logging.getLogger(__name__)


# MediaPipe pose connections (33 keypoints). Matches what the rest of the
# pipeline emits via ``BASKETBALL_KEYPOINTS``.
POSE_CONNECTIONS: List[Tuple[int, int]] = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),  # Mouth
    (11, 12),  # Shoulders
    (11, 13), (13, 15),  # Left arm
    (12, 14), (14, 16),  # Right arm
    (11, 23), (12, 24),  # Shoulders -> hips
    (23, 24),  # Hips
    (23, 25), (25, 27),  # Left leg
    (24, 26), (26, 28),  # Right leg
]


PHASE_COLORS = {
    "stance": (255, 255, 0),
    "setup": (255, 255, 0),
    "crouch": (0, 255, 255),
    "load": (0, 255, 255),
    "release": (0, 255, 0),
    "follow_through": (255, 0, 255),
    "landing": (255, 0, 255),
}


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------


def _draw_skeleton(
    frame: np.ndarray,
    landmarks: np.ndarray,
    confidence: Optional[np.ndarray] = None,
    confidence_threshold: float = 0.50,
) -> np.ndarray:
    """Draw the 33-point MediaPipe skeleton with confidence-sized dots."""
    frame = frame.copy()
    h, w = frame.shape[:2]
    if landmarks.ndim != 2 or landmarks.shape[1] < 2:
        return frame

    pts = landmarks[:, :2].astype(float)
    pts[:, 0] *= float(w)
    pts[:, 1] *= float(h)
    pts_i = pts.astype(int)

    def _valid(i: int) -> bool:
        if i >= len(pts_i):
            return False
        x, y = pts_i[i]
        if x <= 1 or y <= 1 or x >= w - 1 or y >= h - 1:
            return False
        return True

    # Bones first, so joint dots sit on top.
    for a, b in POSE_CONNECTIONS:
        if not _valid(a) or not _valid(b):
            continue
        pa = tuple(pts_i[a])
        pb = tuple(pts_i[b])
        strong = True
        if confidence is not None and a < len(confidence) and b < len(confidence):
            strong = (
                float(confidence[a]) >= confidence_threshold
                and float(confidence[b]) >= confidence_threshold
            )
        colour = (0, 255, 0) if strong else (120, 180, 120)
        thickness = 3 if strong else 1
        cv2.line(frame, pa, pb, colour, thickness, lineType=cv2.LINE_AA)

    # Confidence-scaled joint dots.
    for i, pt in enumerate(pts_i):
        if not _valid(i):
            continue
        conf_i = float(confidence[i]) if (confidence is not None and i < len(confidence)) else 1.0
        if conf_i < 0.10:
            continue
        radius = int(max(3, round(conf_i * 7)))
        colour = (0, 0, 255) if conf_i >= confidence_threshold else (180, 180, 180)
        cv2.circle(frame, tuple(pt), radius, colour, -1, lineType=cv2.LINE_AA)
    return frame


def _draw_phase_ribbon(
    frame: np.ndarray,
    current_phase: Optional[str],
) -> np.ndarray:
    """Top banner with the current phase label."""
    if not current_phase:
        return frame
    frame = frame.copy()
    h, w = frame.shape[:2]
    label = current_phase.replace("_", " ").upper()
    colour = PHASE_COLORS.get(current_phase.lower(), (255, 255, 255))
    # Dark translucent strip at the top.
    overlay = frame.copy()
    strip_h = max(28, h // 22)
    cv2.rectangle(overlay, (0, 0), (w, strip_h), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)
    cv2.putText(
        frame,
        f"PHASE: {label}",
        (12, strip_h - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        colour,
        2,
        lineType=cv2.LINE_AA,
    )
    return frame


def _draw_angle_hud(
    frame: np.ndarray,
    rows: List[Tuple[str, Optional[float], Optional[float]]],
) -> np.ndarray:
    """Bottom-left HUD showing (label, value_deg, sub_score) rows."""
    if not rows:
        return frame
    frame = frame.copy()
    h, w = frame.shape[:2]
    line_h = max(24, h // 28)
    box_w = min(300, int(w * 0.45))
    box_h = line_h * (len(rows) + 1) + 8
    y0 = h - box_h - 8
    x0 = 10
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + box_w, y0 + box_h), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

    cv2.putText(
        frame,
        "ANGLES",
        (x0 + 10, y0 + line_h - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        lineType=cv2.LINE_AA,
    )
    for i, (label, value, score) in enumerate(rows, start=1):
        y = y0 + (i + 1) * line_h - 6
        if value is None:
            text = f"{label}: N/A"
            colour = (170, 170, 170)
        else:
            text = f"{label}: {value:.1f} deg"
            if score is None:
                colour = (220, 220, 220)
            elif score >= 70:
                colour = (70, 230, 90)
            elif score >= 40:
                colour = (0, 200, 255)
            else:
                colour = (0, 90, 255)
        cv2.putText(
            frame,
            text,
            (x0 + 10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            colour,
            2,
            lineType=cv2.LINE_AA,
        )
    return frame


def _draw_event_marker(frame: np.ndarray, label: str, colour: Tuple[int, int, int]) -> np.ndarray:
    frame = frame.copy()
    h, w = frame.shape[:2]
    # Flashing-style border and a label pill top-right.
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), colour, max(4, h // 200))
    text = label.upper()
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    pad = 8
    x2 = w - 14
    x1 = x2 - tw - pad * 2
    y1 = 14
    y2 = y1 + th + pad * 2
    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, -1)
    cv2.putText(
        frame,
        text,
        (x1 + pad, y2 - pad),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 0),
        2,
        lineType=cv2.LINE_AA,
    )
    return frame


# ---------------------------------------------------------------------------
# Pose result interpolation
# ---------------------------------------------------------------------------


def _build_pose_lookup(
    pose_results: List[Dict[str, Any]],
) -> Tuple[Dict[int, Dict[str, Any]], List[int]]:
    lookup: Dict[int, Dict[str, Any]] = {}
    for r in pose_results:
        idx = r.get("frame_idx")
        if idx is None:
            continue
        lookup[int(idx)] = r
    sorted_keys = sorted(lookup.keys())
    return lookup, sorted_keys


def _interp_pose(
    target_frame: int,
    lookup: Dict[int, Dict[str, Any]],
    sorted_keys: List[int],
    max_gap: int = 10,
) -> Optional[Dict[str, Any]]:
    """Return a pose_result (possibly interpolated) for ``target_frame``.

    - If an exact match exists, return it verbatim.
    - Otherwise linearly interpolate landmarks between the two nearest sampled
      frames, provided they are within ``max_gap`` frames of the target.
    - Beyond ``max_gap``, return None (skip annotation for that source frame).
    """
    if not sorted_keys:
        return None
    if target_frame in lookup:
        return lookup[target_frame]

    # Binary-ish search over the small sorted_keys list.
    lo = hi = None
    for k in sorted_keys:
        if k < target_frame:
            lo = k
        elif k > target_frame:
            hi = k
            break
    if lo is None or hi is None:
        nearest = lo if lo is not None else hi
        if nearest is None:
            return None
        if abs(nearest - target_frame) > max_gap:
            return None
        return lookup[nearest]

    if (target_frame - lo) > max_gap or (hi - target_frame) > max_gap:
        return None

    try:
        a = lookup[lo]
        b = lookup[hi]
        la = np.asarray(a.get("landmarks"), dtype=np.float32)
        lb = np.asarray(b.get("landmarks"), dtype=np.float32)
        if la.shape != lb.shape:
            return a  # fall back to the earlier frame
        t = (target_frame - lo) / float(hi - lo)
        blended_landmarks = la + t * (lb - la)
        ca = a.get("confidence")
        cb = b.get("confidence")
        if ca is not None and cb is not None:
            ca_arr = np.asarray(ca, dtype=np.float32)
            cb_arr = np.asarray(cb, dtype=np.float32)
            if ca_arr.shape == cb_arr.shape:
                blended_conf = np.minimum(ca_arr, cb_arr)
            else:
                blended_conf = ca_arr
        else:
            blended_conf = ca if ca is not None else cb
        return {
            "frame_idx": target_frame,
            "landmarks": blended_landmarks,
            "confidence": blended_conf,
            "interpolated": True,
        }
    except Exception:
        return lookup.get(lo)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def annotate_video(
    video_path: str,
    pose_results: List[Dict[str, Any]],
    phases: Optional[List[Dict[str, Any]]] = None,
    ball_trajectory: Optional[List[np.ndarray]] = None,
    output_path: Optional[str] = None,
    fps: float = 30.0,
    shot_window: Optional[Dict[str, Any]] = None,
    metric_hud: Optional[List[Dict[str, Any]]] = None,
    metric_markers: Optional[Dict[int, str]] = None,
) -> str:
    """Render the annotated overlay video.

    Args:
        video_path: Path to the source clip.
        pose_results: Sampled pose results (any stride). Indexed by
            ``frame_idx`` internally, so the skeleton lands on the correct
            source frame regardless of sampling.
        phases: Optional phase detections (list of dicts with ``phase``,
            ``start_frame``, ``end_frame``) used to drive the top ribbon.
        ball_trajectory: Optional normalised ball positions (retained for
            future ball overlay; currently unused).
        output_path: Destination .mp4 path. Defaults to
            ``<video_stem>_annotated.mp4`` next to the source.
        fps: Fallback FPS when the source reports zero.
        shot_window: Optional dict with ``crouch_frame`` / ``release_frame`` /
            ``end_frame`` so we can draw flashing borders at those moments.
        metric_hud: Optional list of {``label``, ``value_deg``, ``score``}
            rows drawn on frames inside the shot window.
        metric_markers: Optional ``{frame_idx: label}`` dict - draws an
            attention marker on the frame each metric was measured at.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps > 0:
        fps = video_fps

    if output_path is None:
        video_path_obj = Path(video_path)
        output_path = str(video_path_obj.parent / f"{video_path_obj.stem}_annotated.mp4")

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    out = None
    for codec in ("mp4v", "avc1", "H264"):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        if out.isOpened():
            break
    if out is None or not out.isOpened():
        raise RuntimeError("Failed to open video writer for overlay (tried mp4v/avc1/H264).")

    # Phase map keyed by SOURCE frame_idx, matching the indices in pose_results.
    phase_map: Dict[int, str] = {}
    if phases:
        for phase in phases:
            phase_obj = phase.get("phase")
            if isinstance(phase_obj, str):
                phase_name = phase_obj.lower()
            else:
                try:
                    phase_name = (
                        phase_obj.value if hasattr(phase_obj, "value") else str(phase_obj).lower().split(".")[-1]
                    )
                except Exception:
                    phase_name = str(phase_obj).lower().split(".")[-1] if phase_obj else ""
            start_frame = int(phase.get("start_frame") or 0)
            end_frame = int(phase.get("end_frame") or start_frame)
            for f in range(start_frame, end_frame + 1):
                phase_map[f] = phase_name

    shot_window = shot_window or {}
    event_frames: Dict[int, Tuple[str, Tuple[int, int, int]]] = {}
    for event_name, colour in (
        ("crouch_frame", (0, 255, 255)),
        ("release_frame", (0, 255, 0)),
        ("end_frame", (255, 0, 255)),
    ):
        f = shot_window.get(event_name)
        if isinstance(f, int):
            label = event_name.replace("_frame", "").upper()
            event_frames[int(f)] = (label, colour)

    metric_markers = metric_markers or {}

    lookup, sorted_keys = _build_pose_lookup(pose_results or [])

    start_frame = shot_window.get("start_frame")
    end_frame = shot_window.get("end_frame")
    in_shot_lo = int(start_frame) if isinstance(start_frame, int) else None
    in_shot_hi = int(end_frame) if isinstance(end_frame, int) else None

    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Skeleton at the ACTUAL source frame, via dict lookup +
            # linear interpolation when the frame was sampled out.
            pose_result = _interp_pose(frame_idx, lookup, sorted_keys)
            if pose_result is not None:
                landmarks = pose_result.get("landmarks")
                confidence = pose_result.get("confidence")
                if landmarks is not None:
                    if not isinstance(landmarks, np.ndarray):
                        landmarks = np.asarray(landmarks, dtype=np.float32)
                    if confidence is not None and not isinstance(confidence, np.ndarray):
                        confidence = np.asarray(confidence, dtype=np.float32)
                    frame = _draw_skeleton(frame, landmarks, confidence)

            # Phase ribbon.
            current_phase = phase_map.get(frame_idx)
            frame = _draw_phase_ribbon(frame, current_phase)

            # Angle HUD during the shot window only.
            if metric_hud and (
                in_shot_lo is None
                or in_shot_hi is None
                or in_shot_lo <= frame_idx <= in_shot_hi
            ):
                rows = [
                    (str(m.get("label", "")), m.get("value_deg"), m.get("score"))
                    for m in metric_hud
                ]
                frame = _draw_angle_hud(frame, rows)

            # Key-event markers (crouch / release / end) and per-metric selected_frame.
            marker_label = None
            if frame_idx in event_frames:
                marker_label, marker_colour = event_frames[frame_idx]
                frame = _draw_event_marker(frame, marker_label, marker_colour)
            metric_label = metric_markers.get(frame_idx)
            if metric_label:
                frame = _draw_event_marker(frame, metric_label, (255, 215, 0))

            out.write(frame)
            frame_idx += 1
    finally:
        cap.release()
        out.release()

    return output_path


# Back-compat aliases so existing imports/tests keep working.
draw_skeleton = _draw_skeleton
draw_phase_label = lambda frame, phase, *_a, **_kw: _draw_phase_ribbon(frame, phase)  # noqa: E731


def draw_ball_trajectory(
    frame: np.ndarray,
    ball_trajectory: List[np.ndarray],
    color: Tuple[int, int, int] = (255, 0, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Retained for backwards compat; the MVP overlay no longer draws ball paths."""
    if not ball_trajectory:
        return frame
    frame = frame.copy()
    h, w = frame.shape[:2]
    points = []
    for pos in ball_trajectory:
        if len(pos) >= 2:
            points.append((int(pos[0] * w), int(pos[1] * h)))
    if len(points) > 1:
        for i in range(len(points) - 1):
            cv2.line(frame, points[i], points[i + 1], color, thickness)
    if points:
        cv2.circle(frame, points[-1], 8, color, -1)
    return frame
