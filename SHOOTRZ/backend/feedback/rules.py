"""
Research-validated feedback rules for basketball shooting analysis.

Maps metric deviations to user-friendly coaching cues with severity levels.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path


# Load normative ranges
NORMATIVE_RANGES_PATH = Path(__file__).parent.parent / "metrics" / "normative_ranges.json"

try:
	with open(NORMATIVE_RANGES_PATH, "r") as f:
		NORMATIVE_RANGES = json.load(f)
except FileNotFoundError:
	NORMATIVE_RANGES = {}


def load_normative_ranges() -> Dict:
	"""Load normative ranges from JSON file."""
	return NORMATIVE_RANGES


def check_threshold(
	value: float,
	threshold: float,
	comparison: str,
) -> bool:
	"""
	Check if value meets threshold condition.
	
	Args:
		value: Metric value
		threshold: Threshold value
		comparison: '>', '<', '>=', '<=', 'outside_range'
	
	Returns:
		True if condition met
	"""
	if comparison == ">":
		return value > threshold
	elif comparison == "<":
		return value < threshold
	elif comparison == ">=":
		return value >= threshold
	elif comparison == "<=":
		return value <= threshold
	elif comparison == "outside_range":
		# threshold should be a list [min, max]
		if isinstance(threshold, list) and len(threshold) == 2:
			return value < threshold[0] or value > threshold[1]
	return False


def get_forearm_verticality_feedback(value: float, confidence: float) -> Optional[Dict]:
	"""
	Generate feedback for forearm verticality.
	
	Based on Cabarkapa et al. (2021):
	- Target: 0-10° (proficient: 7.9° ± 7.2°)
	- Warning if >15°
	"""
	if confidence < 0.5:
		return None

	range_info = NORMATIVE_RANGES.get("forearm_verticality", {})
	target_range = range_info.get("target_range", [0, 10])
	optimal_range = range_info.get("optimal_range", [0, 8])

	if value > 15:
		return {
			"message": "Keep your forearm closer to vertical during the preparatory phase.",
			"severity": "warning",
			"details": (
				f"Your forearm was {value:.1f}° away from vertical. "
				f"Proficient shooters maintain 0-10° (optimal: 0-8°). "
				"Keep your elbow underneath the ball and your forearm upright for better control."
			),
			"metric_name": "forearm_verticality",
			"value": value,
		}
	elif value < -5:
		return {
			"message": "Your forearm is too far backward; bring the elbow forward.",
			"severity": "info",
			"details": "Bring your shooting elbow forward to align with the vertical axis.",
			"metric_name": "forearm_verticality",
			"value": value,
		}
	elif value > optimal_range[1]:
		return {
			"message": "Slight improvement: align forearm closer to vertical.",
			"severity": "info",
			"details": f"Your forearm angle ({value:.1f}°) is acceptable but could be improved to 0-8° for optimal control.",
			"metric_name": "forearm_verticality",
			"value": value,
		}

	return None


def get_elbow_flexion_feedback(
	value: float,
	phase: str,
	confidence: float,
) -> Optional[Dict]:
	"""
	Generate feedback for elbow flexion.
	
	Based on Cabarkapa et al. (2021):
	- Preparatory: 70-85° (proficient: 80.5° ± 6.3°)
	- Release: 165-180° (extension)
	"""
	if confidence < 0.5:
		return None

	if phase == "preparatory" or phase == "crouch":
		range_info = NORMATIVE_RANGES.get("elbow_flexion_preparatory", {})
		target_range = range_info.get("target_range", [70, 85])

		if value < 70:
			return {
				"message": "Bend your elbow more during the preparatory phase (70-85°).",
				"severity": "warning",
				"details": (
					f"Your elbow angle was {value:.1f}°. "
					f"Proficient shooters maintain 70-85° during preparation. "
					"Bending the elbow properly sets up for a smooth release."
				),
				"metric_name": "elbow_flexion_preparatory",
				"value": value,
			}
		elif value > 85:
			return {
				"message": "Your elbow is too flexed; extend slightly more (70-85° range).",
				"severity": "info",
				"details": "Slightly extend your elbow to the optimal 70-85° range.",
				"metric_name": "elbow_flexion_preparatory",
				"value": value,
			}

	elif phase == "release":
		range_info = NORMATIVE_RANGES.get("elbow_flexion_release", {})
		target_range = range_info.get("target_range", [165, 180])

		if value < 165:
			return {
				"message": "Extend your elbow more fully at release (165-180°).",
				"severity": "warning",
				"details": (
					f"Your elbow extension was {value:.1f}° at release. "
					"Fully extend your arm (165-180°) for maximum power and accuracy."
				),
				"metric_name": "elbow_flexion_release",
				"value": value,
			}

	return None


def get_knee_flexion_feedback(value: float, confidence: float) -> Optional[Dict]:
	"""
	Generate feedback for knee flexion.
	
	Based on Cabarkapa et al. (2021):
	- Target: 100-120° (proficient ~108°)
	- Non-proficient typically <100°
	"""
	if confidence < 0.5:
		return None

	range_info = NORMATIVE_RANGES.get("knee_flexion", {})
	target_range = range_info.get("target_range", [100, 120])
	optimal_range = range_info.get("optimal_range", [105, 115])

	if value < 100:
		return {
			"message": "Deeper knee bend generates more power (target: 100-120°).",
			"severity": "warning",
			"details": (
				f"Your knee flexion was {value:.1f}°. "
				f"Proficient shooters bend to 100-120° (optimal: 105-115°). "
				"Deeper flexion improves balance and power generation."
			),
			"metric_name": "knee_flexion",
			"value": value,
		}
	elif value > 120:
		return {
			"message": "Slightly less knee bend (100-120° range) for optimal balance.",
			"severity": "info",
			"details": "Your knee bend is slightly too deep. Aim for 100-120° for optimal balance.",
			"metric_name": "knee_flexion",
			"value": value,
		}

	return None


def get_release_angle_feedback(
	value: float,
	shot_distance: Optional[float],
	confidence: float,
) -> Optional[Dict]:
	"""
	Generate feedback for release angle.
	
	Based on Okazaki et al. (2012):
	- 2.8m: 78.92° ± 5° (74-84°)
	- 4.6m: 65.60° ± 5° (60-70°)
	- 6.0m+: 55-65°
	"""
	if confidence < 0.5:
		return None

	if shot_distance is None:
		return None

	# Determine expected range based on distance
	if shot_distance <= 3.0:
		expected_range = [74, 84]
		mean_angle = 78.92
		distance_label = "close"
	elif shot_distance <= 5.0:
		expected_range = [60, 70]
		mean_angle = 65.60
		distance_label = "mid-range"
	else:
		expected_range = [55, 65]
		mean_angle = 60.0
		distance_label = "long-range"

	# Check if outside expected range
	if value < expected_range[0]:
		return {
			"message": f"Release angle too low for {distance_label} shot. Increase your arc.",
			"severity": "warning",
			"details": (
				f"Your release angle was {value:.1f}°, but for {distance_label} shots "
				f"({shot_distance:.1f}m), aim for {expected_range[0]}-{expected_range[1]}°. "
				"Higher arc improves entry angle and scoring probability."
			),
			"metric_name": "release_angle",
			"value": value,
		}
	elif value > expected_range[1]:
		return {
			"message": f"Release angle slightly high for {distance_label} shot.",
			"severity": "info",
			"details": (
				f"Your release angle ({value:.1f}°) is above optimal for {distance_label} shots. "
				f"Target range: {expected_range[0]}-{expected_range[1]}°."
			),
			"metric_name": "release_angle",
			"value": value,
		}

	return None


def get_entry_angle_feedback(value: float, confidence: float) -> Optional[Dict]:
	"""
	Generate feedback for entry angle.
	
	Target: 45-55° for optimal entry
	"""
	if confidence < 0.5:
		return None

	range_info = NORMATIVE_RANGES.get("entry_angle", {})
	target_range = range_info.get("target_range", [45, 55])
	optimal_range = range_info.get("optimal_range", [48, 52])

	if value < 45:
		return {
			"message": "Increase arc height for better entry angle (target: 45-55°).",
			"severity": "error",
			"details": (
				f"Your entry angle was {value:.1f}°. "
				"Steeper entry (45-55°) increases scoring chance. "
				"Increase your release angle to achieve a higher arc."
			),
			"metric_name": "entry_angle",
			"value": value,
		}
	elif value > 55:
		return {
			"message": "Entry angle is good but could be slightly lower.",
			"severity": "info",
			"details": f"Entry angle ({value:.1f}°) is acceptable. Optimal range: 48-52°.",
			"metric_name": "entry_angle",
			"value": value,
		}

	return None


def get_wrist_velocity_feedback(value: float, confidence: float) -> Optional[Dict]:
	"""
	Generate feedback for wrist angular velocity.
	
	Target: >2.5 rad/s within 100-150ms after release
	"""
	if confidence < 0.5:
		return None

	range_info = NORMATIVE_RANGES.get("wrist_angular_velocity", {})
	target_min = range_info.get("target_min", 2.5)

	if value < target_min:
		return {
			"message": "Faster wrist flick improves spin (target: >2.5 rad/s).",
			"severity": "info",
			"details": (
				f"Your wrist angular velocity was {value:.2f} rad/s. "
				"A faster wrist flick (>2.5 rad/s) generates better backspin and control."
			),
			"metric_name": "wrist_angular_velocity",
			"value": value,
		}

	return None


def get_grip_quality_feedback(value: float, confidence: float) -> Optional[Dict]:
	"""
	Generate feedback for grip quality.
	
	Target: 0.7-1.0 score (optimal: 0.85-1.0)
	"""
	if confidence < 0.5:
		return None

	range_info = NORMATIVE_RANGES.get("grip_quality", {})
	target_range = range_info.get("target_range", [0.7, 1.0])
	optimal_range = range_info.get("optimal_range", [0.85, 1.0])

	if value < target_range[0]:
		return {
			"message": "Improve grip quality: maintain 2-3cm gap between thumb and index finger.",
			"severity": "warning",
			"details": (
				f"Your grip quality score was {value:.2f}. "
				"Maintain proper finger spread (2-3cm) and minimize palm contact for better control."
			),
			"metric_name": "grip_quality",
			"value": value,
		}

	return None


def rules_from_metrics(metrics: List[Dict]) -> List[Dict]:
	"""
	Generate feedback rules from computed metrics.
	
	Args:
		metrics: List of metric dictionaries with 'metric_name', 'value', 'confidence', etc.
	
	Returns:
		List of feedback dictionaries with 'message', 'severity', 'details'
	"""
	feedback_list = []
	metrics_dict = {m.get("metric_name"): m for m in metrics}

	# Forearm verticality
	if "forearm_verticality" in metrics_dict:
		m = metrics_dict["forearm_verticality"]
		fb = get_forearm_verticality_feedback(m.get("value", 0), m.get("confidence", 0))
		if fb:
			feedback_list.append(fb)

	# Elbow flexion (preparatory)
	if "elbow_flexion_preparatory" in metrics_dict:
		m = metrics_dict["elbow_flexion_preparatory"]
		fb = get_elbow_flexion_feedback(
			m.get("value", 0),
			m.get("phase", "preparatory"),
			m.get("confidence", 0),
		)
		if fb:
			feedback_list.append(fb)

	# Elbow flexion (release)
	if "elbow_flexion_release" in metrics_dict:
		m = metrics_dict["elbow_flexion_release"]
		fb = get_elbow_flexion_feedback(
			m.get("value", 0),
			"release",
			m.get("confidence", 0),
		)
		if fb:
			feedback_list.append(fb)

	# Knee flexion
	if "knee_flexion" in metrics_dict:
		m = metrics_dict["knee_flexion"]
		fb = get_knee_flexion_feedback(m.get("value", 0), m.get("confidence", 0))
		if fb:
			feedback_list.append(fb)

	# Release angle
	if "release_angle" in metrics_dict:
		m = metrics_dict["release_angle"]
		fb = get_release_angle_feedback(
			m.get("value", 0),
			m.get("shot_distance"),
			m.get("confidence", 0),
		)
		if fb:
			feedback_list.append(fb)

	# Entry angle
	if "entry_angle" in metrics_dict:
		m = metrics_dict["entry_angle"]
		fb = get_entry_angle_feedback(m.get("value", 0), m.get("confidence", 0))
		if fb:
			feedback_list.append(fb)

	# Wrist angular velocity
	if "wrist_angular_velocity" in metrics_dict:
		m = metrics_dict["wrist_angular_velocity"]
		fb = get_wrist_velocity_feedback(m.get("value", 0), m.get("confidence", 0))
		if fb:
			feedback_list.append(fb)

	# Grip quality
	if "grip_quality" in metrics_dict:
		m = metrics_dict["grip_quality"]
		fb = get_grip_quality_feedback(m.get("value", 0), m.get("confidence", 0))
		if fb:
			feedback_list.append(fb)

	return feedback_list
