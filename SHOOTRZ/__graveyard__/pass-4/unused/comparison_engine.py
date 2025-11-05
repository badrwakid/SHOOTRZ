"""
Intelligent Professional Player Comparison Engine

Analyzes user's shooting form and matches them with similar professional players,
generating personalized improvement paths and detailed comparisons.
"""

import numpy as np
from professional_benchmarks import PROFESSIONAL_PLAYERS

class ComparisonEngine:
    def __init__(self):
        """Initialize comparison engine"""
        self.players = PROFESSIONAL_PLAYERS
        self.metric_weights = {
            'elbow_angle': 0.25,
            'release_angle': 0.20,
            'knee_angle': 0.15,
            'body_alignment': 0.10,
            'follow_through': 0.10,
            'consistency': 0.10,
            'jump_timing': 0.05,
            'body_sway': 0.05
        }
    
    def find_best_matches(self, user_metrics, user_height=None, position_preference=None):
        """
        Find the best professional player matches for the user
        
        Args:
            user_metrics: User's shooting metrics
            user_height: User's height in feet (optional)
            position_preference: Preferred position ('guard', 'forward', 'center')
            
        Returns:
            dict: Comparison results with top matches and improvement path
        """
        try:
            # Calculate similarity scores for all players
            similarities = []
            
            for player_key, player_data in self.players.items():
                similarity = self._calculate_similarity(user_metrics, player_data['benchmarks'])
                
                # Apply height-based adjustment if provided
                if user_height and 'height' in player_data:
                    height_adjustment = self._calculate_height_adjustment(user_height, player_data['height'])
                    similarity *= height_adjustment
                
                # Apply position preference if provided
                if position_preference and player_data['position'].lower() in position_preference.lower():
                    similarity *= 1.1  # 10% bonus for preferred position
                
                similarities.append({
                    'player_key': player_key,
                    'player_data': player_data,
                    'similarity': similarity,
                    'key_differences': self._identify_key_differences(user_metrics, player_data['benchmarks'])
                })
            
            # Sort by similarity score
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Get top 3 matches
            top_matches = similarities[:3]
            
            # Generate improvement path based on best match
            best_match = top_matches[0] if top_matches else None
            improvement_path = self._generate_improvement_path(user_metrics, best_match) if best_match else []
            
            return {
                'best_match': {
                    'name': best_match['player_data']['name'],
                    'similarity': round(best_match['similarity'], 1),
                    'position': best_match['player_data']['position'],
                    'style': best_match['player_data']['style'],
                    'best_for': best_match['player_data']['best_for'],
                    'key_differences': best_match['key_differences']
                },
                'top_matches': [
                    {
                        'name': match['player_data']['name'],
                        'similarity': round(match['similarity'], 1),
                        'position': match['player_data']['position'],
                        'style': match['player_data']['style'],
                        'key_differences': match['key_differences']
                    }
                    for match in top_matches
                ],
                'improvement_path': improvement_path,
                'overall_similarity': round(np.mean([m['similarity'] for m in top_matches]), 1) if top_matches else 0
            }
            
        except Exception as e:
            print(f"Error finding best matches: {e}")
            return self._get_default_comparison()
    
    def _calculate_similarity(self, user_metrics, player_benchmarks):
        """Calculate similarity score between user and professional player"""
        try:
            total_similarity = 0.0
            total_weight = 0.0
            
            for metric, weight in self.metric_weights.items():
                if metric in user_metrics and metric in player_benchmarks:
                    user_value = user_metrics[metric]
                    player_value = player_benchmarks[metric]
                    
                    # Calculate similarity for this metric
                    metric_similarity = self._calculate_metric_similarity(user_value, player_value, metric)
                    
                    total_similarity += metric_similarity * weight
                    total_weight += weight
            
            # Normalize by total weight
            if total_weight > 0:
                return (total_similarity / total_weight) * 100
            else:
                return 0.0
                
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def _calculate_metric_similarity(self, user_value, player_value, metric):
        """Calculate similarity for a specific metric"""
        try:
            if user_value == 0 or player_value == 0:
                return 0.0
            
            # Calculate percentage difference
            difference = abs(user_value - player_value)
            
            # Define tolerance ranges for each metric
            tolerances = {
                'elbow_angle': 10.0,      # ±10° tolerance
                'release_angle': 5.0,     # ±5° tolerance
                'knee_angle': 15.0,       # ±15° tolerance
                'body_alignment': 20.0,   # ±20% tolerance
                'follow_through': 15.0,   # ±15% tolerance
                'consistency': 10.0,      # ±10% tolerance
                'jump_timing': 20.0,      # ±20% tolerance
                'body_sway': 15.0         # ±15% tolerance
            }
            
            tolerance = tolerances.get(metric, 10.0)
            
            # Calculate similarity (0-100%)
            if difference <= tolerance:
                # Within tolerance - high similarity
                similarity = 100 - (difference / tolerance * 50)  # 50-100% range
            else:
                # Outside tolerance - lower similarity
                excess = difference - tolerance
                similarity = max(0, 50 - (excess / tolerance * 50))  # 0-50% range
            
            return max(0, min(100, similarity))
            
        except Exception as e:
            print(f"Error calculating metric similarity: {e}")
            return 0.0
    
    def _calculate_height_adjustment(self, user_height, player_height):
        """Calculate height-based adjustment factor"""
        try:
            height_diff = abs(user_height - player_height)
            
            # Height difference adjustment (closer height = higher similarity)
            if height_diff <= 0.5:  # Within 6 inches
                return 1.0
            elif height_diff <= 1.0:  # Within 1 foot
                return 0.95
            elif height_diff <= 1.5:  # Within 1.5 feet
                return 0.90
            elif height_diff <= 2.0:  # Within 2 feet
                return 0.85
            else:  # More than 2 feet difference
                return 0.80
                
        except Exception as e:
            print(f"Error calculating height adjustment: {e}")
            return 1.0
    
    def _identify_key_differences(self, user_metrics, player_benchmarks):
        """Identify the most significant differences between user and player"""
        try:
            differences = []
            
            for metric in self.metric_weights.keys():
                if metric in user_metrics and metric in player_benchmarks:
                    user_value = user_metrics[metric]
                    player_value = player_benchmarks[metric]
                    difference = abs(user_value - player_value)
                    
                    # Only include significant differences
                    if difference > 5:  # Threshold for significant difference
                        differences.append({
                            'metric': metric,
                            'user_value': user_value,
                            'player_value': player_value,
                            'difference': difference,
                            'improvement_direction': self._get_improvement_direction(user_value, player_value, metric)
                        })
            
            # Sort by difference magnitude
            differences.sort(key=lambda x: x['difference'], reverse=True)
            
            # Return top 3 differences
            return differences[:3]
            
        except Exception as e:
            print(f"Error identifying key differences: {e}")
            return []
    
    def _get_improvement_direction(self, user_value, player_value, metric):
        """Get improvement direction for a metric"""
        try:
            if user_value < player_value:
                return "increase"
            elif user_value > player_value:
                return "decrease"
            else:
                return "maintain"
        except:
            return "maintain"
    
    def _generate_improvement_path(self, user_metrics, best_match):
        """Generate step-by-step improvement path"""
        try:
            if not best_match:
                return []
            
            player_benchmarks = best_match['player_data']['benchmarks']
            key_differences = best_match['key_differences']
            
            improvement_steps = []
            
            for i, diff in enumerate(key_differences[:3]):  # Top 3 improvements
                metric = diff['metric']
                current = diff['user_value']
                target = diff['player_value']
                direction = diff['improvement_direction']
                
                # Calculate impact score
                impact = self._calculate_improvement_impact(metric, current, target)
                
                # Generate drill recommendation
                drill = self._get_drill_recommendation(metric, direction)
                
                improvement_steps.append({
                    'step': i + 1,
                    'metric': self._format_metric_name(metric),
                    'current': round(current, 1),
                    'target': round(target, 1),
                    'direction': direction,
                    'impact': f"+{impact}% similarity to {best_match['player_data']['name']}",
                    'drill': drill,
                    'priority': 'high' if i == 0 else 'medium' if i == 1 else 'low'
                })
            
            return improvement_steps
            
        except Exception as e:
            print(f"Error generating improvement path: {e}")
            return []
    
    def _calculate_improvement_impact(self, metric, current, target):
        """Calculate the impact of improving a metric"""
        try:
            # Calculate potential similarity improvement
            current_diff = abs(current - target)
            if current_diff > 0:
                # Estimate improvement in similarity score
                improvement = min(15, current_diff * 0.5)  # Cap at 15% improvement
                return round(improvement, 1)
            return 0.0
        except:
            return 0.0
    
    def _get_drill_recommendation(self, metric, direction):
        """Get specific drill recommendation for a metric"""
        try:
            drill_database = {
                'elbow_angle': {
                    'increase': "Wall touch drill - 3 sets of 20 touches, focus on 90° angle",
                    'decrease': "Close-range shooting - 3 sets of 15 shots, emphasize elbow position",
                    'maintain': "Form shooting - 3 sets of 10 shots, maintain current elbow angle"
                },
                'release_angle': {
                    'increase': "High arc shooting - 3 sets of 15 shots, aim for higher trajectory",
                    'decrease': "Flat shot correction - 3 sets of 15 shots, focus on 45-50° release",
                    'maintain': "Consistent release practice - 3 sets of 10 shots"
                },
                'knee_angle': {
                    'increase': "Squat hold drill - 3 sets of 30 seconds, build leg strength",
                    'decrease': "Shallow knee bend practice - 3 sets of 15 shots",
                    'maintain': "Power shooting - 3 sets of 10 shots, maintain knee bend"
                },
                'body_alignment': {
                    'increase': "Square up drill - 3 sets of 20 shots, focus on shoulder alignment",
                    'decrease': "Alignment correction - 3 sets of 15 shots, check shoulder position",
                    'maintain': "Balance practice - 3 sets of 10 shots, maintain alignment"
                },
                'follow_through': {
                    'increase': "Wrist snap drill - 3 sets of 20 snaps, emphasize follow-through",
                    'decrease': "Controlled release - 3 sets of 15 shots, reduce excessive snap",
                    'maintain': "Consistent follow-through - 3 sets of 10 shots"
                },
                'consistency': {
                    'increase': "Repetition drill - 3 sets of 20 shots, same motion every time",
                    'decrease': "Variation practice - 3 sets of 15 shots, controlled changes",
                    'maintain': "Form consistency - 3 sets of 10 shots, maintain current form"
                },
                'jump_timing': {
                    'increase': "Jump shot timing - 3 sets of 15 shots, coordinate legs and arms",
                    'decrease': "Timing adjustment - 3 sets of 15 shots, modify jump timing",
                    'maintain': "Power transfer practice - 3 sets of 10 shots, maintain timing"
                },
                'body_sway': {
                    'increase': "Balance drill - 3 sets of 20 shots, focus on stability",
                    'decrease': "Stability practice - 3 sets of 15 shots, reduce lateral movement",
                    'maintain': "Balance maintenance - 3 sets of 10 shots, keep current stability"
                }
            }
            
            return drill_database.get(metric, {}).get(direction, "Practice this metric with focused repetition")
            
        except Exception as e:
            print(f"Error getting drill recommendation: {e}")
            return "Practice this metric with focused repetition"
    
    def _format_metric_name(self, metric):
        """Format metric name for display"""
        try:
            name_mapping = {
                'elbow_angle': 'Elbow Angle',
                'release_angle': 'Release Angle',
                'knee_angle': 'Knee Angle',
                'body_alignment': 'Body Alignment',
                'follow_through': 'Follow-Through',
                'consistency': 'Shot Consistency',
                'jump_timing': 'Jump Timing',
                'body_sway': 'Body Stability'
            }
            return name_mapping.get(metric, metric.replace('_', ' ').title())
        except:
            return metric.replace('_', ' ').title()
    
    def get_player_analysis(self, player_key):
        """Get detailed analysis of a specific professional player"""
        try:
            if player_key not in self.players:
                return None
            
            player = self.players[player_key]
            
            return {
                'name': player['name'],
                'position': player['position'],
                'height': player.get('height', 'Unknown'),
                'style': player['style'],
                'best_for': player['best_for'],
                'ft_percentage': player.get('ft_percentage', 0),
                'career_3p': player.get('career_3p', 0),
                'benchmarks': player['benchmarks'],
                'analysis': self._generate_player_analysis(player)
            }
            
        except Exception as e:
            print(f"Error getting player analysis: {e}")
            return None
    
    def _generate_player_analysis(self, player):
        """Generate detailed analysis of a player's shooting style"""
        try:
            benchmarks = player['benchmarks']
            analysis = []
            
            # Analyze strengths
            strengths = []
            if benchmarks.get('elbow_angle', 0) >= 90:
                strengths.append("Excellent elbow positioning")
            if benchmarks.get('consistency', 0) >= 95:
                strengths.append("Exceptional consistency")
            if benchmarks.get('body_alignment', 0) >= 95:
                strengths.append("Perfect body alignment")
            if benchmarks.get('follow_through', 0) >= 90:
                strengths.append("Strong follow-through")
            
            if strengths:
                analysis.append(f"Key Strengths: {', '.join(strengths)}")
            
            # Analyze style characteristics
            style_notes = []
            if benchmarks.get('release_angle', 0) >= 48:
                style_notes.append("High-arc shooter")
            if benchmarks.get('knee_angle', 0) >= 135:
                style_notes.append("Power-based shot")
            if benchmarks.get('jump_timing', 0) >= 90:
                style_notes.append("Excellent power transfer")
            
            if style_notes:
                analysis.append(f"Style: {', '.join(style_notes)}")
            
            # Add career context
            if player.get('ft_percentage', 0) >= 90:
                analysis.append("Elite free-throw shooter")
            if player.get('career_3p', 0) >= 40:
                analysis.append("Elite three-point shooter")
            
            return analysis if analysis else ["Fundamentally sound shooting form"]
            
        except Exception as e:
            print(f"Error generating player analysis: {e}")
            return ["Professional shooting form"]
    
    def _get_default_comparison(self):
        """Get default comparison when analysis fails"""
        return {
            'best_match': {
                'name': 'Stephen Curry',
                'similarity': 50.0,
                'position': 'Point Guard',
                'style': 'Quick release, high arc',
                'best_for': 'Quick release, long range shooting',
                'key_differences': []
            },
            'top_matches': [],
            'improvement_path': [],
            'overall_similarity': 50.0
        }


