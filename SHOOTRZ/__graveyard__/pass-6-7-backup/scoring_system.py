"""
Enhanced Scoring System for Basketball Shooting Analysis

Implements advanced scoring with:
- Weighted metrics by importance
- Position-specific scoring (guards vs forwards)
- Consistency bonus scoring
- Professional comparison scoring
- Predicted shot success probability
"""

import numpy as np

class EnhancedScoringSystem:
    def __init__(self):
        """Initialize enhanced scoring system"""
        # Metric weights based on basketball research
        self.metric_weights = {
            'elbow_angle': 0.25,      # Most important for accuracy
            'release_angle': 0.20,     # Critical for trajectory
            'knee_angle': 0.15,       # Important for power
            'body_alignment': 0.10,    # Important for balance
            'follow_through': 0.10,   # Important for consistency
            'consistency': 0.10,      # Overall form stability
            'jump_timing': 0.05,      # Power transfer
            'body_sway': 0.05         # Stability
        }
        
        # Position-specific adjustments
        self.position_adjustments = {
            'guard': {
                'elbow_angle': 1.0,      # Standard weight
                'release_angle': 1.1,    # Guards need higher arc
                'knee_angle': 0.9,       # Less emphasis on power
                'body_alignment': 1.0,
                'follow_through': 1.1,   # More emphasis on quick release
                'consistency': 1.0,
                'jump_timing': 0.9,
                'body_sway': 1.0
            },
            'forward': {
                'elbow_angle': 1.0,
                'release_angle': 0.9,    # Forwards can use lower arc
                'knee_angle': 1.1,       # More emphasis on power
                'body_alignment': 1.0,
                'follow_through': 0.9,   # Less emphasis on quick release
                'consistency': 1.0,
                'jump_timing': 1.1,      # More emphasis on power transfer
                'body_sway': 1.0
            },
            'center': {
                'elbow_angle': 1.0,
                'release_angle': 0.8,    # Centers can use even lower arc
                'knee_angle': 1.2,       # Maximum emphasis on power
                'body_alignment': 1.1,   # More emphasis on stability
                'follow_through': 0.8,
                'consistency': 1.0,
                'jump_timing': 1.2,      # Maximum emphasis on power transfer
                'body_sway': 1.1         # More emphasis on stability
            }
        }
        
        # Ideal values for each metric
        self.ideal_values = {
            'elbow_angle': 90.0,
            'release_angle': 47.5,
            'knee_angle': 130.0,
            'body_alignment': 100.0,
            'follow_through': 85.0,
            'consistency': 90.0,
            'jump_timing': 80.0,
            'body_sway': 85.0
        }
        
        # Tolerance ranges for each metric
        self.tolerance_ranges = {
            'elbow_angle': 10.0,      # ±10° from ideal
            'release_angle': 5.0,     # ±5° from ideal
            'knee_angle': 15.0,       # ±15° from ideal
            'body_alignment': 20.0,   # ±20% from ideal
            'follow_through': 15.0,  # ±15% from ideal
            'consistency': 10.0,      # ±10% from ideal
            'jump_timing': 20.0,      # ±20% from ideal
            'body_sway': 15.0         # ±15% from ideal
        }
    
    def calculate_enhanced_scores(self, basic_metrics, advanced_metrics, confidence_scores, position='guard'):
        """
        Calculate enhanced scores with weighted metrics and position adjustments
        
        Args:
            basic_metrics: Basic angle metrics
            advanced_metrics: Advanced metrics
            confidence_scores: Confidence scores for each metric
            position: Player position ('guard', 'forward', 'center')
            
        Returns:
            dict: Enhanced scores with explanations
        """
        try:
            # Combine all metrics
            all_metrics = {
                'elbow_angle': basic_metrics.get('elbow_angle', 0),
                'release_angle': basic_metrics.get('release_angle', 0),
                'knee_angle': basic_metrics.get('knee_angle', 0),
                'body_alignment': basic_metrics.get('body_alignment', 0),
                'follow_through': advanced_metrics.get('follow_through_angle', 0),
                'consistency': advanced_metrics.get('consistency_score', 0),
                'jump_timing': advanced_metrics.get('jump_timing', 0),
                'body_sway': advanced_metrics.get('body_sway', 0)
            }
            
            # Calculate individual scores
            individual_scores = {}
            weighted_scores = {}
            
            for metric, value in all_metrics.items():
                # Calculate base score
                base_score = self._calculate_metric_score(metric, value)
                
                # Apply confidence weighting
                confidence = confidence_scores.get(f'{metric}_confidence', 50.0)
                confidence_weighted_score = base_score * (confidence / 100.0)
                
                # Apply position adjustment
                position_multiplier = self.position_adjustments.get(position, {}).get(metric, 1.0)
                final_score = confidence_weighted_score * position_multiplier
                
                individual_scores[metric] = round(base_score, 1)
                weighted_scores[metric] = round(final_score, 1)
            
            # Calculate weighted total score
            total_score = sum(weighted_scores[metric] * self.metric_weights[metric] 
                            for metric in self.metric_weights.keys())
            
            # Apply consistency bonus
            consistency_bonus = self._calculate_consistency_bonus(all_metrics)
            total_score += consistency_bonus
            
            # Calculate predicted make rate
            predicted_make_rate = self._calculate_predicted_make_rate(all_metrics, total_score)
            
            # Generate score explanations
            explanations = self._generate_score_explanations(individual_scores, weighted_scores)
            
            return {
                'individual_scores': individual_scores,
                'weighted_scores': weighted_scores,
                'total_score': round(total_score, 1),
                'consistency_bonus': round(consistency_bonus, 1),
                'predicted_make_rate': round(predicted_make_rate, 1),
                'position_adjustments': self.position_adjustments.get(position, {}),
                'explanations': explanations,
                'grade': self._calculate_grade(total_score)
            }
            
        except Exception as e:
            print(f"Error calculating enhanced scores: {e}")
            return self._get_default_scores()
    
    def _calculate_metric_score(self, metric, value):
        """Calculate score for a single metric (0-100)"""
        try:
            if value == 0:
                return 0.0
            
            ideal = self.ideal_values[metric]
            tolerance = self.tolerance_ranges[metric]
            
            # Calculate deviation from ideal
            deviation = abs(value - ideal)
            
            # Calculate score based on tolerance
            if deviation <= tolerance:
                # Within tolerance - calculate proportional score
                score = 100 - (deviation / tolerance * 50)  # 50-100 range
            else:
                # Outside tolerance - calculate penalty score
                excess = deviation - tolerance
                score = max(0, 50 - (excess / tolerance * 50))  # 0-50 range
            
            return max(0, min(100, score))
            
        except Exception as e:
            print(f"Error calculating metric score for {metric}: {e}")
            return 0.0
    
    def _calculate_consistency_bonus(self, metrics):
        """Calculate consistency bonus based on metric stability"""
        try:
            # This would typically use frame-by-frame variance data
            # For now, we'll use the consistency score directly
            consistency_score = metrics.get('consistency', 0)
            
            # Bonus scales with consistency (0-10 points)
            if consistency_score >= 90:
                bonus = 10.0
            elif consistency_score >= 80:
                bonus = 7.5
            elif consistency_score >= 70:
                bonus = 5.0
            elif consistency_score >= 60:
                bonus = 2.5
            else:
                bonus = 0.0
            
            return bonus
            
        except Exception as e:
            print(f"Error calculating consistency bonus: {e}")
            return 0.0
    
    def _calculate_predicted_make_rate(self, metrics, total_score):
        """Calculate predicted shot success rate based on form"""
        try:
            # Base make rate from total score
            base_rate = total_score * 0.8  # Scale score to 0-80%
            
            # Adjustments based on specific metrics
            adjustments = 0.0
            
            # Elbow angle adjustment (most important)
            elbow_angle = metrics.get('elbow_angle', 0)
            if 85 <= elbow_angle <= 95:
                adjustments += 5.0  # Perfect elbow angle
            elif 80 <= elbow_angle <= 100:
                adjustments += 2.5  # Good elbow angle
            
            # Release angle adjustment
            release_angle = metrics.get('release_angle', 0)
            if 45 <= release_angle <= 50:
                adjustments += 3.0  # Perfect release angle
            elif 42 <= release_angle <= 53:
                adjustments += 1.5  # Good release angle
            
            # Consistency adjustment
            consistency = metrics.get('consistency', 0)
            if consistency >= 85:
                adjustments += 2.0  # High consistency bonus
            
            # Body alignment adjustment
            body_alignment = metrics.get('body_alignment', 0)
            if body_alignment >= 90:
                adjustments += 1.5  # Excellent alignment
            
            # Calculate final predicted rate
            predicted_rate = base_rate + adjustments
            
            # Cap at realistic maximum (95%)
            return min(95.0, max(0.0, predicted_rate))
            
        except Exception as e:
            print(f"Error calculating predicted make rate: {e}")
            return 50.0  # Default 50% make rate
    
    def _generate_score_explanations(self, individual_scores, weighted_scores):
        """Generate explanations for scores"""
        try:
            explanations = {}
            
            for metric in individual_scores.keys():
                base_score = individual_scores[metric]
                weighted_score = weighted_scores[metric]
                
                # Determine performance level
                if base_score >= 90:
                    level = "Excellent"
                    color = "green"
                elif base_score >= 80:
                    level = "Good"
                    color = "blue"
                elif base_score >= 70:
                    level = "Fair"
                    color = "yellow"
                elif base_score >= 60:
                    level = "Needs Improvement"
                    color = "orange"
                else:
                    level = "Poor"
                    color = "red"
                
                # Generate specific feedback
                feedback = self._generate_metric_feedback(metric, base_score)
                
                explanations[metric] = {
                    'base_score': base_score,
                    'weighted_score': weighted_score,
                    'level': level,
                    'color': color,
                    'feedback': feedback
                }
            
            return explanations
            
        except Exception as e:
            print(f"Error generating score explanations: {e}")
            return {}
    
    def _generate_metric_feedback(self, metric, score):
        """Generate specific feedback for a metric"""
        try:
            feedback_templates = {
                'elbow_angle': {
                    'excellent': "Perfect 90° elbow angle! This maximizes accuracy and power transfer.",
                    'good': "Good elbow angle. Slight adjustments could improve consistency.",
                    'fair': "Elbow angle needs work. Focus on keeping your elbow at 90° during release.",
                    'poor': "Elbow angle is significantly off. Practice with wall touches to develop muscle memory."
                },
                'release_angle': {
                    'excellent': "Excellent release angle! This creates the perfect shot arc.",
                    'good': "Good release angle. Minor tweaks could improve trajectory.",
                    'fair': "Release angle needs adjustment. Aim for 45-50° for optimal arc.",
                    'poor': "Release angle is too flat or too steep. Practice with higher arc."
                },
                'knee_angle': {
                    'excellent': "Perfect knee bend! This generates excellent power for your shot.",
                    'good': "Good knee bend. Consistent form will improve power transfer.",
                    'fair': "Knee bend needs work. Bend knees more to generate power.",
                    'poor': "Insufficient knee bend. Focus on using your legs for power."
                },
                'body_alignment': {
                    'excellent': "Perfect body alignment! Your shoulders and hips are perfectly aligned.",
                    'good': "Good body alignment. Minor adjustments will improve balance.",
                    'fair': "Body alignment needs work. Keep shoulders square to the basket.",
                    'poor': "Poor body alignment. Focus on squaring your shoulders to the basket."
                },
                'follow_through': {
                    'excellent': "Excellent follow-through! Your wrist snap is consistent and powerful.",
                    'good': "Good follow-through. Keep working on wrist snap consistency.",
                    'fair': "Follow-through needs improvement. Focus on snapping your wrist down.",
                    'poor': "Follow-through is inconsistent. Practice wrist snap drills."
                },
                'consistency': {
                    'excellent': "Excellent consistency! Your form is very stable throughout the shot.",
                    'good': "Good consistency. Minor variations won't affect your shooting.",
                    'fair': "Consistency needs work. Focus on repeating the same motion.",
                    'poor': "Inconsistent form. Practice the same motion repeatedly."
                },
                'jump_timing': {
                    'excellent': "Perfect jump timing! Your knee extension and release are perfectly coordinated.",
                    'good': "Good jump timing. Slight adjustments could improve power transfer.",
                    'fair': "Jump timing needs work. Coordinate your leg drive with your release.",
                    'poor': "Poor jump timing. Focus on using your legs to power your shot."
                },
                'body_sway': {
                    'excellent': "Excellent stability! No lateral movement during your shot.",
                    'good': "Good stability. Minor sway won't affect your accuracy.",
                    'fair': "Some body sway detected. Focus on staying balanced.",
                    'poor': "Significant body sway. Work on maintaining balance throughout the shot."
                }
            }
            
            # Determine feedback level
            if score >= 90:
                level = 'excellent'
            elif score >= 80:
                level = 'good'
            elif score >= 70:
                level = 'fair'
            else:
                level = 'poor'
            
            return feedback_templates.get(metric, {}).get(level, "Keep practicing to improve this aspect of your shot.")
            
        except Exception as e:
            print(f"Error generating metric feedback: {e}")
            return "Keep practicing to improve this aspect of your shot."
    
    def _calculate_grade(self, total_score):
        """Calculate letter grade based on total score"""
        try:
            if total_score >= 95:
                return "A+"
            elif total_score >= 90:
                return "A"
            elif total_score >= 85:
                return "A-"
            elif total_score >= 80:
                return "B+"
            elif total_score >= 75:
                return "B"
            elif total_score >= 70:
                return "B-"
            elif total_score >= 65:
                return "C+"
            elif total_score >= 60:
                return "C"
            elif total_score >= 55:
                return "C-"
            elif total_score >= 50:
                return "D"
            else:
                return "F"
        except:
            return "F"
    
    def _get_default_scores(self):
        """Get default scores when calculation fails"""
        return {
            'individual_scores': {},
            'weighted_scores': {},
            'total_score': 0.0,
            'consistency_bonus': 0.0,
            'predicted_make_rate': 0.0,
            'position_adjustments': {},
            'explanations': {},
            'grade': 'F'
        }


