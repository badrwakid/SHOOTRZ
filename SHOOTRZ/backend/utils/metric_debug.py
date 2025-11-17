"""
Debug utilities for metric computation.

Helps identify which metrics are missing and why.
"""

from typing import Dict, List, Any


def analyze_metrics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
	"""
	Analyze computed metrics and identify missing ones.
	
	Args:
		metrics: List of computed metrics
		
	Returns:
		Dict with analysis results
	"""
	expected_metrics = {
		"forearm_verticality": "Elbow Position",
		"elbow_flexion_release": "Elbow Angle (Release)",
		"elbow_flexion_crouch": "Elbow Angle (Crouch)",
		"knee_flexion": "Knee Alignment",
		"hip_flexion": "Hip Alignment",
		"elbow_height": "Release Height",
		"release_angle": "Release Angle",
		"entry_angle": "Entry Angle",
		"arc_height": "Arc Height",
		"release_height": "Release Height",
		"wrist_angular_velocity": "Follow Through",
		"grip_quality": "Grip Quality",
	}
	
	computed_metrics = {m["metric_name"]: m for m in metrics}
	missing = []
	low_confidence = []
	
	for metric_name, display_name in expected_metrics.items():
		if metric_name not in computed_metrics:
			missing.append(display_name)
		else:
			metric = computed_metrics[metric_name]
			if metric.get("confidence", 1.0) < 0.5:
				low_confidence.append(display_name)
	
	return {
		"total_expected": len(expected_metrics),
		"total_computed": len(metrics),
		"missing_metrics": missing,
		"low_confidence_metrics": low_confidence,
		"computed_metric_names": list(computed_metrics.keys()),
	}


def log_metric_computation(metrics: List[Dict[str, Any]], phase: str = "computation"):
	"""
	Log metric computation results for debugging.
	
	Args:
		metrics: List of computed metrics
		phase: Phase name for logging
	"""
	analysis = analyze_metrics(metrics)
	
	print(f"\n=== Metric {phase} Analysis ===")
	print(f"Computed: {analysis['total_computed']}/{analysis['total_expected']} metrics")
	
	if analysis["missing_metrics"]:
		print(f"\nMissing metrics ({len(analysis['missing_metrics'])}):")
		for metric in analysis["missing_metrics"]:
			print(f"  - {metric}")
	
	if analysis["low_confidence_metrics"]:
		print(f"\nLow confidence metrics ({len(analysis['low_confidence_metrics'])}):")
		for metric in analysis["low_confidence_metrics"]:
			print(f"  - {metric}")
	
	if analysis["computed_metric_names"]:
		print(f"\nComputed metrics:")
		for name in analysis["computed_metric_names"]:
			metric = next(m for m in metrics if m["metric_name"] == name)
			conf = metric.get("confidence", 0.0)
			value = metric.get("value", 0.0)
			print(f"  - {name}: {value:.2f} (confidence: {conf:.2f})")

