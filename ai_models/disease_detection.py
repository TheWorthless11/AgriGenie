"""
AI/ML utilities for crop disease detection
Uses custom-trained CNN model (plant_disease_model.h5) for accurate disease detection
"""

import os
import cv2
import numpy as np
from PIL import Image
import io
import tempfile

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

# Path to custom trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "plant_disease_model.h5")

# Model input size (determined from model inspection: 256x256x3)
MODEL_INPUT_SIZE = (256, 256)


class DiseaseDetectionModel:
    """
    Handles crop disease detection using custom-trained deep learning model
    Model: plant_disease_model.h5 (15 classes, 256x256 input)
    """
    
    # Disease mapping for 15 PlantVillage classes
    # Standard PlantVillage folder naming order (alphabetical with underscores)
    DISEASE_MAPPING = {
        0: {'name': 'Pepper Bell Bacterial Spot', 'type': 'bacterial'},
        1: {'name': 'Pepper Bell Healthy', 'type': 'healthy'},
        2: {'name': 'Potato Early Blight', 'type': 'fungal'},
        3: {'name': 'Potato Healthy', 'type': 'healthy'},
        4: {'name': 'Potato Late Blight', 'type': 'fungal'},
        5: {'name': 'Tomato Bacterial Spot', 'type': 'bacterial'},
        6: {'name': 'Tomato Early Blight', 'type': 'fungal'},
        7: {'name': 'Tomato Healthy', 'type': 'healthy'},
        8: {'name': 'Tomato Late Blight', 'type': 'fungal'},
        9: {'name': 'Tomato Leaf Mold', 'type': 'fungal'},
        10: {'name': 'Tomato Septoria Leaf Spot', 'type': 'fungal'},
        11: {'name': 'Tomato Spider Mites', 'type': 'pest'},
        12: {'name': 'Tomato Target Spot', 'type': 'fungal'},
        13: {'name': 'Tomato Mosaic Virus', 'type': 'viral'},
        14: {'name': 'Tomato Yellow Leaf Curl Virus', 'type': 'viral'},
    }
    
    # Treatment recommendations for each disease
    TREATMENT_RECOMMENDATIONS = {
        'Pepper Bell Bacterial Spot': 'Remove infected leaves, apply copper-based bactericide, avoid overhead watering, rotate crops.',
        'Pepper Bell Healthy': 'Plant is healthy. Continue regular monitoring and maintenance.',
        'Potato Early Blight': 'Remove infected leaves, apply fungicide (mancozeb or chlorothalonil), improve air circulation, water at base.',
        'Potato Healthy': 'Plant is healthy. Continue regular monitoring and maintenance.',
        'Potato Late Blight': 'Remove affected plants immediately, apply copper or systemic fungicide, destroy infected debris, improve ventilation.',
        'Tomato Bacterial Spot': 'Remove infected leaves, apply copper-based spray, avoid wetting foliage, use disease-free seeds.',
        'Tomato Early Blight': 'Remove lower infected leaves, apply fungicide, mulch around plants, stake for air flow.',
        'Tomato Healthy': 'Plant is healthy. Continue regular monitoring and maintenance.',
        'Tomato Late Blight': 'Remove affected plants immediately, apply fungicide preventatively, avoid overhead watering.',
        'Tomato Leaf Mold': 'Improve ventilation, reduce humidity, remove infected leaves, apply fungicide if severe.',
        'Tomato Septoria Leaf Spot': 'Remove infected leaves from bottom up, apply fungicide, mulch to prevent splash, rotate crops.',
        'Tomato Spider Mites': 'Spray with water to dislodge mites, apply insecticidal soap or neem oil, introduce predatory mites.',
        'Tomato Target Spot': 'Remove infected leaves, apply fungicide, improve air circulation, avoid overhead irrigation.',
        'Tomato Mosaic Virus': 'Remove infected plants immediately, sanitize tools, control aphid vectors, wash hands before handling plants.',
        'Tomato Yellow Leaf Curl Virus': 'Remove infected plants, control whitefly vectors with insecticide, use reflective mulches, plant resistant varieties.',
    }
    
    def __init__(self):
        """Initialize the disease detection model"""
        self.model = None
        self.model_type = 'custom_cnn' if HAS_TENSORFLOW else 'opencv'
        self._initialize_model()
    
    def _initialize_model(self):
        """Load the custom trained plant disease model"""
        if HAS_TENSORFLOW:
            try:
                if os.path.exists(MODEL_PATH):
                    # Load custom trained model (compile=False to avoid version issues)
                    self.model = load_model(MODEL_PATH, compile=False)
                    self.model_type = 'plant_disease_model'
                    print(f"Successfully loaded plant disease model from {MODEL_PATH}")
                else:
                    print(f"Model file not found at {MODEL_PATH}")
                    self.model = None
                    self.model_type = 'opencv'
            except Exception as e:
                print(f"Error loading plant disease model: {e}")
                self.model = None
                self.model_type = 'opencv'
    
    def preprocess_image(self, image_data):
        """
        Preprocess image for model input
        Args:
            image_data: PIL Image, file path, or file object
        Returns:
            Preprocessed image array (256, 256, 3) normalized to [0, 1]
        """
        try:
            # Convert different input types to PIL Image
            if isinstance(image_data, str):
                # File path
                img = Image.open(image_data)
            elif hasattr(image_data, 'read'):
                # File-like object
                img = Image.open(image_data)
            elif isinstance(image_data, Image.Image):
                img = image_data
            else:
                # Assume numpy array or other format
                img = Image.fromarray(image_data)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to model input size (256x256)
            img = img.resize(MODEL_INPUT_SIZE)
            
            # Convert to array and normalize to [0, 1]
            img_array = np.array(img, dtype=np.float32)
            img_array /= 255.0
            
            return np.expand_dims(img_array, axis=0)
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def predict_disease(self, image_path_or_file):
        """
        Predict disease from image using the trained model
        Args:
            image_path_or_file: File path or file object
        Returns:
            Dictionary with disease information and confidence
        """
        try:
            # Preprocess image
            img_array = self.preprocess_image(image_path_or_file)
            if img_array is None:
                return self._get_default_prediction('Unknown')
            
            # Use the trained model for prediction
            if self.model is not None and HAS_TENSORFLOW:
                # Get predictions from the model
                predictions = self.model.predict(img_array, verbose=0)
                
                # Get the predicted class index and confidence
                top_disease_idx = int(np.argmax(predictions[0]))
                confidence = float(predictions[0][top_disease_idx])
                
                # Debug: Print all predictions sorted by confidence
                print("=" * 50)
                print("DEBUG: Raw model predictions:")
                sorted_indices = np.argsort(predictions[0])[::-1]  # Sort descending
                for idx in sorted_indices[:5]:  # Top 5 predictions
                    print(f"  Class {idx}: {predictions[0][idx]:.4f} -> {self.DISEASE_MAPPING.get(idx, {}).get('name', 'Unknown')}")
                print(f"Top prediction: Class {top_disease_idx} with confidence {confidence:.4f}")
                print("=" * 50)
                
                # Handle case where predicted index is out of range
                if top_disease_idx >= len(self.DISEASE_MAPPING):
                    return self._get_default_prediction('Unknown')
                
                disease_info = self.DISEASE_MAPPING[top_disease_idx]
                
                return {
                    'disease_name': disease_info['name'],
                    'disease_type': disease_info['type'],
                    'confidence': round(confidence * 100, 2),
                    'is_mock': False,
                    'model_used': self.model_type,
                    'all_predictions': {
                        self.DISEASE_MAPPING[i]['name']: round(float(predictions[0][i]) * 100, 2)
                        for i in range(min(len(predictions[0]), len(self.DISEASE_MAPPING)))
                    }
                }
            else:
                # Fallback: Use color-based heuristics when model is unavailable
                features = self._extract_fallback_features(img_array)
                disease_scores = self._calculate_disease_scores(features, img_array)
                
                top_disease_idx = np.argmax(disease_scores)
                confidence = float(np.max(disease_scores))
                
                disease_info = self.DISEASE_MAPPING.get(top_disease_idx, self.DISEASE_MAPPING[0])
                
                return {
                    'disease_name': disease_info['name'],
                    'disease_type': disease_info['type'],
                    'confidence': round(confidence * 100, 2),
                    'is_mock': True,
                    'model_used': 'opencv_fallback'
                }
        except Exception as e:
            print(f"Error predicting disease: {e}")
            return self._get_default_prediction('Unknown')
    
    def _extract_fallback_features(self, image_array):
        """Extract color histogram features for fallback mode"""
        try:
            img = (image_array[0] * 255).astype(np.uint8)
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            
            hist_h = cv2.calcHist([hsv], [0], None, [256], [0, 256])
            hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
            
            features = np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
            return features
        except Exception as e:
            print(f"Error extracting features: {e}")
            return np.zeros(768)
    
    def _calculate_disease_scores(self, features, image_array):
        """
        Fallback: Calculate disease likelihood scores based on image color features
        Only used when the trained model is unavailable
        """
        scores = np.zeros(len(self.DISEASE_MAPPING))
        
        try:
            # Normalize features
            features = (features - features.min()) / (features.max() - features.min() + 1e-8)
            
            # Analyze color patterns
            img = (image_array[0] * 255).astype(np.uint8)
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            
            # Calculate color statistics
            h_mean = np.mean(hsv[:, :, 0])
            s_mean = np.mean(hsv[:, :, 1])
            v_mean = np.mean(hsv[:, :, 2])
            
            s_ratio = s_mean / 255.0
            v_ratio = v_mean / 255.0
            h_ratio = h_mean / 180.0
            
            # Healthy classes get higher scores with high saturation
            healthy_score = (s_ratio * 0.6 + v_ratio * 0.4) if s_ratio > 0.4 else 0.3
            scores[1] = healthy_score   # Pepper Bell Healthy
            scores[4] = healthy_score   # Potato Healthy
            scores[14] = healthy_score  # Tomato Healthy
            
            # Disease classes get higher scores with lower saturation
            disease_score = max(0.3, 1.0 - s_ratio)
            for i in [0, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
                scores[i] = disease_score * (0.5 + 0.1 * (i % 3))
            
            # Normalize scores to sum to 1
            scores = np.exp(scores) / np.sum(np.exp(scores))
            
            return scores
        except Exception as e:
            print(f"Error calculating disease scores: {e}")
            # Return uniform distribution on error
            return np.ones(len(self.DISEASE_MAPPING)) / len(self.DISEASE_MAPPING)
    
    def _get_default_prediction(self, disease_name):
        """Return default prediction structure"""
        return {
            'disease_name': disease_name,
            'disease_type': 'unknown',
            'confidence': 0.0,
            'is_mock': False,
            'model_used': self.model_type
        }


# Global instance
_disease_model = None


def get_disease_detector():
    """Get or create disease detection model singleton"""
    global _disease_model
    if _disease_model is None:
        _disease_model = DiseaseDetectionModel()
    return _disease_model


def analyze_disease_image(image_file, crop_name=None):
    """
    Analyze image for crop disease
    
    Args:
        image_file: Uploaded image file
        crop_name: Name of the crop (optional)
    
    Returns:
        dict with disease information and treatment
    """
    detector = get_disease_detector()
    
    try:
        prediction = detector.predict_disease(image_file)
        disease_name = prediction['disease_name']
        treatment = detector.TREATMENT_RECOMMENDATIONS.get(
            disease_name,
            'Consult with agricultural extension officer for detailed treatment plan'
        )
        
        return {
            'name': disease_name,
            'type': prediction['disease_type'],
            'confidence': prediction['confidence'],
            'treatment': treatment,
            'crop': crop_name,
            'model_used': prediction.get('model_used', 'unknown'),
            'is_mock': prediction.get('is_mock', False)
        }
    except Exception as e:
        print(f"Error analyzing disease image: {e}")
        return {
            'name': 'Unable to analyze image',
            'type': 'error',
            'confidence': 0.0,
            'treatment': f'Error during analysis. Please try again or consult an expert.',
            'crop': crop_name,
            'error': str(e)
        }

