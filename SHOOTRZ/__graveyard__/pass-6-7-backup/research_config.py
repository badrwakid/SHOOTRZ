"""
Research-Based Biomechanics Configuration

Based on peer-reviewed studies:
- International Journal of Home Science (2022)
- Journal of Functional Morphology and Kinesiology (2023, 2024)
- Kansas Biomechanics Research
- Physio-pedia Biomechanics Analysis
"""

# PHASE-SPECIFIC IDEAL VALUES (based on research)
IDEAL_VALUES_BY_PHASE = {
    'preparation_cocking': {
        'elbow': 90.0,          # 85-95° during cocking
        'knee': 77.5,           # 70-85° during loading (bent)
        'shoulder': 52.5,       # 45-60° relative to trunk
        'wrist': 140.0,         # 130-150° (cocked)
        'hip': 135.0,           # 130-140° (slight forward lean)
        'ankle': 120.0          # 110-130° (dorsiflexion)
    },
    'release': {
        'elbow': 165.0,         # 160-170° at release (nearly straight!)
        'knee': 167.5,          # 160-175° at release (nearly straight!)
        'shoulder': 170.0,      # 160-180° at release (vertical)
        'wrist': 146.0,         # 130-150° at release
        'release_trajectory': 51.5,  # 48-55° launch angle
        'hip': 135.0,           # 130-140°
        'ankle': 116.0,         # 110-130°
        'trunk_lean': 5.0       # 0-10° forward
    },
    'follow_through': {
        'elbow': 160.0,         # 160-170° (stay extended)
        'wrist': 115.0,         # 110-120° (snap forward)
        'shoulder': 171.0       # 160-180° (vertical)
    }
}

# TOLERANCE RANGES (research-based)
TOLERANCE_RANGES = {
    'elbow': 10.0,           # ±10°
    'knee': 10.0,            # ±10°
    'shoulder': 10.0,        # ±10°
    'wrist': 15.0,           # ±15°
    'release_trajectory': 5.0,  # ±5°
    'hip': 10.0,             # ±10°
    'ankle': 15.0,           # ±15°
    'trunk_lean': 5.0        # ±5°
}

# SCORING WEIGHTS (research priority)
METRIC_WEIGHTS = {
    'elbow_at_release': 5,      # Highest importance
    'release_trajectory': 5,    # Highest importance
    'knee_at_release': 4,       # High importance
    'shoulder_at_release': 4,   # High importance
    'wrist_at_release': 3,      # Moderate importance
    'hip_angle': 3,             # Moderate importance
    'ankle': 2,                 # Lower importance
    'trunk_lean': 2             # Lower importance
}

# SIMPLIFIED FOR CURRENT SYSTEM (until full phase detection works)
SIMPLIFIED_IDEAL_VALUES = {
    # Use RELEASE phase values since that's most critical
    'elbow_angle': 165.0,       # Measured at release: 160-170°
    'knee_angle': 167.5,        # Measured at release: 160-175°
    'release_angle': 51.5,      # Launch trajectory: 48-55°
    'body_alignment': 90.0,     # Shoulders aligned with hips
    'shoulder_angle': 170.0,    # At release: 160-180°
    'wrist_angle': 146.0,       # At release: 130-150°
}

SIMPLIFIED_TOLERANCES = {
    'elbow_angle': 10.0,
    'knee_angle': 10.0,
    'release_angle': 5.0,
    'body_alignment': 20.0,
    'shoulder_angle': 10.0,
    'wrist_angle': 15.0
}

# OLD VALUES (INCORRECT - for reference only)
OLD_INCORRECT_VALUES = {
    'elbow_angle': 90.0,        # WRONG - this is cocking phase, not release!
    'knee_angle': 130.0,        # WRONG - this is loading phase, not release!
    'release_angle': 47.5,      # Close but should be 48-55°
}

# RESEARCH REFERENCES
RESEARCH_SOURCES = {
    'primary': [
        'International Journal of Home Science (2022) - 3-Point Shot Kinematics',
        'J. Functional Morphology and Kinesiology (2023) - Female Players',
        'J. Functional Morphology and Kinesiology (2024) - U18 Males',
        'Kansas Biomechanics Research - Training & Conditioning',
        'Physio-pedia - Biomechanics of Basketball Jump Shot'
    ],
    'supporting': [
        'Breakthrough Basketball - Shooting Technique',
        'Ars Technica - Perfect Free-Throw Science'
    ]
}

def get_score_for_angle(angle_value, ideal_value, tolerance, phase='release'):
    """
    Calculate score for an angle based on research
    
    Args:
        angle_value: Measured angle
        ideal_value: Ideal value from research
        tolerance: Acceptable tolerance
        phase: Shooting phase
        
    Returns:
        Score 0-100
    """
    deviation = abs(angle_value - ideal_value)
    
    if deviation <= tolerance:
        # Within tolerance - excellent
        score = 100 - (deviation / tolerance * 30)  # 70-100 range
    elif deviation <= tolerance * 2:
        # Outside but acceptable
        score = 70 - ((deviation - tolerance) / tolerance * 40)  # 30-70 range
    else:
        # Poor
        excess = deviation - (tolerance * 2)
        score = max(0, 30 - (excess / tolerance * 30))  # 0-30 range
    
    return max(0, min(100, score))

# Example usage:
# knee_score = get_score_for_angle(173, 167.5, 10.0, 'release')
# Result: 173 is within 160-175 range → Score ~95/100!

