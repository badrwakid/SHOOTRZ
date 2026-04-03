"""
Shot event and window detection for MVP pipeline.

Fused temporal detection using knee flexion, hip vertical motion, wrist height,
and elbow extension. Frame IDs are original video indices (angles / pose CSV).

Legacy path available via shot_detection.use_legacy_detector in config.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from scipy.signal import find_peaks


def _series_for_joint(
    pose_df: pd.DataFrame,
    joint: str,
    y_col: str,
) -> pd.DataFrame:
    sub = pose_df[pose_df["joint"] == joint].copy()
    if sub.empty:
        return pd.DataFrame(columns=["frame_id", "y", "confidence"])
    sub = sub.sort_values("frame_id")
    return pd.DataFrame(
        {
            "frame_id": sub["frame_id"].values.astype(int),
            "y": sub[y_col].astype(float).values,
            "confidence": sub["confidence"].astype(float).values,
        }
    )


def _row_at_frame(angles_df: pd.DataFrame, frame_id: int) -> Optional[pd.Series]:
    m = angles_df[angles_df["frame_id"] == frame_id]
    if len(m):
        return m.iloc[0]
    if angles_df.empty:
        return None
    nearest_idx = (angles_df["frame_id"] - frame_id).abs().idxmin()
    return angles_df.loc[nearest_idx]


class ShotDetector:
    """Detects shot events and shot window with diagnostics."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.knee_flexion_threshold = config.get("knee_flexion_threshold", 100.0)
        self.wrist_peak_window = config.get("wrist_peak_window", 15)
        self.pre_frames = config.get("pre_frames", 10)
        self.post_frames = config.get("post_frames", 20)
        self.stable_window = int(config.get("stable_window_frames", 5))
        self.motion_energy_threshold = float(config.get("motion_energy_threshold", 3.0))
        self.use_legacy_detector = bool(config.get("use_legacy_detector", False))

    def detect_shot_window(
        self,
        angles_df: pd.DataFrame,
        pose_keypoints_df: pd.DataFrame,
        shooting_side: str,
    ) -> Dict[str, Any]:
        angles_df = angles_df.sort_values("frame_id").reset_index(drop=True)
        frame_ids = angles_df["frame_id"].values.astype(int)
        y_col = "y_norm_smooth" if "y_norm_smooth" in pose_keypoints_df.columns else "y_norm"
        wrist_joint = f"{shooting_side}_wrist"
        hip_joint = f"{shooting_side}_hip"
        wrist_s = _series_for_joint(pose_keypoints_df, wrist_joint, y_col)
        hip_s = _series_for_joint(pose_keypoints_df, hip_joint, y_col)

        diagnostics: Dict[str, Any] = {
            "method": "fused_temporal",
            "candidates": {},
            "warnings": [],
        }

        if self.use_legacy_detector:
            return self._legacy_shot_window(
                angles_df, pose_keypoints_df, shooting_side, y_col, diagnostics
            )

        crouch_frame, crouch_conf, crouch_diag = self._detect_crouch_fused(
            angles_df, wrist_s, hip_s, diagnostics
        )
        diagnostics["candidates"]["crouch"] = crouch_diag

        release_frame, release_conf, release_diag = self._detect_release_scored(
            angles_df,
            wrist_s,
            shooting_side,
            int(crouch_frame),
            y_col,
            pose_keypoints_df,
        )
        diagnostics["candidates"]["release"] = release_diag

        start_frame, start_diag = self._detect_start_signal(
            angles_df, int(crouch_frame), frame_ids
        )
        diagnostics["candidates"]["start"] = start_diag

        fid_max = int(frame_ids.max()) if len(frame_ids) else 0
        end_frame, end_diag = self._detect_end_signal(
            wrist_s, int(release_frame), fid_max
        )
        diagnostics["candidates"]["end"] = end_diag

        fid_min = int(frame_ids.min()) if len(frame_ids) else 0
        start_frame = max(fid_min, min(int(start_frame), int(crouch_frame)))

        if int(crouch_frame) >= int(release_frame):
            diagnostics["warnings"].append("crouch_gte_release_adjusted")
            release_frame = min(
                fid_max,
                int(crouch_frame) + max(3, self.wrist_peak_window // 3),
            )
            release_conf *= 0.7
        if int(release_frame) > fid_max:
            release_frame = fid_max
        end_frame = int(end_frame)
        if end_frame < int(release_frame):
            end_frame = min(fid_max, int(release_frame) + self.post_frames)
        end_frame = min(fid_max, max(end_frame, int(release_frame)))

        overall_confidence = float(max(0.05, min(1.0, min(crouch_conf, release_conf))))

        return {
            "start_frame": int(start_frame),
            "crouch_frame": int(crouch_frame),
            "release_frame": int(release_frame),
            "end_frame": int(end_frame),
            "confidence": "high"
            if overall_confidence > 0.7
            else "medium"
            if overall_confidence > 0.4
            else "low",
            "confidence_score": overall_confidence,
            "method": "fused_temporal",
            "crouch_confidence": float(crouch_conf),
            "release_confidence": float(release_conf),
            "start_confidence": float(start_diag.get("confidence", 0.5)),
            "end_confidence": float(end_diag.get("confidence", 0.5)),
            "diagnostics": diagnostics,
        }

    def _legacy_shot_window(
        self,
        angles_df: pd.DataFrame,
        pose_keypoints_df: pd.DataFrame,
        shooting_side: str,
        y_col: str,
        diagnostics: Dict[str, Any],
    ) -> Dict[str, Any]:
        crouch_frame, crouch_conf = self._detect_crouch_simple(angles_df)
        release_frame, release_conf = self._detect_release_simple(
            pose_keypoints_df, shooting_side, int(crouch_frame), y_col
        )
        frame_ids = angles_df["frame_id"].values.astype(int)
        fid_min = int(frame_ids.min()) if len(frame_ids) else 0
        fid_max = int(frame_ids.max()) if len(frame_ids) else 0
        start_frame = max(0, int(crouch_frame) - self.pre_frames)
        end_frame = min(fid_max, int(release_frame) + self.post_frames)
        overall = float(min(crouch_conf, release_conf))
        diagnostics.update({"method": "legacy", "warnings": ["use_legacy_detector"]})
        return {
            "start_frame": int(start_frame),
            "crouch_frame": int(crouch_frame),
            "release_frame": int(release_frame),
            "end_frame": int(end_frame),
            "confidence": "high"
            if overall > 0.7
            else "medium"
            if overall > 0.4
            else "low",
            "confidence_score": overall,
            "method": "knee_minimum_wrist_peak",
            "crouch_confidence": float(crouch_conf),
            "release_confidence": float(release_conf),
            "start_confidence": 0.5,
            "end_confidence": 0.5,
            "diagnostics": diagnostics,
        }

    def _detect_crouch_simple(self, angles_df: pd.DataFrame) -> Tuple[int, float]:
        knee_angles = angles_df["knee_angle"].values
        knee_confidence = angles_df["confidence_knee"].values
        frame_ids = angles_df["frame_id"].values.astype(int)
        valid_mask = ~np.isnan(knee_angles)
        knee_angles = knee_angles[valid_mask]
        knee_confidence = knee_confidence[valid_mask]
        frame_ids = frame_ids[valid_mask]
        if len(knee_angles) == 0:
            mid = len(angles_df) // 2
            return int(angles_df.iloc[mid]["frame_id"]), 0.2
        inverted = -knee_angles
        peaks, properties = find_peaks(
            inverted,
            prominence=2.0,
            distance=max(5, self.pre_frames // 2),
        )
        conf = 0.2
        if len(peaks) > 0:
            peak_prom = properties.get("prominences", np.ones_like(peaks))
            best_i = int(np.argmax(peak_prom))
            best_peak = peaks[best_i]
            if best_peak <= 2 or best_peak >= len(frame_ids) - 2:
                valid = [(i, p) for i, p in enumerate(peaks) if 2 < p < len(frame_ids) - 2]
                if valid:
                    best_i, best_peak = max(valid, key=lambda ip: peak_prom[ip[0]])
            crouch_frame = int(frame_ids[best_peak])
            conf = float(knee_confidence[best_peak])
        else:
            min_idx = int(np.argmin(knee_angles))
            crouch_frame = int(frame_ids[min_idx])
            conf = float(knee_confidence[min_idx])
        if crouch_frame <= int(frame_ids.min()) + 2 or crouch_frame >= int(frame_ids.max()) - 2:
            conf *= 0.5
        try:
            ki = int(np.where(frame_ids == crouch_frame)[0][0])
            angle_at = float(knee_angles[ki])
        except Exception:
            angle_at = float(np.min(knee_angles))
        if angle_at > self.knee_flexion_threshold:
            conf *= 0.5
        return crouch_frame, conf

    def _detect_release_simple(
        self,
        pose_keypoints_df: pd.DataFrame,
        shooting_side: str,
        crouch_frame: int,
        y_col: str,
    ) -> Tuple[int, float]:
        wrist_joint = f"{shooting_side}_wrist"
        wrist_df = pose_keypoints_df[
            pose_keypoints_df["joint"] == wrist_joint
        ].sort_values("frame_id")
        if wrist_df.empty:
            return crouch_frame, 0.3
        after = wrist_df[wrist_df["frame_id"] >= crouch_frame]
        if after.empty:
            return crouch_frame, 0.3
        wy = -after[y_col].values.astype(float)
        peaks, _ = find_peaks(
            wy,
            distance=self.wrist_peak_window,
            prominence=0.01,
        )
        if len(peaks) > 0:
            row = after.iloc[peaks[0]]
            return int(row["frame_id"]), float(row["confidence"])
        max_idx = int(np.argmax(wy))
        row = after.iloc[max_idx]
        return int(row["frame_id"]), float(row["confidence"]) * 0.7

    def _detect_crouch_fused(
        self,
        angles_df: pd.DataFrame,
        wrist_s: pd.DataFrame,
        hip_s: pd.DataFrame,
        diagnostics: Dict[str, Any],
    ) -> Tuple[int, float, Dict[str, Any]]:
        base_frame, base_conf = self._detect_crouch_simple(angles_df)
        diag: Dict[str, Any] = {"base_frame": base_frame, "base_confidence": base_conf}

        knee_angles = angles_df["knee_angle"].values
        frame_ids = angles_df["frame_id"].values.astype(int)
        valid = ~np.isnan(knee_angles)
        if valid.sum() < 3:
            return base_frame, base_conf, diag

        min_knee_idx = int(np.argmin(knee_angles[valid]))
        knee_min_frame = int(frame_ids[valid][min_knee_idx])

        hip_boost = 0.0
        if not hip_s.empty and len(hip_s) > 3:
            hy = hip_s["y"].values
            hf = hip_s["frame_id"].values.astype(int)
            hip_min_idx = int(np.argmax(hy))
            hip_bottom_frame = int(hf[hip_min_idx])
            if abs(hip_bottom_frame - knee_min_frame) <= max(15, self.wrist_peak_window):
                hip_boost = 0.15

        wrist_boost = 0.0
        if not wrist_s.empty and len(wrist_s) > 3:
            search = wrist_s[wrist_s["frame_id"] <= knee_min_frame + 20]
            search = search[search["frame_id"] >= knee_min_frame - 20]
            if len(search) > 2:
                wyi = search["y"].values
                dip_idx = int(np.argmax(wyi))
                dip_frame = int(search.iloc[dip_idx]["frame_id"])
                if abs(dip_frame - knee_min_frame) <= 12:
                    wrist_boost = 0.1

        fused_conf = min(1.0, base_conf + hip_boost + wrist_boost)
        fused_frame = knee_min_frame
        if abs(knee_min_frame - base_frame) <= 8:
            fused_frame = int(round((knee_min_frame + base_frame) / 2))
        diag.update(
            {
                "knee_min_frame": knee_min_frame,
                "fused_frame": fused_frame,
                "hip_boost": hip_boost,
                "wrist_boost": wrist_boost,
            }
        )
        return fused_frame, fused_conf, diag

    def _detect_release_scored(
        self,
        angles_df: pd.DataFrame,
        wrist_s: pd.DataFrame,
        shooting_side: str,
        crouch_frame: int,
        y_col: str,
        pose_keypoints_df: pd.DataFrame,
    ) -> Tuple[int, float, Dict[str, Any]]:
        diag: Dict[str, Any] = {"candidates": []}
        wrist_joint = f"{shooting_side}_wrist"
        wrist_df = pose_keypoints_df[
            pose_keypoints_df["joint"] == wrist_joint
        ].sort_values("frame_id")
        if wrist_df.empty:
            row = _row_at_frame(angles_df, crouch_frame)
            ef = crouch_frame
            if row is not None:
                ef = int(row["frame_id"])
            return ef, 0.3, diag

        after = wrist_df[wrist_df["frame_id"] > crouch_frame].copy()
        if after.empty:
            return crouch_frame, 0.3, diag

        yvals = after[y_col].astype(float).values
        fids = after["frame_id"].values.astype(int)
        confs = after["confidence"].astype(float).values

        inverted = -yvals
        peaks, props = find_peaks(
            inverted,
            distance=max(3, self.wrist_peak_window // 2),
            prominence=0.008,
        )

        candidates: List[Tuple[int, float, str]] = []

        prominences = props.get("prominences")
        if prominences is None or len(prominences) != len(peaks):
            prominences = np.ones(len(peaks), dtype=float) * 0.02
        for pi_idx, pi in enumerate(peaks):
            fid = int(fids[pi])
            elb = _row_at_frame(angles_df, fid)
            elbow_ang = float(elb["elbow_angle"]) if elb is not None and not pd.isna(elb["elbow_angle"]) else 140.0
            elbow_score = np.clip((elbow_ang - 130.0) / 50.0, 0.0, 1.0)
            prom = float(prominences[pi_idx])
            prom_n = min(1.0, prom / 0.05)
            wconf = float(confs[pi])
            score = 0.45 * elbow_score + 0.35 * prom_n + 0.20 * wconf
            candidates.append((fid, score, "peak"))

        if not candidates:
            pi = int(np.argmax(inverted))
            fid = int(fids[pi])
            candidates.append((fid, 0.4, "argmax_fallback"))

        if len(yvals) >= 3:
            dy = np.diff(yvals.astype(float))
            for i in range(1, len(dy)):
                if dy[i - 1] < 0 and dy[i] >= 0:
                    fid = int(fids[i])
                    if fid > crouch_frame:
                        elb = _row_at_frame(angles_df, fid)
                        elbow_ang = (
                            float(elb["elbow_angle"])
                            if elb is not None and not pd.isna(elb["elbow_angle"])
                            else 150.0
                        )
                        score = 0.5 + 0.02 * (elbow_ang - 150.0) / 30.0
                        candidates.append((fid, float(np.clip(score, 0.2, 0.95)), "vel_zero"))

        best_fid, best_score, best_kind = max(candidates, key=lambda t: t[1])
        elb = _row_at_frame(angles_df, best_fid)
        match_conf = confs[np.where(fids == best_fid)[0]]
        wconf = float(match_conf[0]) if len(match_conf) else 0.7
        if elb is not None:
            wconf = float(min(wconf, elb.get("confidence_wrist", wconf)))

        for fid, sc, kind in candidates:
            diag["candidates"].append(
                {"frame_id": fid, "score": float(sc), "kind": kind}
            )
        diag["chosen"] = {"frame_id": best_fid, "score": float(best_score), "kind": best_kind}
        return best_fid, float(max(0.2, min(1.0, best_score * wconf))), diag

    def _detect_start_signal(
        self,
        angles_df: pd.DataFrame,
        crouch_frame: int,
        frame_ids: np.ndarray,
    ) -> Tuple[int, Dict[str, Any]]:
        knee = angles_df["knee_angle"].values.astype(float)
        fids = angles_df["frame_id"].values.astype(int)
        if len(knee) < self.stable_window + 2:
            fallback = max(int(fids.min()) if len(fids) else 0, crouch_frame - self.pre_frames)
            return fallback, {"confidence": 0.3, "reason": "short_series"}

        best_start = max(int(fids.min()), crouch_frame - self.pre_frames)
        best_conf = 0.4

        for i in range(len(knee) - self.stable_window):
            if fids[i + self.stable_window - 1] >= crouch_frame:
                break
            window = knee[i : i + self.stable_window]
            if np.any(np.isnan(window)):
                continue
            energy = float(np.std(window))
            if energy < self.motion_energy_threshold:
                cand = int(fids[i])
                conf = 0.85 - min(0.4, energy / 10.0)
                if conf > best_conf:
                    best_conf = conf
                    best_start = cand

        return best_start, {"confidence": float(best_conf), "reason": "low_motion_window"}

    def _detect_end_signal(
        self,
        wrist_s: pd.DataFrame,
        release_frame: int,
        fid_max: int,
    ) -> Tuple[int, Dict[str, Any]]:
        if wrist_s.empty or len(wrist_s) < 3:
            return min(fid_max, release_frame + self.post_frames), {
                "confidence": 0.4,
                "reason": "post_release_fallback",
            }

        after = wrist_s[wrist_s["frame_id"] >= release_frame].copy()
        if after.empty:
            return min(fid_max, release_frame + self.post_frames), {
                "confidence": 0.4,
                "reason": "no_wrist_after",
            }

        y = after["y"].astype(float).values
        f = after["frame_id"].values.astype(int)
        settle_idx = None
        if len(y) >= self.stable_window + 2:
            dy = np.abs(np.diff(y))
            for i in range(len(dy) - self.stable_window):
                if float(np.mean(dy[i : i + self.stable_window])) < 0.003:
                    settle_idx = i + self.stable_window
                    break
        if settle_idx is not None:
            end_f = int(min(fid_max, f[min(settle_idx, len(f) - 1)]))
            return end_f, {"confidence": 0.75, "reason": "wrist_settle"}

        cap = release_frame + self.post_frames
        for j in range(len(f) - 1):
            if f[j] >= cap:
                return int(min(fid_max, f[j])), {
                    "confidence": 0.55,
                    "reason": "cap_frames",
                }
        return int(min(fid_max, release_frame + self.post_frames)), {
            "confidence": 0.5,
            "reason": "post_release_default",
        }

    def export_shot_window_json(self, shot_window: Dict[str, Any], output_path: Path):
        export = {k: v for k, v in shot_window.items() if k != "diagnostics"}
        export["diagnostics"] = shot_window.get("diagnostics", {})
        with open(output_path, "w") as f:
            json.dump(export, f, indent=2)


def detect_shot_window(
    angles_csv: Path,
    pose_keypoints_csv: Path,
    shooting_side: str,
    config: Dict[str, Any],
    output_path: Path,
) -> Dict[str, Any]:
    angles_df = pd.read_csv(angles_csv)
    pose_df = pd.read_csv(pose_keypoints_csv)
    detector = ShotDetector(config)
    shot_window = detector.detect_shot_window(angles_df, pose_df, shooting_side)
    detector.export_shot_window_json(shot_window, output_path)
    return shot_window
