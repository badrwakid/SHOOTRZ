import time
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class PerformanceEvaluator:
    def __init__(self):
        """Initialize performance evaluator for tracking metrics"""
        self.metrics = {
            'processing_time': [],
            'fps': [],
            'accuracy': [],
            'pose_detection_rate': [],
            'video_duration': [],
            'frame_count': [],
            'processed_frames': []
        }
        self.evaluation_history = []
        
    def evaluate_analysis(self, video_path, processor, ground_truth=None):
        """
        Measure performance metrics for video analysis
        
        Args:
            video_path: Path to video file
            processor: VideoProcessor instance
            ground_truth: Optional ground truth data for accuracy calculation
            
        Returns:
            dict: Performance metrics
        """
        try:
            start_time = time.time()
            
            # Process video
            result = processor.process_video(video_path)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Extract metrics from result
            total_frames = result.get('total_frames', 0)
            processed_frames = result.get('processed_frames', 0)
            video_duration = result.get('video_properties', {}).get('duration', 0)
            
            # Calculate FPS
            fps = total_frames / processing_time if processing_time > 0 else 0
            
            # Calculate pose detection rate
            pose_detection_rate = (processed_frames / total_frames * 100) if total_frames > 0 else 0
            
            # Calculate accuracy if ground truth provided
            accuracy = None
            if ground_truth and result.get('metrics'):
                accuracy = self.calculate_accuracy(result['metrics'], ground_truth)
            
            # Store metrics
            self.metrics['processing_time'].append(processing_time)
            self.metrics['fps'].append(fps)
            self.metrics['pose_detection_rate'].append(pose_detection_rate)
            self.metrics['video_duration'].append(video_duration)
            self.metrics['frame_count'].append(total_frames)
            self.metrics['processed_frames'].append(processed_frames)
            
            if accuracy is not None:
                self.metrics['accuracy'].append(accuracy)
            
            # Create evaluation record
            evaluation_record = {
                'timestamp': datetime.now().isoformat(),
                'video_path': video_path,
                'processing_time': round(processing_time, 2),
                'fps': round(fps, 2),
                'pose_detection_rate': round(pose_detection_rate, 2),
                'video_duration': round(video_duration, 2),
                'total_frames': total_frames,
                'processed_frames': processed_frames,
                'accuracy': round(accuracy, 2) if accuracy is not None else None,
                'success': result.get('success', False)
            }
            
            self.evaluation_history.append(evaluation_record)
            
            return {
                'processing_time': round(processing_time, 2),
                'fps': round(fps, 2),
                'pose_detection_rate': round(pose_detection_rate, 2),
                'video_duration': round(video_duration, 2),
                'total_frames': total_frames,
                'processed_frames': processed_frames,
                'accuracy': round(accuracy, 2) if accuracy is not None else None,
                'success': result.get('success', False)
            }
            
        except Exception as e:
            print(f"Error in performance evaluation: {e}")
            return {
                'processing_time': 0,
                'fps': 0,
                'pose_detection_rate': 0,
                'video_duration': 0,
                'total_frames': 0,
                'processed_frames': 0,
                'accuracy': None,
                'success': False,
                'error': str(e)
            }
    
    def calculate_accuracy(self, predicted_metrics, ground_truth):
        """
        Calculate angle prediction accuracy
        
        Args:
            predicted_metrics: Dictionary of predicted angles
            ground_truth: Dictionary of ground truth angles
            
        Returns:
            float: Accuracy percentage
        """
        try:
            angle_keys = ['elbow_angle', 'knee_angle', 'release_angle']
            errors = []
            
            for key in angle_keys:
                if key in predicted_metrics and key in ground_truth:
                    predicted = predicted_metrics[key]
                    truth = ground_truth[key]
                    error = abs(predicted - truth)
                    errors.append(error)
            
            if not errors:
                return 0.0
            
            # Calculate accuracy: percentage of predictions within 5° threshold
            within_threshold = sum(1 for e in errors if e <= 5)
            accuracy = (within_threshold / len(errors)) * 100
            
            return accuracy
            
        except Exception as e:
            print(f"Error calculating accuracy: {e}")
            return 0.0
    
    def get_summary(self):
        """
        Get summary of all evaluation metrics
        
        Returns:
            dict: Summary statistics
        """
        try:
            summary = {
                'total_evaluations': len(self.metrics['processing_time']),
                'average_processing_time': 0,
                'average_fps': 0,
                'average_pose_detection_rate': 0,
                'average_accuracy': 0,
                'total_videos_processed': len(self.evaluation_history),
                'successful_analyses': 0,
                'failed_analyses': 0
            }
            
            if self.metrics['processing_time']:
                summary['average_processing_time'] = round(np.mean(self.metrics['processing_time']), 2)
                summary['min_processing_time'] = round(np.min(self.metrics['processing_time']), 2)
                summary['max_processing_time'] = round(np.max(self.metrics['processing_time']), 2)
            
            if self.metrics['fps']:
                summary['average_fps'] = round(np.mean(self.metrics['fps']), 2)
                summary['min_fps'] = round(np.min(self.metrics['fps']), 2)
                summary['max_fps'] = round(np.max(self.metrics['fps']), 2)
            
            if self.metrics['pose_detection_rate']:
                summary['average_pose_detection_rate'] = round(np.mean(self.metrics['pose_detection_rate']), 2)
                summary['min_pose_detection_rate'] = round(np.min(self.metrics['pose_detection_rate']), 2)
                summary['max_pose_detection_rate'] = round(np.max(self.metrics['pose_detection_rate']), 2)
            
            if self.metrics['accuracy']:
                summary['average_accuracy'] = round(np.mean(self.metrics['accuracy']), 2)
                summary['min_accuracy'] = round(np.min(self.metrics['accuracy']), 2)
                summary['max_accuracy'] = round(np.max(self.metrics['accuracy']), 2)
            
            # Count successful vs failed analyses
            for record in self.evaluation_history:
                if record.get('success', False):
                    summary['successful_analyses'] += 1
                else:
                    summary['failed_analyses'] += 1
            
            return summary
            
        except Exception as e:
            print(f"Error getting summary: {e}")
            return {
                'total_evaluations': 0,
                'average_processing_time': 0,
                'average_fps': 0,
                'average_pose_detection_rate': 0,
                'average_accuracy': 0,
                'total_videos_processed': 0,
                'successful_analyses': 0,
                'failed_analyses': 0
            }
    
    def get_recent_evaluations(self, limit=10):
        """
        Get recent evaluation records
        
        Args:
            limit: Maximum number of recent records to return
            
        Returns:
            list: Recent evaluation records
        """
        try:
            return self.evaluation_history[-limit:] if self.evaluation_history else []
        except Exception as e:
            print(f"Error getting recent evaluations: {e}")
            return []
    
    def get_performance_trends(self):
        """
        Analyze performance trends over time
        
        Returns:
            dict: Performance trend analysis
        """
        try:
            if len(self.evaluation_history) < 2:
                return {'trend': 'insufficient_data', 'message': 'Need at least 2 evaluations for trend analysis'}
            
            # Sort by timestamp
            sorted_history = sorted(self.evaluation_history, key=lambda x: x['timestamp'])
            
            # Calculate trends
            recent_half = sorted_history[len(sorted_history)//2:]
            older_half = sorted_history[:len(sorted_history)//2]
            
            trends = {}
            
            # Processing time trend
            if len(recent_half) > 0 and len(older_half) > 0:
                recent_avg_time = np.mean([r['processing_time'] for r in recent_half])
                older_avg_time = np.mean([r['processing_time'] for r in older_half])
                trends['processing_time'] = {
                    'trend': 'improving' if recent_avg_time < older_avg_time else 'degrading',
                    'recent_avg': round(recent_avg_time, 2),
                    'older_avg': round(older_avg_time, 2)
                }
            
            # FPS trend
            if len(recent_half) > 0 and len(older_half) > 0:
                recent_avg_fps = np.mean([r['fps'] for r in recent_half])
                older_avg_fps = np.mean([r['fps'] for r in older_half])
                trends['fps'] = {
                    'trend': 'improving' if recent_avg_fps > older_avg_fps else 'degrading',
                    'recent_avg': round(recent_avg_fps, 2),
                    'older_avg': round(older_avg_fps, 2)
                }
            
            # Success rate trend
            recent_success_rate = sum(1 for r in recent_half if r.get('success', False)) / len(recent_half)
            older_success_rate = sum(1 for r in older_half if r.get('success', False)) / len(older_half)
            trends['success_rate'] = {
                'trend': 'improving' if recent_success_rate > older_success_rate else 'degrading',
                'recent_rate': round(recent_success_rate * 100, 2),
                'older_rate': round(older_success_rate * 100, 2)
            }
            
            return trends
            
        except Exception as e:
            print(f"Error analyzing trends: {e}")
            return {'trend': 'error', 'message': str(e)}
    
    def reset_metrics(self):
        """Reset all metrics and history"""
        self.metrics = {
            'processing_time': [],
            'fps': [],
            'accuracy': [],
            'pose_detection_rate': [],
            'video_duration': [],
            'frame_count': [],
            'processed_frames': []
        }
        self.evaluation_history = []
        print("Performance metrics reset")
    
    def export_metrics(self, file_path):
        """
        Export metrics to file
        
        Args:
            file_path: Path to export file
        """
        try:
            import json
            
            export_data = {
                'summary': self.get_summary(),
                'trends': self.get_performance_trends(),
                'recent_evaluations': self.get_recent_evaluations(50),
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"Metrics exported to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return False


