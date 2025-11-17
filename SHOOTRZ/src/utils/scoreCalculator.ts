/**
 * Score calculation utilities for normalizing metric values to 0-25 scale
 * based on research-validated normative ranges.
 */

interface NormativeRange {
  target_range?: number[];
  optimal_range?: number[];
  unit?: string;
}

/**
 * Calculate a normalized score (0-25) based on how close a value is to optimal range.
 * 
 * @param value - The actual metric value (e.g., angle in degrees)
 * @param targetRange - [min, max] acceptable range
 * @param optimalRange - [min, max] optimal range (if provided, used for bonus)
 * @param invert - If true, lower values are better (e.g., forearm verticality)
 * @returns Score from 0-25
 */
export function calculateMetricScore(
  value: number,
  targetRange: number[],
  optimalRange?: number[],
  invert: boolean = false
): number {
  if (!targetRange || targetRange.length !== 2) {
    return 0; // No range data = no score
  }

  const [targetMin, targetMax] = targetRange;
  const [optimalMin = targetMin, optimalMax = targetMax] = optimalRange || targetRange;

  // Handle inverted metrics (lower is better)
  if (invert) {
    // For inverted metrics, being in optimal range gives full score
    if (value >= optimalMin && value <= optimalMax) {
      return 25; // Perfect
    }
    if (value >= targetMin && value <= targetMax) {
      // Linear interpolation within target range
      const distFromOptimal = Math.min(
        Math.abs(value - optimalMin),
        Math.abs(value - optimalMax)
      );
      const rangeSize = targetMax - targetMin;
      const score = 25 * (1 - distFromOptimal / rangeSize);
      return Math.max(0, Math.min(25, score));
    }
    // Outside target range - penalize heavily
    const distFromTarget = value < targetMin 
      ? targetMin - value 
      : value - targetMax;
    const penalty = distFromTarget * 2; // Harsh penalty for being outside
    return Math.max(0, 25 - penalty);
  }

  // Normal metrics (being in range is better)
  if (value >= optimalMin && value <= optimalMax) {
    return 25; // Perfect
  }
  
  if (value >= targetMin && value <= targetMax) {
    // Within target but not optimal - linear interpolation
    const rangeCenter = (targetMin + targetMax) / 2;
    const optimalCenter = (optimalMin + optimalMax) / 2;
    const distFromOptimal = Math.abs(value - optimalCenter);
    const maxDist = (targetMax - targetMin) / 2;
    const score = 20 + (5 * (1 - distFromOptimal / maxDist)); // 20-25 range
    return Math.max(20, Math.min(25, score));
  }

  // Outside target range - calculate penalty
  let distFromTarget: number;
  if (value < targetMin) {
    distFromTarget = targetMin - value;
  } else {
    distFromTarget = value - targetMax;
  }

  // Penalize based on distance from target range
  const rangeSize = targetMax - targetMin;
  const normalizedDistance = distFromTarget / rangeSize;
  const penalty = normalizedDistance * 25; // Max penalty is full score
  
  return Math.max(0, 25 - penalty);
}

/**
 * Calculate score for elbow angle (uses elbow_flexion_release if available).
 * Optimal: 170-180°, Target: 165-180°
 */
export function calculateElbowScore(metrics: any[]): number {
  // Try to find release phase elbow flexion first
  let metric = metrics.find((m: any) => m.metric_name === 'elbow_flexion_release');
  
  // Fallback to crouch phase
  if (!metric) {
    metric = metrics.find((m: any) => m.metric_name === 'elbow_flexion_crouch');
  }
  
  // Fallback to generic elbow_angle
  if (!metric) {
    metric = metrics.find((m: any) => m.metric_name === 'elbow_angle');
  }

  if (!metric || !metric.value) {
    return 0;
  }

  const value = metric.value;
  // Based on normative_ranges.json: optimal 170-180°, target 165-180°
  return calculateMetricScore(value, [165, 180], [170, 180], false);
}

/**
 * Calculate score for knee angle (knee_flexion).
 * Optimal: 105-115°, Target: 100-120°
 */
export function calculateKneeScore(metrics: any[]): number {
  const metric = metrics.find((m: any) => m.metric_name === 'knee_flexion');
  
  if (!metric || !metric.value) {
    return 0;
  }

  const value = metric.value;
  // Based on normative_ranges.json: optimal 105-115°, target 100-120°
  return calculateMetricScore(value, [100, 120], [105, 115], false);
}

/**
 * Calculate score for release angle.
 * Optimal depends on shot distance, but default: 45-55° for mid-range
 */
export function calculateReleaseScore(metrics: any[]): number {
  const metric = metrics.find((m: any) => m.metric_name === 'release_angle');
  
  if (!metric || !metric.value) {
    return 0;
  }

  const value = metric.value;
  // Default mid-range optimal: 45-55°, target: 40-60°
  // For different distances, use specific ranges from normative_ranges.json
  return calculateMetricScore(value, [40, 60], [45, 55], false);
}

/**
 * Calculate score for body alignment (uses shoulder alignment or hip alignment).
 * This is a composite metric - try to find alignment-related metrics.
 */
export function calculateAlignmentScore(metrics: any[]): number {
  // Look for shoulder alignment or similar metrics
  let metric = metrics.find((m: any) => 
    m.metric_name.includes('alignment') || 
    m.metric_name.includes('shoulder') ||
    m.metric_name.includes('body')
  );

  if (!metric || !metric.value) {
    // No alignment metric found - return baseline score
    return 12; // Middle of range
  }

  const value = metric.value;
  // For alignment, smaller deviations are better
  // Assuming value is deviation from optimal (0 is perfect)
  // Target: 0-10°, Optimal: 0-5°
  return calculateMetricScore(value, [0, 10], [0, 5], true);
}

/**
 * Calculate score for elbow position (forearm verticality).
 * Lower is better - optimal: 0-8°, target: 0-10°
 */
export function calculateElbowPositionScore(metrics: any[]): number {
	const metric = metrics.find((m: any) => m.metric_name === 'forearm_verticality')

	if (!metric || !metric.value) {
		return 0
	}

	const value = metric.value
	// Lower is better - optimal: 0-8°, target: 0-10°
	return calculateMetricScore(value, [0, 10], [0, 8], true)
}

/**
 * Calculate score for release height (elbow_height).
 * Optimal: 147-153cm, Target: 145-155cm
 */
export function calculateReleaseHeightScore(metrics: any[]): number {
	const metric = metrics.find((m: any) => m.metric_name === 'elbow_height')

	if (!metric || !metric.value) {
		return 0
	}

	const value = metric.value
	// Optimal: 147-153cm, Target: 145-155cm
	return calculateMetricScore(value, [145, 155], [147, 153], false)
}

/**
 * Calculate score for knee-to-toe alignment (combined knee_flexion + hip_flexion).
 * Combines knee flexion score with alignment check
 */
export function calculateKneeAlignmentScore(metrics: any[]): number {
	const kneeMetric = metrics.find((m: any) => m.metric_name === 'knee_flexion')
	const hipMetric = metrics.find((m: any) => m.metric_name === 'hip_flexion')

	if (!kneeMetric || !kneeMetric.value) {
		return 0
	}

	// Calculate knee flexion score
	const kneeValue = kneeMetric.value
	const kneeScore = calculateMetricScore(kneeValue, [100, 120], [105, 115], false)

	// If hip flexion is available, use it to adjust score (for alignment)
	if (hipMetric && hipMetric.value) {
		const hipValue = hipMetric.value
		const hipScore = calculateMetricScore(hipValue, [140, 160], [145, 155], false)
		// Weighted average: 70% knee, 30% hip alignment
		return Math.round(kneeScore * 0.7 + hipScore * 0.3)
	}

	return kneeScore
}

/**
 * Calculate score for arc height.
 * Context-aware: depends on shot distance
 * Default optimal: 3.8-4.0m, target: 3.6-4.1m
 */
export function calculateArcHeightScore(metrics: any[], shotDistance?: number): number {
	const metric = metrics.find((m: any) => m.metric_name === 'arc_height')

	if (!metric || !metric.value || metric.confidence === 0) {
		return 0
	}

	const value = metric.value // in meters
	
	// If value is negative or 0, return 0 (invalid measurement)
	if (value <= 0) {
		return 0
	}

	// Context-aware: adjust optimal range based on shot distance
	let targetRange: [number, number] = [3.6, 4.1]
	let optimalRange: [number, number] = [3.8, 4.0]

	if (shotDistance) {
		// Closer shots need less arc, farther shots need more
		if (shotDistance < 3) {
			// Close range
			targetRange = [3.4, 3.9]
			optimalRange = [3.6, 3.8]
		} else if (shotDistance > 6) {
			// Long range
			targetRange = [3.8, 4.3]
			optimalRange = [4.0, 4.2]
		}
	}

	return calculateMetricScore(value, targetRange, optimalRange, false)
}

/**
 * Calculate score for entry angle.
 * Optimal: 48-52°, Target: 45-55°
 */
export function calculateEntryAngleScore(metrics: any[]): number {
	const metric = metrics.find((m: any) => m.metric_name === 'entry_angle')

	if (!metric || !metric.value) {
		return 0
	}

	const value = metric.value
	// Optimal: 48-52°, Target: 45-55°
	return calculateMetricScore(value, [45, 55], [48, 52], false)
}

/**
 * Calculate score for grip quality (0-1 scale to 0-25).
 * Optimal: 0.85-1.0, Target: 0.7-1.0
 */
export function calculateGripScore(metrics: any[]): number {
	const metric = metrics.find((m: any) => m.metric_name === 'grip_quality')

	if (!metric || !metric.value) {
		return 0
	}

	const value = metric.value // 0-1 scale
	// Optimal: 0.85-1.0, Target: 0.7-1.0
	return calculateMetricScore(value, [0.7, 1.0], [0.85, 1.0], false)
}

/**
 * Calculate score for follow-through (wrist angular velocity).
 * Minimum threshold: 2.5 rad/s, Optimal: 3.0+ rad/s
 */
export function calculateFollowThroughScore(metrics: any[]): number {
	const metric = metrics.find((m: any) => m.metric_name === 'wrist_angular_velocity')

	if (!metric || !metric.value) {
		return 0
	}

	const value = metric.value // rad/s

	// Minimum threshold: 2.5 rad/s, Optimal: 3.0+ rad/s
	// This is a minimum-threshold metric (higher is better, but with minimum)
	if (value >= 3.0) {
		return 25 // Perfect
	}
	if (value >= 2.5) {
		// Between threshold and optimal: linear interpolation
		const score = ((value - 2.5) / (3.0 - 2.5)) * 10 + 15 // 15-25 range
		return Math.round(score)
	}
	// Below threshold: penalty
	const penalty = (2.5 - value) * 10
	return Math.max(0, Math.round(15 - penalty))
}

/**
 * Calculate total score (0-100) from all individual scores.
 * Updated to include new metrics with appropriate weighting.
 */
export function calculateTotalScore(
	elbowScore: number,
	kneeScore: number,
	releaseScore: number,
	alignmentScore: number
): number {
	// Simple sum of all scores (each out of 25)
	return Math.round(elbowScore + kneeScore + releaseScore + alignmentScore)
}

/**
 * Calculate comprehensive total score including all new metrics.
 * Optional: Use this for more detailed scoring if all metrics are available.
 */
export function calculateComprehensiveTotalScore(
	coreScores: {
		elbowPosition: number
		releaseHeight: number
		kneeAlignment: number
		arcHeight: number
		entryAngle: number
	},
	technicalScores: {
		grip: number
		followThrough: number
	}
): number {
	// Core metrics: 60% weight (6 metrics * 10% each)
	const coreTotal =
		coreScores.elbowPosition +
		coreScores.releaseHeight +
		coreScores.kneeAlignment +
		coreScores.arcHeight +
		coreScores.entryAngle
	const coreWeighted = (coreTotal / 125) * 60 // Normalize to 60 points

	// Technical metrics: 40% weight (2 metrics * 20% each)
	const technicalTotal = technicalScores.grip + technicalScores.followThrough
	const technicalWeighted = (technicalTotal / 50) * 40 // Normalize to 40 points

	return Math.round(coreWeighted + technicalWeighted)
}

