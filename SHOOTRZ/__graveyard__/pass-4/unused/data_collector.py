"""
Data Collection Framework for ML Model Training

Collects and stores shooting form data with outcomes for training
shot success prediction models.
"""

import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class DataCollector:
    def __init__(self, data_file='models/shot_data.json'):
        """
        Initialize data collector
        
        Args:
            data_file: Path to JSON file for storing shot data
        """
        self.data_file = data_file
        self.data = {
            'shots': [],
            'metadata': {
                'total_shots': 0,
                'makes': 0,
                'misses': 0,
                'unknown': 0,
                'last_updated': None
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        
        # Load existing data
        self.load_data()
    
    def add_shot(self, shot_data: Dict, outcome: str = 'unknown') -> bool:
        """
        Add a shot to the dataset
        
        Args:
            shot_data: Dict with shot metrics and features
            outcome: 'make', 'miss', or 'unknown'
            
        Returns:
            Success boolean
        """
        try:
            # Validate outcome
            if outcome not in ['make', 'miss', 'unknown']:
                print(f"Invalid outcome: {outcome}")
                return False
            
            # Create shot record
            shot_record = {
                'id': len(self.data['shots']) + 1,
                'timestamp': datetime.now().isoformat(),
                'outcome': outcome,
                'features': self._extract_features(shot_data),
                'raw_data': shot_data
            }
            
            # Add to dataset
            self.data['shots'].append(shot_record)
            
            # Update metadata
            self.data['metadata']['total_shots'] += 1
            if outcome == 'make':
                self.data['metadata']['makes'] += 1
            elif outcome == 'miss':
                self.data['metadata']['misses'] += 1
            else:
                self.data['metadata']['unknown'] += 1
            
            self.data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Save to file
            self.save_data()
            
            return True
            
        except Exception as e:
            print(f"Error adding shot: {e}")
            return False
    
    def _extract_features(self, shot_data: Dict) -> Dict:
        """
        Extract ML features from shot data
        
        Args:
            shot_data: Raw shot data
            
        Returns:
            Dict of features for ML model
        """
        features = {}
        
        # Basic form metrics
        metrics = shot_data.get('metrics', {})
        features['elbow_angle'] = metrics.get('elbow_angle', 0)
        features['knee_angle'] = metrics.get('knee_angle', 0)
        features['release_angle'] = metrics.get('release_angle', 0)
        features['body_alignment'] = metrics.get('body_alignment', 0)
        
        # Advanced metrics
        advanced = shot_data.get('advanced_metrics', {})
        features['follow_through'] = advanced.get('follow_through_angle', 0)
        features['consistency'] = advanced.get('consistency_score', 0)
        features['jump_timing'] = advanced.get('jump_timing', 0)
        features['body_sway'] = advanced.get('body_sway', 0)
        
        # Trajectory metrics (if available)
        trajectory = shot_data.get('trajectory', {})
        features['shot_arc'] = trajectory.get('arc_angle', 0)
        features['release_velocity'] = trajectory.get('release_velocity', 0)
        features['peak_height'] = trajectory.get('peak_height', 0)
        features['entry_angle'] = trajectory.get('entry_angle', 0)
        
        # Camera quality metrics
        camera = shot_data.get('camera_analysis', {})
        features['camera_reliability'] = camera.get('reliability_score', 50)
        
        # Performance scores
        scores = shot_data.get('scores', {})
        features['total_score'] = scores.get('total', 0)
        
        return features
    
    def get_training_data(self, include_unknown=False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get data formatted for ML training
        
        Args:
            include_unknown: Whether to include shots with unknown outcomes
            
        Returns:
            Tuple of (features_array, labels_array)
        """
        try:
            X = []
            y = []
            
            for shot in self.data['shots']:
                outcome = shot['outcome']
                
                # Skip unknown outcomes if requested
                if outcome == 'unknown' and not include_unknown:
                    continue
                
                # Extract features
                features = shot['features']
                feature_vector = [
                    features.get('elbow_angle', 0),
                    features.get('knee_angle', 0),
                    features.get('release_angle', 0),
                    features.get('body_alignment', 0),
                    features.get('follow_through', 0),
                    features.get('consistency', 0),
                    features.get('jump_timing', 0),
                    features.get('body_sway', 0),
                    features.get('shot_arc', 0),
                    features.get('release_velocity', 0),
                    features.get('peak_height', 0),
                    features.get('entry_angle', 0),
                    features.get('camera_reliability', 50),
                    features.get('total_score', 0)
                ]
                
                # Convert outcome to binary label
                if outcome == 'make':
                    label = 1
                elif outcome == 'miss':
                    label = 0
                else:
                    label = 0.5  # Unknown
                
                X.append(feature_vector)
                y.append(label)
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            print(f"Error getting training data: {e}")
            return np.array([]), np.array([])
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of feature names
        
        Returns:
            List of feature names
        """
        return [
            'elbow_angle',
            'knee_angle',
            'release_angle',
            'body_alignment',
            'follow_through',
            'consistency',
            'jump_timing',
            'body_sway',
            'shot_arc',
            'release_velocity',
            'peak_height',
            'entry_angle',
            'camera_reliability',
            'total_score'
        ]
    
    def get_statistics(self) -> Dict:
        """
        Get dataset statistics
        
        Returns:
            Dict with statistics
        """
        makes = self.data['metadata']['makes']
        misses = self.data['metadata']['misses']
        total_labeled = makes + misses
        
        stats = {
            'total_shots': self.data['metadata']['total_shots'],
            'makes': makes,
            'misses': misses,
            'unknown': self.data['metadata']['unknown'],
            'labeled_shots': total_labeled,
            'make_percentage': (makes / total_labeled * 100) if total_labeled > 0 else 0,
            'last_updated': self.data['metadata']['last_updated']
        }
        
        return stats
    
    def update_shot_outcome(self, shot_id: int, outcome: str) -> bool:
        """
        Update the outcome of an existing shot
        
        Args:
            shot_id: ID of shot to update
            outcome: New outcome ('make', 'miss', or 'unknown')
            
        Returns:
            Success boolean
        """
        try:
            # Find shot
            shot_index = None
            for i, shot in enumerate(self.data['shots']):
                if shot['id'] == shot_id:
                    shot_index = i
                    break
            
            if shot_index is None:
                print(f"Shot ID {shot_id} not found")
                return False
            
            # Update outcome
            old_outcome = self.data['shots'][shot_index]['outcome']
            self.data['shots'][shot_index]['outcome'] = outcome
            
            # Update metadata
            if old_outcome == 'make':
                self.data['metadata']['makes'] -= 1
            elif old_outcome == 'miss':
                self.data['metadata']['misses'] -= 1
            elif old_outcome == 'unknown':
                self.data['metadata']['unknown'] -= 1
            
            if outcome == 'make':
                self.data['metadata']['makes'] += 1
            elif outcome == 'miss':
                self.data['metadata']['misses'] += 1
            elif outcome == 'unknown':
                self.data['metadata']['unknown'] += 1
            
            self.data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Save to file
            self.save_data()
            
            return True
            
        except Exception as e:
            print(f"Error updating shot outcome: {e}")
            return False
    
    def export_csv(self, output_file: str) -> bool:
        """
        Export data to CSV file
        
        Args:
            output_file: Path to output CSV file
            
        Returns:
            Success boolean
        """
        try:
            import csv
            
            feature_names = self.get_feature_names()
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['id', 'timestamp', 'outcome'] + feature_names)
                
                # Write data
                for shot in self.data['shots']:
                    row = [
                        shot['id'],
                        shot['timestamp'],
                        shot['outcome']
                    ]
                    
                    # Add features
                    features = shot['features']
                    for feature_name in feature_names:
                        row.append(features.get(feature_name, 0))
                    
                    writer.writerow(row)
            
            print(f"Data exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def load_data(self):
        """Load data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
                print(f"Loaded {self.data['metadata']['total_shots']} shots from {self.data_file}")
            else:
                print(f"No existing data file found. Starting fresh.")
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def save_data(self):
        """Save data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def clear_data(self, confirm=False):
        """
        Clear all collected data
        
        Args:
            confirm: Must be True to actually clear data
        """
        if not confirm:
            print("Warning: Set confirm=True to actually clear data")
            return False
        
        self.data = {
            'shots': [],
            'metadata': {
                'total_shots': 0,
                'makes': 0,
                'misses': 0,
                'unknown': 0,
                'last_updated': None
            }
        }
        
        self.save_data()
        print("Data cleared")
        return True

