"""
Enhanced Tip Generation System with Biomechanics Explanations

Generates comprehensive coaching tips with:
- Biomechanics explanations
- Injury prevention advice
- Professional player references
- Progressive drill recommendations
- Phase-specific feedback
"""

def generate_tips(metrics, confidence_scores=None, advanced_metrics=None, professional_comparison=None):
    """
    Generate comprehensive tips with biomechanics explanations
    
    Args:
        metrics: User's measured angles
        confidence_scores: Confidence scores for each metric
        advanced_metrics: Advanced metrics (follow-through, consistency, etc.)
        professional_comparison: Professional player comparison data
        
    Returns:
        dict: Comprehensive feedback with tips, insights, and recommendations
    """
    try:
        tips = []
        biomechanics_insights = []
        injury_prevention = []
        drill_recommendations = []
        
        # Generate tips for each metric
        tips.extend(_generate_elbow_tips(metrics, confidence_scores))
        tips.extend(_generate_release_tips(metrics, confidence_scores))
        tips.extend(_generate_knee_tips(metrics, confidence_scores))
        tips.extend(_generate_alignment_tips(metrics, confidence_scores))
        
        # Add advanced metrics tips
        if advanced_metrics:
            tips.extend(_generate_advanced_tips(advanced_metrics))
        
        # Add professional comparison insights
        if professional_comparison:
            tips.extend(_generate_professional_tips(professional_comparison))
        
        # Generate biomechanics insights
        biomechanics_insights = _generate_biomechanics_insights(metrics, advanced_metrics)
        
        # Generate injury prevention tips
        injury_prevention = _generate_injury_prevention_tips(metrics, advanced_metrics)
        
        # Generate drill recommendations
        drill_recommendations = _generate_drill_recommendations(metrics, advanced_metrics)
        
        return {
            'tips': tips[:5],  # Top 5 actionable tips
            'biomechanics_insights': biomechanics_insights,
            'injury_prevention': injury_prevention,
            'drill_recommendations': drill_recommendations,
            'priority_tips': _prioritize_tips(tips, confidence_scores)
        }
        
    except Exception as e:
        print(f"Error generating comprehensive tips: {e}")
        return {
            'tips': ["Keep practicing to improve your shooting form!"],
            'biomechanics_insights': [],
            'injury_prevention': [],
            'drill_recommendations': [],
            'priority_tips': []
        }

def _generate_elbow_tips(metrics, confidence_scores):
    """Generate elbow-specific tips with biomechanics explanations"""
    tips = []
    elbow_angle = metrics.get('elbow_angle', 0)
    confidence = confidence_scores.get('elbow_confidence', 50) if confidence_scores else 50
    
    if elbow_angle < 85:
        tips.append({
            'tip': "Your elbow is too closed. Straighten your shooting arm to 90° for optimal power transfer.",
            'biomechanics': "A 90° elbow angle maximizes force transfer through the kinetic chain from legs to fingertips.",
            'drill': "Wall touch drill: Stand 2 feet from wall, touch wall with fingertips at 90° angle, 3 sets of 20",
            'priority': 'high',
            'confidence': confidence
        })
    elif elbow_angle > 110:
        tips.append({
            'tip': "Your elbow is too open. Keep your shooting elbow at 90° to maintain control and consistency.",
            'biomechanics': "An open elbow reduces accuracy and power transfer, leading to inconsistent shots.",
            'drill': "Close-range shooting: Practice 3-5 feet from basket, focus on 90° elbow, 3 sets of 15",
            'priority': 'high',
            'confidence': confidence
        })
    elif 85 <= elbow_angle <= 95:
        tips.append({
            'tip': "Excellent elbow alignment! Your 90° shooting form is biomechanically optimal.",
            'biomechanics': "Your elbow angle allows for maximum force transfer and consistent release point.",
            'drill': "Maintain this form with form shooting: 3 sets of 10 shots from 5 feet",
            'priority': 'low',
            'confidence': confidence
        })
    
    return tips

def _generate_release_tips(metrics, confidence_scores):
    """Generate release angle tips with biomechanics explanations"""
    tips = []
    release_angle = metrics.get('release_angle', 0)
    confidence = confidence_scores.get('release_confidence', 50) if confidence_scores else 50
    
    if release_angle < 40:
        tips.append({
            'tip': "Increase your release angle to 45-50° to create optimal shot arc.",
            'biomechanics': "A 45-50° release angle provides the best trajectory for consistent shooting and soft rim contact.",
            'drill': "High arc shooting: Aim for the back of the rim, 3 sets of 15 shots from 10 feet",
            'priority': 'high',
            'confidence': confidence
        })
    elif release_angle > 60:
        tips.append({
            'tip': "Your release angle is too high. Lower it to 45-50° for a more consistent arc.",
            'biomechanics': "Excessive release angle reduces accuracy and makes the shot harder to control.",
            'drill': "Flat shot correction: Focus on 45° release, 3 sets of 15 shots from 8 feet",
            'priority': 'medium',
            'confidence': confidence
        })
    elif 45 <= release_angle <= 50:
        tips.append({
            'tip': "Perfect release angle! Your shot arc is biomechanically optimal.",
            'biomechanics': "Your release angle creates the ideal trajectory for consistent shooting success.",
            'drill': "Maintain with arc shooting: 3 sets of 10 shots from various distances",
            'priority': 'low',
            'confidence': confidence
        })
    
    return tips

def _generate_knee_tips(metrics, confidence_scores):
    """Generate knee bend tips with biomechanics explanations"""
    tips = []
    knee_angle = metrics.get('knee_angle', 0)
    confidence = confidence_scores.get('knee_confidence', 50) if confidence_scores else 50
    
    if knee_angle > 150:
        tips.append({
            'tip': "Bend your knees more (120-140°) for better power generation and lift.",
            'biomechanics': "Proper knee bend (120-140°) allows for optimal leg drive and power transfer to the shot.",
            'drill': "Squat hold drill: Hold 120° knee bend for 30 seconds, 3 sets",
            'priority': 'high',
            'confidence': confidence
        })
    elif knee_angle < 110:
        tips.append({
            'tip': "You're bending your knees too much. Aim for 120-140° for optimal balance.",
            'biomechanics': "Excessive knee bend reduces power transfer and can lead to inconsistent shooting rhythm.",
            'drill': "Shallow knee bend practice: Focus on 130° knee angle, 3 sets of 15 shots",
            'priority': 'medium',
            'confidence': confidence
        })
    elif 120 <= knee_angle <= 140:
        tips.append({
            'tip': "Excellent knee bend! Your leg positioning provides optimal power and balance.",
            'biomechanics': "Your knee angle allows for maximum leg drive and smooth power transfer to the upper body.",
            'drill': "Power shooting: 3 sets of 10 shots from 15 feet, emphasize leg drive",
            'priority': 'low',
            'confidence': confidence
        })
    
    return tips

def _generate_alignment_tips(metrics, confidence_scores):
    """Generate body alignment tips with biomechanics explanations"""
    tips = []
    body_alignment = metrics.get('body_alignment', 0)
    confidence = confidence_scores.get('alignment_confidence', 50) if confidence_scores else 50
    
    if body_alignment < 80:
        tips.append({
            'tip': "Keep your shoulders and hips aligned with the basket for better accuracy.",
            'biomechanics': "Proper body alignment ensures consistent shooting direction and reduces lateral forces.",
            'drill': "Square up drill: Practice squaring shoulders to basket, 3 sets of 20 shots",
            'priority': 'high',
            'confidence': confidence
        })
    elif body_alignment >= 90:
        tips.append({
            'tip': "Excellent body alignment! Your straight posture improves shooting consistency.",
            'biomechanics': "Your alignment minimizes lateral movement and ensures consistent shooting direction.",
            'drill': "Balance practice: 3 sets of 10 shots, maintain perfect alignment",
            'priority': 'low',
            'confidence': confidence
        })
    
    return tips

def _generate_advanced_tips(advanced_metrics):
    """Generate tips for advanced metrics"""
    tips = []
    
    # Follow-through tips
    follow_through = advanced_metrics.get('follow_through_angle', 0)
    if follow_through < 70:
        tips.append({
            'tip': "Improve your follow-through consistency for better shot control.",
            'biomechanics': "Consistent follow-through ensures proper wrist snap and shot direction.",
            'drill': "Wrist snap drill: Practice snapping wrist down, 3 sets of 20 reps",
            'priority': 'medium',
            'confidence': 80
        })
    
    # Consistency tips
    consistency = advanced_metrics.get('consistency_score', 0)
    if consistency < 70:
        tips.append({
            'tip': "Focus on repeating the same motion for better consistency.",
            'biomechanics': "Consistent form reduces variability and improves shooting accuracy.",
            'drill': "Repetition drill: 3 sets of 20 shots, same motion every time",
            'priority': 'high',
            'confidence': 85
        })
    
    # Jump timing tips
    jump_timing = advanced_metrics.get('jump_timing', 0)
    if jump_timing < 70:
        tips.append({
            'tip': "Coordinate your knee extension with your arm movement for better power transfer.",
            'biomechanics': "Proper timing ensures maximum power transfer from legs to shooting arm.",
            'drill': "Jump shot timing: Practice coordinating leg drive with release, 3 sets of 15",
            'priority': 'medium',
            'confidence': 75
        })
    
    return tips

def _generate_professional_tips(professional_comparison):
    """Generate tips based on professional player comparison"""
    tips = []
    
    if professional_comparison and 'best_match' in professional_comparison:
        best_match = professional_comparison['best_match']
        similarity = best_match.get('similarity', 0)
        player_name = best_match.get('name', 'professional player')
        
        if similarity >= 80:
            tips.append({
                'tip': f"Your form is {similarity}% similar to {player_name}! You're on the right track.",
                'biomechanics': f"Your shooting mechanics closely match {player_name}'s proven technique.",
                'drill': f"Study {player_name}'s form and practice their shooting style",
                'priority': 'low',
                'confidence': 90
            })
        elif similarity >= 60:
            tips.append({
                'tip': f"Your form is {similarity}% similar to {player_name}. Focus on the key differences.",
                'biomechanics': f"Your form has similarities to {player_name} but needs refinement in specific areas.",
                'drill': f"Work on the key differences from {player_name}'s form",
                'priority': 'medium',
                'confidence': 80
            })
        else:
            tips.append({
                'tip': f"Your form differs significantly from {player_name}. Focus on fundamental improvements.",
                'biomechanics': f"Your shooting mechanics need development to match {player_name}'s proven technique.",
                'drill': f"Focus on basic fundamentals before comparing to {player_name}",
                'priority': 'high',
                'confidence': 70
            })
    
    return tips

def _generate_biomechanics_insights(metrics, advanced_metrics):
    """Generate biomechanics insights"""
    insights = []
    
    # Elbow biomechanics
    elbow_angle = metrics.get('elbow_angle', 0)
    if 85 <= elbow_angle <= 95:
        insights.append("Your 90° elbow angle maximizes force transfer through the kinetic chain, from legs to fingertips.")
    elif elbow_angle < 85:
        insights.append("A closed elbow angle reduces power transfer and can lead to inconsistent release points.")
    else:
        insights.append("An open elbow angle reduces accuracy and makes the shot harder to control.")
    
    # Release biomechanics
    release_angle = metrics.get('release_angle', 0)
    if 45 <= release_angle <= 50:
        insights.append("Your release angle creates optimal trajectory for consistent shooting and soft rim contact.")
    elif release_angle < 45:
        insights.append("A low release angle creates a flat trajectory that's harder to control and less forgiving.")
    else:
        insights.append("A high release angle reduces accuracy and makes the shot harder to control.")
    
    # Advanced metrics insights
    if advanced_metrics:
        consistency = advanced_metrics.get('consistency_score', 0)
        if consistency >= 85:
            insights.append("Your consistent form reduces variability and improves shooting accuracy.")
        elif consistency < 70:
            insights.append("Inconsistent form increases shot variability and reduces accuracy.")
        
        follow_through = advanced_metrics.get('follow_through_angle', 0)
        if follow_through >= 85:
            insights.append("Your consistent follow-through ensures proper wrist snap and shot direction.")
        elif follow_through < 70:
            insights.append("Inconsistent follow-through can lead to poor shot direction and reduced accuracy.")
    
    return insights

def _generate_injury_prevention_tips(metrics, advanced_metrics):
    """Generate injury prevention tips"""
    prevention_tips = []
    
    # Elbow injury prevention
    elbow_angle = metrics.get('elbow_angle', 0)
    if elbow_angle < 80 or elbow_angle > 100:
        prevention_tips.append("Improper elbow angle can lead to elbow strain and tendonitis. Focus on 90° angle.")
    
    # Knee injury prevention
    knee_angle = metrics.get('knee_angle', 0)
    if knee_angle < 100:
        prevention_tips.append("Excessive knee bend can strain the knees. Aim for 120-140° knee angle.")
    
    # Body alignment injury prevention
    body_alignment = metrics.get('body_alignment', 0)
    if body_alignment < 70:
        prevention_tips.append("Poor body alignment can lead to back strain. Keep shoulders and hips aligned.")
    
    # Advanced metrics injury prevention
    if advanced_metrics:
        body_sway = advanced_metrics.get('body_sway', 0)
        if body_sway < 70:
            prevention_tips.append("Excessive body sway can lead to ankle and knee injuries. Focus on stability.")
        
        jump_timing = advanced_metrics.get('jump_timing', 0)
        if jump_timing < 60:
            prevention_tips.append("Poor jump timing can lead to knee and ankle injuries. Coordinate leg drive with release.")
    
    return prevention_tips

def _generate_drill_recommendations(metrics, advanced_metrics):
    """Generate specific drill recommendations"""
    drills = []
    
    # Basic drills based on metrics
    elbow_angle = metrics.get('elbow_angle', 0)
    if elbow_angle < 85 or elbow_angle > 95:
        drills.append({
            'name': 'Wall Touch Drill',
            'description': 'Stand 2 feet from wall, touch wall with fingertips at 90° angle',
            'sets': '3 sets of 20 touches',
            'focus': 'Elbow angle consistency'
        })
    
    release_angle = metrics.get('release_angle', 0)
    if release_angle < 40 or release_angle > 60:
        drills.append({
            'name': 'Arc Shooting Drill',
            'description': 'Practice shooting with high arc, aim for back of rim',
            'sets': '3 sets of 15 shots from 10 feet',
            'focus': 'Release angle and trajectory'
        })
    
    # Advanced drills based on advanced metrics
    if advanced_metrics:
        consistency = advanced_metrics.get('consistency_score', 0)
        if consistency < 80:
            drills.append({
                'name': 'Repetition Drill',
                'description': 'Practice same shooting motion repeatedly',
                'sets': '3 sets of 20 shots',
                'focus': 'Form consistency'
            })
        
        follow_through = advanced_metrics.get('follow_through_angle', 0)
        if follow_through < 80:
            drills.append({
                'name': 'Wrist Snap Drill',
                'description': 'Practice snapping wrist down on follow-through',
                'sets': '3 sets of 20 snaps',
                'focus': 'Follow-through consistency'
            })
    
    return drills

def _prioritize_tips(tips, confidence_scores):
    """Prioritize tips based on importance and confidence"""
    try:
        if not tips:
            return []
        
        # Sort tips by priority and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        def tip_priority(tip):
            priority_score = priority_order.get(tip.get('priority', 'low'), 1)
            confidence = tip.get('confidence', 50)
            return (priority_score, confidence)
        
        sorted_tips = sorted(tips, key=tip_priority, reverse=True)
        return sorted_tips[:3]  # Top 3 priority tips
        
    except Exception as e:
        print(f"Error prioritizing tips: {e}")
        return tips[:3]

def calculate_scores(metrics):
    """
    Calculate component scores (0-25 each) based on RESEARCH-BASED metrics
    
    Based on peer-reviewed biomechanics research:
    - Elbow at RELEASE: 160-170° (not 90°!)
    - Knee at RELEASE: 160-175° (nearly straight, not bent!)
    - Release trajectory: 48-55°
    
    Args:
        metrics: Dictionary containing angle measurements
        
    Returns:
        dict: Component scores and total score
    """
    try:
        elbow_angle = metrics.get('elbow_angle', 0)
        knee_angle = metrics.get('knee_angle', 0)
        release_angle = metrics.get('release_angle', 0)
        body_alignment = metrics.get('body_alignment', 0)
        
        # RESEARCH-BASED SCORING (corrected!)
        
        # Elbow score (RESEARCH: 160-170° at release, NOT 90°!)
        # If measuring at release phase
        if elbow_angle > 120:  # Likely measured at release
            ideal_elbow = 165.0  # Research: 160-170° at release
            elbow_deviation = abs(elbow_angle - ideal_elbow)
            if elbow_deviation <= 10:  # Within 160-175° (excellent)
                elbow_score = 25
            elif elbow_deviation <= 20:  # Within 145-185° (good)
                elbow_score = 20
            elif elbow_deviation <= 30:  # Within 135-195° (fair)
                elbow_score = 15
            else:
                elbow_score = max(0, 25 - (elbow_deviation * 0.5))
        else:  # Likely measured during cocking (67-95°)
            # Lower expectations for cocking phase
            ideal_elbow = 90.0  # 85-95° during cocking
            elbow_deviation = abs(elbow_angle - ideal_elbow)
            if elbow_deviation <= 5:  # 85-95° (excellent)
                elbow_score = 20  # Max 20 if measured at wrong phase
            elif elbow_deviation <= 15:  # 75-105° (good)
                elbow_score = 15
            elif elbow_deviation <= 25:  # 65-115° (fair)
                elbow_score = 10
            else:
                elbow_score = max(0, 20 - (elbow_deviation * 0.5))
        
        # Knee score (RESEARCH: 160-175° at release, NOT 130°!)
        # Almost straight legs at release is CORRECT!
        ideal_knee = 167.5  # Research: 160-175° at release
        knee_deviation = abs(knee_angle - ideal_knee)
        if knee_deviation <= 7.5:  # Within 160-175° (perfect!)
            balance_score = 25
        elif knee_deviation <= 15:  # Within 152.5-182.5° (excellent)
            balance_score = 23
        elif knee_deviation <= 25:  # Within 142.5-192.5° (good)
            balance_score = 20
        elif knee_deviation <= 40:  # Within 127.5-207.5° (fair)
            balance_score = 15
        else:
            balance_score = max(0, 25 - (knee_deviation * 0.3))
        
        # Release score (RESEARCH: 48-55° - this was mostly correct!)
        ideal_release = 51.5  # Research: 48-55° launch angle
        release_deviation = abs(release_angle - ideal_release)
        if release_deviation <= 5:  # Within 46.5-56.5° (excellent)
            release_score = 25
        elif release_deviation <= 8:  # Within 43.5-59.5° (good)
            release_score = 22
        elif release_deviation <= 12:  # Within 39.5-63.5° (fair)
            release_score = 18
        elif release_deviation <= 18:  # Within 33.5-69.5° (poor)
            release_score = 12
        else:
            release_score = max(0, 25 - (release_deviation * 0.8))
        
        # Alignment score (0-100 scale to 0-25)
        alignment_score = (body_alignment / 100) * 25
        
        # Calculate total score
        total_score = elbow_score + balance_score + release_score + alignment_score
        
        return {
            'elbow': round(elbow_score, 2),
            'balance': round(balance_score, 2),
            'release': round(release_score, 2),
            'alignment': round(alignment_score, 2),
            'total': round(total_score, 2)
        }
        
    except Exception as e:
        print(f"Error calculating scores: {e}")
        return {
            'elbow': 0,
            'balance': 0,
            'release': 0,
            'alignment': 0,
            'total': 0
        }

def get_performance_level(total_score):
    """
    Get performance level based on total score
    
    Args:
        total_score: Total score out of 100
        
    Returns:
        str: Performance level description
    """
    try:
        if total_score >= 90:
            return "Excellent"
        elif total_score >= 80:
            return "Great"
        elif total_score >= 70:
            return "Good"
        elif total_score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"
    except Exception as e:
        print(f"Error getting performance level: {e}")
        return "Unknown"