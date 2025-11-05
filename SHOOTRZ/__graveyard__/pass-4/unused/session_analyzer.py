"""
Session Analyzer

Analyzes multiple shots in one session to calculate consistency,
identify patterns, and detect form breakdown.
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class SessionAnalyzer:
    def __init__(self):
        """Initialize session analyzer"""
        self.session_shots = []
        self.session_start = None
    
    def start_session(self):
        """Start a new session"""
        self.session_shots = []
        self.session_start = datetime.now()
        print("Session started")
    
    def add_shot(self, analysis: Dict):
        """
        Add a shot to current session
        
        Args:
            analysis: Shot analysis results
        """
        shot_data = {
            'timestamp': datetime.now().isoformat(),
            'shot_number': len(self.session_shots) + 1,
            'analysis': analysis
        }
        
        self.session_shots.append(shot_data)
    
    def analyze_session(self) -> Dict:
        """
        Analyze complete session
        
        Returns:
            Dict with session analysis
        """
        try:
            if not self.session_shots:
                return {
                    'success': False,
                    'message': 'No shots in session'
                }
            
            # Extract metrics from all shots
            all_metrics = self._extract_all_metrics()
            
            # Calculate consistency scores
            consistency = self._calculate_consistency(all_metrics)
            
            # Detect form breakdown patterns
            breakdown = self._detect_form_breakdown(all_metrics)
            
            # Calculate session statistics
            statistics = self._calculate_statistics(all_metrics)
            
            # Generate session insights
            insights = self._generate_insights(consistency, breakdown, statistics)
            
            session_duration = (datetime.now() - self.session_start).total_seconds() / 60 if self.session_start else 0
            
            return {
                'success': True,
                'session_start': self.session_start.isoformat() if self.session_start else None,
                'total_shots': len(self.session_shots),
                'duration_minutes': round(session_duration, 1),
                'consistency_scores': consistency,
                'form_breakdown': breakdown,
                'statistics': statistics,
                'insights': insights,
                'shot_details': self._get_shot_details()
            }
            
        except Exception as e:
            print(f"Error analyzing session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_all_metrics(self) -> Dict:
        """Extract metrics from all shots in session"""
        metrics_by_shot = []
        
        for shot in self.session_shots:
            analysis = shot['analysis']
            metrics = analysis.get('metrics', {})
            scores = analysis.get('scores', {})
            
            combined = {**metrics, **scores}
            metrics_by_shot.append(combined)
        
        # Organize by metric name
        metrics_dict = {}
        for shot_metrics in metrics_by_shot:
            for metric_name, value in shot_metrics.items():
                if isinstance(value, (int, float)):
                    if metric_name not in metrics_dict:
                        metrics_dict[metric_name] = []
                    metrics_dict[metric_name].append(value)
        
        return metrics_dict
    
    def _calculate_consistency(self, all_metrics: Dict) -> Dict:
        """
        Calculate consistency scores for each metric
        
        Args:
            all_metrics: Dict of metric values across shots
            
        Returns:
            Dict of consistency scores
        """
        consistency_scores = {}
        
        for metric_name, values in all_metrics.items():
            if len(values) < 2:
                consistency_scores[metric_name] = 0
                continue
            
            # Calculate coefficient of variation (CV)
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if mean_val != 0:
                cv = std_val / mean_val
                # Convert to 0-100 score (lower CV = higher consistency)
                consistency_score = max(0, 100 - (cv * 100))
            else:
                consistency_score = 0
            
            consistency_scores[metric_name] = round(consistency_score, 1)
        
        # Calculate overall consistency
        if consistency_scores:
            consistency_scores['overall'] = round(np.mean(list(consistency_scores.values())), 1)
        
        return consistency_scores
    
    def _detect_form_breakdown(self, all_metrics: Dict) -> Dict:
        """
        Detect form breakdown patterns (fatigue, loss of focus)
        
        Args:
            all_metrics: Dict of metric values across shots
            
        Returns:
            Dict with breakdown analysis
        """
        breakdown = {
            'detected': False,
            'breakdown_shot': None,
            'affected_metrics': [],
            'severity': 'none'
        }
        
        if len(self.session_shots) < 5:
            return breakdown
        
        # Check each metric for significant decline
        for metric_name, values in all_metrics.items():
            if len(values) < 5:
                continue
            
            # Split into first half and second half
            mid_point = len(values) // 2
            first_half = values[:mid_point]
            second_half = values[mid_point:]
            
            first_avg = np.mean(first_half)
            second_avg = np.mean(second_half)
            
            # Check for significant decline (> 10%)
            if first_avg > 0:
                decline_percent = ((first_avg - second_avg) / first_avg) * 100
                
                if decline_percent > 10:
                    breakdown['detected'] = True
                    breakdown['affected_metrics'].append({
                        'metric': metric_name,
                        'decline_percent': round(decline_percent, 1),
                        'first_half_avg': round(first_avg, 2),
                        'second_half_avg': round(second_avg, 2)
                    })
        
        # Determine severity
        if breakdown['detected']:
            affected_count = len(breakdown['affected_metrics'])
            if affected_count >= 3:
                breakdown['severity'] = 'high'
            elif affected_count >= 2:
                breakdown['severity'] = 'moderate'
            else:
                breakdown['severity'] = 'low'
            
            # Find approximate breakdown shot
            # (where metrics start declining consistently)
            breakdown['breakdown_shot'] = mid_point + 1
        
        return breakdown
    
    def _calculate_statistics(self, all_metrics: Dict) -> Dict:
        """
        Calculate session statistics
        
        Args:
            all_metrics: Dict of metric values
            
        Returns:
            Dict with statistics
        """
        statistics = {}
        
        for metric_name, values in all_metrics.items():
            if not values:
                continue
            
            statistics[metric_name] = {
                'mean': round(np.mean(values), 2),
                'median': round(np.median(values), 2),
                'std': round(np.std(values), 2),
                'min': round(np.min(values), 2),
                'max': round(np.max(values), 2),
                'range': round(np.max(values) - np.min(values), 2)
            }
        
        return statistics
    
    def _generate_insights(self, consistency: Dict, breakdown: Dict, 
                          statistics: Dict) -> List[str]:
        """
        Generate actionable insights from session
        
        Args:
            consistency: Consistency scores
            breakdown: Breakdown analysis
            statistics: Session statistics
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Consistency insights
        overall_consistency = consistency.get('overall', 0)
        if overall_consistency >= 80:
            insights.append("✓ Excellent shot consistency throughout the session!")
        elif overall_consistency >= 60:
            insights.append("👍 Good consistency - keep working on repeating your form")
        else:
            insights.append("💡 Work on consistency - focus on repeating the same motion each shot")
        
        # Breakdown insights
        if breakdown['detected']:
            severity = breakdown['severity']
            if severity == 'high':
                insights.append(
                    f"⚠️ Significant form breakdown detected after shot {breakdown['breakdown_shot']}. "
                    "Consider shorter practice sessions or rest breaks."
                )
            else:
                insights.append(
                    f"💡 Minor form decline noticed in second half. "
                    "Focus on maintaining form even when fatigued."
                )
            
            # Specific metric advice
            if breakdown['affected_metrics']:
                worst_metric = max(breakdown['affected_metrics'], 
                                 key=lambda x: x['decline_percent'])
                insights.append(
                    f"📉 {worst_metric['metric']} declined most "
                    f"({worst_metric['decline_percent']:.1f}%)"
                )
        else:
            insights.append("✓ No significant form breakdown - good endurance!")
        
        # Volume insights
        shot_count = len(self.session_shots)
        if shot_count < 10:
            insights.append("💪 Good warm-up session. Consider more reps for skill development.")
        elif shot_count > 50:
            insights.append("⚠️ High volume session. Monitor for fatigue in future sessions.")
        else:
            insights.append(f"👍 Good practice volume ({shot_count} shots)")
        
        # Best metric insight
        if statistics:
            # Find metric with lowest variance (most consistent)
            variances = {
                name: stats['std'] / stats['mean'] if stats['mean'] != 0 else 999
                for name, stats in statistics.items()
            }
            
            if variances:
                best_metric = min(variances.keys(), key=lambda k: variances[k])
                insights.append(f"⭐ Your most consistent metric: {best_metric}")
        
        return insights
    
    def _get_shot_details(self) -> List[Dict]:
        """Get summary of each shot in session"""
        details = []
        
        for shot in self.session_shots:
            analysis = shot['analysis']
            
            details.append({
                'shot_number': shot['shot_number'],
                'timestamp': shot['timestamp'],
                'total_score': analysis.get('scores', {}).get('total', 0),
                'elbow_angle': analysis.get('metrics', {}).get('elbow_angle', 0),
                'release_angle': analysis.get('metrics', {}).get('release_angle', 0),
                'prediction': analysis.get('ml_prediction', {}).get('prediction', 'unknown')
            })
        
        return details
    
    def get_best_shot(self) -> Optional[Dict]:
        """
        Get the best shot from session
        
        Returns:
            Best shot data or None
        """
        if not self.session_shots:
            return None
        
        # Find shot with highest total score
        best_shot = max(
            self.session_shots,
            key=lambda s: s['analysis'].get('scores', {}).get('total', 0)
        )
        
        return best_shot
    
    def get_worst_shot(self) -> Optional[Dict]:
        """
        Get the worst shot from session
        
        Returns:
            Worst shot data or None
        """
        if not self.session_shots:
            return None
        
        # Find shot with lowest total score
        worst_shot = min(
            self.session_shots,
            key=lambda s: s['analysis'].get('scores', {}).get('total', 0)
        )
        
        return worst_shot
    
    def end_session(self) -> Dict:
        """
        End session and return complete analysis
        
        Returns:
            Complete session analysis
        """
        analysis = self.analyze_session()
        
        # Reset session
        self.session_shots = []
        self.session_start = None
        
        return analysis

