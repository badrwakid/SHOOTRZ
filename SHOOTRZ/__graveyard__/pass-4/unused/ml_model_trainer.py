"""
ML Model Trainer for Shot Success Prediction

Trains LightGBM models on collected shot data to predict
shot success probability based on form metrics.
"""

import numpy as np
import joblib
import os
from datetime import datetime
from typing import Dict, Tuple, Optional
import json

class MLModelTrainer:
    def __init__(self, model_save_path='models/shot_predictor.pkl'):
        """
        Initialize ML model trainer
        
        Args:
            model_save_path: Path to save trained model
        """
        self.model_save_path = model_save_path
        self.model = None
        self.feature_names = None
        self.training_history = []
        self.model_metadata = {}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    
    def train_model(self, X: np.ndarray, y: np.ndarray, 
                   feature_names: list) -> Dict:
        """
        Train LightGBM model
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,) - 0 or 1 for miss/make
            feature_names: List of feature names
            
        Returns:
            Dict with training results
        """
        try:
            import lightgbm as lgb
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            
            if len(X) < 10:
                return {
                    'success': False,
                    'error': 'Insufficient training data (need at least 10 samples)'
                }
            
            self.feature_names = feature_names
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
            )
            
            # Create LightGBM model (optimized for CPU)
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                num_leaves=31,
                random_state=42,
                n_jobs=1,  # Single thread for consistency
                verbose=-1
            )
            
            # Train model
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                eval_metric='binary_logloss',
                callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
            )
            
            # Evaluate on test set
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
            except:
                auc = 0.5
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X, y, cv=min(5, len(X) // 2), scoring='accuracy')
            
            # Feature importance
            feature_importance = dict(zip(feature_names, self.model.feature_importances_))
            sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            # Store metadata
            self.model_metadata = {
                'training_date': datetime.now().isoformat(),
                'n_samples': len(X),
                'n_features': len(feature_names),
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'auc': float(auc),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'feature_importance': {k: float(v) for k, v in sorted_importance}
            }
            
            # Save model
            self.save_model()
            
            # Update training history
            self.training_history.append(self.model_metadata)
            
            return {
                'success': True,
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'auc': float(auc),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'feature_importance': {k: float(v) for k, v in sorted_importance[:5]},  # Top 5
                'model_path': self.model_save_path
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'lightgbm not installed. Run: pip install lightgbm'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Training error: {str(e)}'
            }
    
    def train_with_professional_data(self, user_X: np.ndarray, user_y: np.ndarray,
                                    feature_names: list) -> Dict:
        """
        Train model with both user data and professional benchmarks
        
        Args:
            user_X: User feature matrix
            user_y: User labels
            feature_names: Feature names
            
        Returns:
            Training results
        """
        try:
            # Load professional benchmarks
            from professional_benchmarks import PROFESSIONAL_PLAYERS
            
            # Extract features from professional players (all assumed to be "makes")
            pro_X = []
            pro_y = []
            
            for player_key, player_data in PROFESSIONAL_PLAYERS.items():
                benchmarks = player_data['benchmarks']
                
                # Create feature vector
                features = [
                    benchmarks.get('elbow_angle', 90),
                    benchmarks.get('knee_angle', 130),
                    benchmarks.get('release_angle', 47),
                    benchmarks.get('body_alignment', 96),
                    benchmarks.get('follow_through', 90),
                    benchmarks.get('consistency', 95),
                    benchmarks.get('jump_timing', 90),
                    benchmarks.get('body_sway', 90),
                    benchmarks.get('shot_arc', 46),
                    5.0,  # release_velocity (assumed)
                    100.0,  # peak_height (assumed)
                    45.0,  # entry_angle (assumed)
                    100.0,  # camera_reliability (assumed perfect)
                    95.0   # total_score (assumed high)
                ]
                
                pro_X.append(features)
                pro_y.append(1)  # All professional shots assumed to be makes
            
            pro_X = np.array(pro_X)
            pro_y = np.array(pro_y)
            
            # Combine with user data
            if len(user_X) > 0:
                combined_X = np.vstack([user_X, pro_X])
                combined_y = np.concatenate([user_y, pro_y])
            else:
                combined_X = pro_X
                combined_y = pro_y
            
            # Train model
            return self.train_model(combined_X, combined_y, feature_names)
            
        except Exception as e:
            print(f"Error training with professional data: {e}")
            # Fall back to user data only
            return self.train_model(user_X, user_y, feature_names)
    
    def save_model(self):
        """Save trained model to file"""
        try:
            if self.model is None:
                print("No model to save")
                return False
            
            # Save model and metadata
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'metadata': self.model_metadata
            }
            
            joblib.dump(model_data, self.model_save_path)
            
            # Save metadata as JSON
            metadata_path = self.model_save_path.replace('.pkl', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
            
            print(f"Model saved to {self.model_save_path}")
            return True
            
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self) -> bool:
        """
        Load trained model from file
        
        Returns:
            Success boolean
        """
        try:
            if not os.path.exists(self.model_save_path):
                print(f"Model file not found: {self.model_save_path}")
                return False
            
            model_data = joblib.load(self.model_save_path)
            
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.model_metadata = model_data.get('metadata', {})
            
            print(f"Model loaded from {self.model_save_path}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """
        Get information about trained model
        
        Returns:
            Dict with model information
        """
        if self.model is None:
            return {'trained': False, 'message': 'No model trained'}
        
        return {
            'trained': True,
            'model_type': 'LightGBM Classifier',
            'feature_names': self.feature_names,
            'metadata': self.model_metadata
        }


class ModelOptimizer:
    """
    Optimize model for faster inference
    """
    
    def __init__(self):
        """Initialize model optimizer"""
        self.optimized_model = None
    
    def optimize_for_cpu(self, model_path: str, output_path: str = None) -> bool:
        """
        Optimize model for CPU inference
        
        Args:
            model_path: Path to model file
            output_path: Path to save optimized model
            
        Returns:
            Success boolean
        """
        try:
            import joblib
            
            # Load model
            model_data = joblib.load(model_path)
            model = model_data['model']
            
            # LightGBM models are already optimized for CPU
            # Just ensure single-threaded for consistency
            if hasattr(model, 'set_params'):
                model.set_params(n_jobs=1)
            
            # Save optimized model
            if output_path is None:
                output_path = model_path.replace('.pkl', '_optimized.pkl')
            
            model_data['model'] = model
            joblib.dump(model_data, output_path)
            
            print(f"Optimized model saved to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error optimizing model: {e}")
            return False
    
    def benchmark_model(self, model_path: str, test_samples: int = 100) -> Dict:
        """
        Benchmark model inference speed
        
        Args:
            model_path: Path to model file
            test_samples: Number of test samples
            
        Returns:
            Dict with benchmark results
        """
        try:
            import time
            import joblib
            
            # Load model
            model_data = joblib.load(model_path)
            model = model_data['model']
            feature_names = model_data['feature_names']
            
            # Generate random test data
            X_test = np.random.randn(test_samples, len(feature_names))
            
            # Benchmark prediction
            start_time = time.time()
            predictions = model.predict_proba(X_test)
            end_time = time.time()
            
            total_time = end_time - start_time
            avg_time_per_sample = total_time / test_samples
            
            return {
                'success': True,
                'test_samples': test_samples,
                'total_time_seconds': round(total_time, 4),
                'avg_time_per_sample_ms': round(avg_time_per_sample * 1000, 2),
                'predictions_per_second': round(test_samples / total_time, 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Benchmark error: {str(e)}'
            }

