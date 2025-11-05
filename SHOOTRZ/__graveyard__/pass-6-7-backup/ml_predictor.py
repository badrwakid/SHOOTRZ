"""
ML-Based Shot Success Predictor

Uses trained LightGBM model to predict shot success probability
based on form metrics and trajectory data.
"""

import numpy as np
import os
from typing import Dict, Optional
import joblib

class ShotPredictor:
    def __init__(self, model_path='models/shot_predictor.pkl'):
        """
        Initialize shot predictor
        
        Args:
            model_path: Path to trained model file
        """
        self.model_path = model_path
        self.model = None
        self.feature_names = None
        self.model_metadata = {}
        self.is_loaded = False
        
        # Try to load model
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Load trained model
        
        Returns:
            Success boolean
        """
        try:
            if not os.path.exists(self.model_path):
                print(f"⚠ Model file not found: {self.model_path}")
                print("  Using rule-based prediction instead")
                return False
            
            model_data = joblib.load(self.model_path)
            
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.model_metadata = model_data.get('metadata', {})
            self.is_loaded = True
            
            print(f"✓ ML model loaded from {self.model_path}")
            return True
            
        except Exception as e:
            print(f"⚠ Error loading model: {e}")
            print("  Using rule-based prediction instead")
            return False
    
    def predict(self, features: Dict) -> Dict:
        """
        Predict shot success probability
        
        Args:
            features: Dict of feature values
            
        Returns:
            Dict with prediction results
        """
        try:
            if not self.is_loaded or self.model is None:
                # Fall back to rule-based prediction
                return self._rule_based_prediction(features)
            
            # Extract features in correct order
            feature_vector = self._extract_feature_vector(features)
            
            # Make prediction
            prediction_proba = self.model.predict_proba([feature_vector])[0]
            probability_make = float(prediction_proba[1]) * 100  # Convert to percentage
            
            # Get confidence score
            confidence = self._calculate_confidence(prediction_proba)
            
            # Get feature contributions (SHAP-like interpretation)
            feature_contributions = self._get_feature_contributions(feature_vector)
            
            return {
                'success': True,
                'method': 'ml',
                'probability_make': round(probability_make, 1),
                'probability_miss': round(100 - probability_make, 1),
                'confidence': round(confidence, 1),
                'prediction': 'make' if probability_make >= 50 else 'miss',
                'feature_contributions': feature_contributions,
                'model_accuracy': self.model_metadata.get('accuracy', 0) * 100
            }
            
        except Exception as e:
            print(f"Error in ML prediction: {e}")
            return self._rule_based_prediction(features)
    
    def _extract_feature_vector(self, features: Dict) -> np.ndarray:
        """
        Extract feature vector from feature dict
        
        Args:
            features: Dict of feature values
            
        Returns:
            Feature vector array
        """
        feature_vector = []
        
        for feature_name in self.feature_names:
            value = features.get(feature_name, 0)
            feature_vector.append(float(value))
        
        return np.array(feature_vector)
    
    def _calculate_confidence(self, prediction_proba: np.ndarray) -> float:
        """
        Calculate confidence score from prediction probabilities
        
        Args:
            prediction_proba: Probability array [p_miss, p_make]
            
        Returns:
            Confidence score (0-100)
        """
        # Confidence is how far from 50/50 the prediction is
        # Higher separation = higher confidence
        separation = abs(prediction_proba[1] - 0.5) * 2  # Normalize to 0-1
        confidence = separation * 100
        
        return float(confidence)
    
    def _get_feature_contributions(self, feature_vector: np.ndarray) -> Dict:
        """
        Get feature contributions to prediction
        
        Args:
            feature_vector: Feature values
            
        Returns:
            Dict of feature contributions
        """
        try:
            # Get feature importance from model
            feature_importance = self.model.feature_importances_
            
            # Normalize feature values to 0-1 range
            normalized_values = []
            for i, value in enumerate(feature_vector):
                # Simple min-max normalization (approximate)
                if value > 0:
                    normalized = min(value / 100, 1.0)  # Assume max ~100
                else:
                    normalized = 0.0
                normalized_values.append(normalized)
            
            # Calculate weighted contributions
            contributions = {}
            for i, feature_name in enumerate(self.feature_names):
                contribution = feature_importance[i] * normalized_values[i]
                contributions[feature_name] = float(contribution)
            
            # Sort by contribution
            sorted_contributions = dict(
                sorted(contributions.items(), key=lambda x: x[1], reverse=True)
            )
            
            # Return top 5 contributors
            return dict(list(sorted_contributions.items())[:5])
            
        except Exception as e:
            print(f"Error calculating feature contributions: {e}")
            return {}
    
    def _rule_based_prediction(self, features: Dict) -> Dict:
        """
        Rule-based prediction fallback (when ML model not available)
        
        Args:
            features: Feature dict
            
        Returns:
            Prediction dict
        """
        # Calculate score based on ideal values
        score = 50.0  # Base score
        
        # Elbow angle (ideal: 90°)
        elbow = features.get('elbow_angle', 0)
        if 85 <= elbow <= 95:
            score += 10
        elif 80 <= elbow <= 100:
            score += 5
        else:
            score -= 5
        
        # Release angle (ideal: 45-50°)
        release = features.get('release_angle', 0)
        if 45 <= release <= 50:
            score += 10
        elif 40 <= release <= 55:
            score += 5
        else:
            score -= 5
        
        # Knee angle (ideal: 120-140°)
        knee = features.get('knee_angle', 0)
        if 120 <= knee <= 140:
            score += 8
        elif 110 <= knee <= 150:
            score += 4
        else:
            score -= 4
        
        # Body alignment (ideal: 90-100)
        alignment = features.get('body_alignment', 0)
        if alignment >= 90:
            score += 8
        elif alignment >= 80:
            score += 4
        else:
            score -= 4
        
        # Trajectory (if available)
        shot_arc = features.get('shot_arc', 0)
        if 43 <= shot_arc <= 50:
            score += 7
        elif shot_arc > 0:
            score += 3
        
        # Clamp to 0-100
        probability_make = max(0, min(100, score))
        
        return {
            'success': True,
            'method': 'rule_based',
            'probability_make': round(probability_make, 1),
            'probability_miss': round(100 - probability_make, 1),
            'confidence': 70.0,  # Rule-based has moderate confidence
            'prediction': 'make' if probability_make >= 50 else 'miss',
            'feature_contributions': {},
            'model_accuracy': 0
        }
    
    def get_model_info(self) -> Dict:
        """
        Get model information
        
        Returns:
            Dict with model info
        """
        if not self.is_loaded:
            return {
                'loaded': False,
                'method': 'rule_based',
                'message': 'ML model not loaded, using rule-based prediction'
            }
        
        return {
            'loaded': True,
            'method': 'ml',
            'model_path': self.model_path,
            'feature_count': len(self.feature_names),
            'accuracy': self.model_metadata.get('accuracy', 0),
            'training_date': self.model_metadata.get('training_date', 'unknown')
        }


class EnsemblePredictor:
    """
    Ensemble predictor combining ML and rule-based predictions
    """
    
    def __init__(self, model_path='models/shot_predictor.pkl'):
        """
        Initialize ensemble predictor
        
        Args:
            model_path: Path to ML model
        """
        self.ml_predictor = ShotPredictor(model_path)
        
        # Weights for ensemble (can be adjusted)
        self.ml_weight = 0.7
        self.rule_weight = 0.3
    
    def predict(self, features: Dict) -> Dict:
        """
        Make ensemble prediction
        
        Args:
            features: Feature dict
            
        Returns:
            Combined prediction
        """
        # Get ML prediction
        ml_result = self.ml_predictor.predict(features)
        
        # Get rule-based prediction
        rule_result = self.ml_predictor._rule_based_prediction(features)
        
        # Combine predictions
        if ml_result['method'] == 'ml':
            # Both predictions available - ensemble
            combined_probability = (
                ml_result['probability_make'] * self.ml_weight +
                rule_result['probability_make'] * self.rule_weight
            )
            
            confidence = (
                ml_result['confidence'] * self.ml_weight +
                rule_result['confidence'] * self.rule_weight
            )
            
            method = 'ensemble'
        else:
            # Only rule-based available
            combined_probability = rule_result['probability_make']
            confidence = rule_result['confidence']
            method = 'rule_based'
        
        return {
            'success': True,
            'method': method,
            'probability_make': round(combined_probability, 1),
            'probability_miss': round(100 - combined_probability, 1),
            'confidence': round(confidence, 1),
            'prediction': 'make' if combined_probability >= 50 else 'miss',
            'ml_prediction': ml_result['probability_make'],
            'rule_prediction': rule_result['probability_make'],
            'feature_contributions': ml_result.get('feature_contributions', {})
        }
    
    def adjust_weights(self, ml_weight: float):
        """
        Adjust ensemble weights
        
        Args:
            ml_weight: Weight for ML prediction (0-1)
        """
        self.ml_weight = max(0, min(1, ml_weight))
        self.rule_weight = 1 - self.ml_weight

