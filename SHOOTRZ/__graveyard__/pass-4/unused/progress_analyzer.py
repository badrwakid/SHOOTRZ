"""
Progress Analyzer

Compares current shot to previous sessions and generates progress reports.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database.progress_db import ProgressDatabase

class ProgressAnalyzer:
    def __init__(self, db_path='database/progress.db'):
        """
        Initialize progress analyzer
        
        Args:
            db_path: Path to progress database
        """
        self.db = ProgressDatabase(db_path)
    
    def compare_to_previous(self, user_id: int, current_analysis: Dict, 
                           lookback_days: int = 30) -> Dict:
        """
        Compare current analysis to previous sessions
        
        Args:
            user_id: User ID
            current_analysis: Current analysis results
            lookback_days: Number of days to look back
            
        Returns:
            Dict with comparison results
        """
        try:
            # Get historical data
            history = self.db.get_user_history(user_id, limit=100)
            
            if not history:
                return {
                    'success': False,
                    'message': 'No previous data for comparison'
                }
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            recent_history = [
                h for h in history 
                if datetime.fromisoformat(h['timestamp']) >= cutoff_date
            ]
            
            if not recent_history:
                return {
                    'success': False,
                    'message': f'No data in last {lookback_days} days'
                }
            
            # Extract metrics
            current_metrics = current_analysis.get('metrics', {})
            current_scores = current_analysis.get('scores', {})
            current_combined = {**current_metrics, **current_scores}
            
            # Calculate historical averages
            historical_averages = self._calculate_averages(recent_history)
            
            # Compare metrics
            comparisons = {}
            improvements = []
            regressions = []
            
            for metric_name, current_value in current_combined.items():
                if not isinstance(current_value, (int, float)):
                    continue
                
                historical_value = historical_averages.get(metric_name)
                
                if historical_value is not None:
                    difference = current_value - historical_value
                    percent_change = (difference / historical_value * 100) if historical_value != 0 else 0
                    
                    comparisons[metric_name] = {
                        'current': round(current_value, 2),
                        'historical_avg': round(historical_value, 2),
                        'difference': round(difference, 2),
                        'percent_change': round(percent_change, 1),
                        'trend': 'improving' if difference > 0 else 'declining' if difference < 0 else 'stable'
                    }
                    
                    # Track significant changes
                    if abs(percent_change) >= 5:  # 5% threshold
                        change_info = {
                            'metric': metric_name,
                            'change': percent_change
                        }
                        if difference > 0:
                            improvements.append(change_info)
                        else:
                            regressions.append(change_info)
            
            # Sort improvements and regressions
            improvements.sort(key=lambda x: abs(x['change']), reverse=True)
            regressions.sort(key=lambda x: abs(x['change']), reverse=True)
            
            return {
                'success': True,
                'lookback_days': lookback_days,
                'historical_sessions': len(recent_history),
                'comparisons': comparisons,
                'top_improvements': improvements[:5],
                'top_regressions': regressions[:5],
                'overall_trend': self._calculate_overall_trend(comparisons)
            }
            
        except Exception as e:
            print(f"Error comparing to previous: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_progress_report(self, user_id: int, days: int = 30) -> Dict:
        """
        Generate comprehensive progress report
        
        Args:
            user_id: User ID
            days: Number of days to include
            
        Returns:
            Dict with progress report
        """
        try:
            # Get improvement summary
            improvement_summary = self.db.get_improvement_summary(user_id)
            
            # Get goal progress
            goals = self.db.update_goal_progress(user_id)
            
            # Get statistics
            stats = self.db.get_statistics(user_id)
            
            # Get metric trends
            key_metrics = ['elbow_angle', 'release_angle', 'total']
            trends = {}
            for metric in key_metrics:
                trend_data = self.db.get_progress_trends(user_id, metric, days)
                if trend_data:
                    trends[metric] = {
                        'data_points': len(trend_data),
                        'first_value': trend_data[0][1] if trend_data else 0,
                        'last_value': trend_data[-1][1] if trend_data else 0,
                        'trend_direction': self._calculate_trend_direction(trend_data)
                    }
            
            # Calculate practice consistency
            history = self.db.get_user_history(user_id, limit=100)
            consistency = self._calculate_practice_consistency(history, days)
            
            return {
                'success': True,
                'report_date': datetime.now().isoformat(),
                'period_days': days,
                'improvement_summary': improvement_summary,
                'goals': goals,
                'statistics': stats,
                'metric_trends': trends,
                'practice_consistency': consistency,
                'recommendations': self._generate_recommendations(
                    improvement_summary, goals, consistency
                )
            }
            
        except Exception as e:
            print(f"Error generating progress report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_averages(self, history: List[Dict]) -> Dict:
        """Calculate average metrics from history"""
        metrics_sum = {}
        metrics_count = {}
        
        for analysis in history:
            metrics = analysis.get('metrics', {})
            scores = analysis.get('scores', {})
            combined = {**metrics, **scores}
            
            for key, value in combined.items():
                if isinstance(value, (int, float)):
                    metrics_sum[key] = metrics_sum.get(key, 0) + value
                    metrics_count[key] = metrics_count.get(key, 0) + 1
        
        return {
            key: metrics_sum[key] / metrics_count[key]
            for key in metrics_sum.keys()
            if metrics_count[key] > 0
        }
    
    def _calculate_overall_trend(self, comparisons: Dict) -> str:
        """Calculate overall trend from comparisons"""
        if not comparisons:
            return 'insufficient_data'
        
        improving_count = sum(1 for c in comparisons.values() if c['trend'] == 'improving')
        declining_count = sum(1 for c in comparisons.values() if c['trend'] == 'declining')
        
        if improving_count > declining_count * 1.5:
            return 'strong_improvement'
        elif improving_count > declining_count:
            return 'slight_improvement'
        elif declining_count > improving_count * 1.5:
            return 'declining'
        elif declining_count > improving_count:
            return 'slight_decline'
        else:
            return 'stable'
    
    def _calculate_trend_direction(self, trend_data: List[Tuple[str, float]]) -> str:
        """Calculate trend direction from time series data"""
        if len(trend_data) < 2:
            return 'insufficient_data'
        
        values = [v for _, v in trend_data]
        
        # Simple linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.5:
            return 'increasing'
        elif slope < -0.5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_practice_consistency(self, history: List[Dict], days: int) -> Dict:
        """Calculate practice consistency metrics"""
        if not history:
            return {
                'total_sessions': 0,
                'sessions_per_week': 0,
                'consistency_score': 0
            }
        
        # Extract dates
        dates = [datetime.fromisoformat(h['timestamp']).date() for h in history]
        
        # Filter by period
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_dates = [d for d in dates if d >= cutoff_date]
        
        total_sessions = len(recent_dates)
        weeks = days / 7
        sessions_per_week = total_sessions / weeks if weeks > 0 else 0
        
        # Calculate consistency score (based on regularity)
        if total_sessions < 2:
            consistency_score = 0
        else:
            # Calculate gaps between sessions
            sorted_dates = sorted(recent_dates)
            gaps = [(sorted_dates[i+1] - sorted_dates[i]).days 
                   for i in range(len(sorted_dates)-1)]
            
            if gaps:
                avg_gap = np.mean(gaps)
                gap_variance = np.var(gaps)
                
                # Lower variance = more consistent
                # Ideal gap: 2-3 days
                consistency_score = max(0, 100 - (gap_variance * 5))
            else:
                consistency_score = 50
        
        return {
            'total_sessions': total_sessions,
            'sessions_per_week': round(sessions_per_week, 1),
            'consistency_score': round(consistency_score, 1),
            'days_since_last': (datetime.now().date() - recent_dates[-1]).days if recent_dates else None
        }
    
    def _generate_recommendations(self, improvement_summary: Dict, 
                                 goals: List[Dict], consistency: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Practice frequency recommendations
        sessions_per_week = consistency.get('sessions_per_week', 0)
        if sessions_per_week < 2:
            recommendations.append(
                "💪 Increase practice frequency to at least 2-3 sessions per week for faster improvement"
            )
        elif sessions_per_week > 5:
            recommendations.append(
                "⚠️ Consider rest days to prevent fatigue and maintain form quality"
            )
        
        # Consistency recommendations
        consistency_score = consistency.get('consistency_score', 0)
        if consistency_score < 50:
            recommendations.append(
                "📅 Try to maintain a more regular practice schedule for better muscle memory development"
            )
        
        # Goal-based recommendations
        if goals:
            incomplete_goals = [g for g in goals if g['status'] == 'active']
            if incomplete_goals:
                closest_goal = min(incomplete_goals, 
                                 key=lambda g: abs(g['target_value'] - g.get('current_value', 0)))
                progress_percent = closest_goal.get('progress_percent', 0)
                
                if progress_percent > 80:
                    recommendations.append(
                        f"🎯 You're {progress_percent:.0f}% towards your {closest_goal['goal_type']} goal - keep it up!"
                    )
                elif progress_percent < 30:
                    recommendations.append(
                        f"💡 Focus on {closest_goal['goal_type']} - targeted drills can accelerate progress"
                    )
        
        # Improvement-based recommendations
        if improvement_summary.get('success'):
            improvements = improvement_summary.get('improvements', {})
            
            # Find areas that improved
            improved_metrics = [k for k, v in improvements.items() 
                              if v.get('percent_change', 0) > 5]
            
            if improved_metrics:
                recommendations.append(
                    f"✓ Great improvement in: {', '.join(improved_metrics[:3])}"
                )
            
            # Find areas that declined
            declined_metrics = [k for k, v in improvements.items() 
                              if v.get('percent_change', 0) < -5]
            
            if declined_metrics:
                recommendations.append(
                    f"⚠️ Focus needed on: {', '.join(declined_metrics[:2])}"
                )
        
        if not recommendations:
            recommendations.append("Keep practicing consistently to track your progress!")
        
        return recommendations

