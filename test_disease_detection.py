"""
Quick test script for disease detection model
Run: python test_disease_detection.py
"""
import numpy as np
from PIL import Image
from ai_models.disease_detection import analyze_disease_image, get_disease_detector

# Create a simple test image (random colored pattern)
print("Creating test image...")
test_img = Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8))
test_img.save('test_leaf.jpg')

# Get detector info
detector = get_disease_detector()
print(f"\nModel type: {detector.model_type}")
print(f"Model loaded: {detector.model is not None}")
print(f"Number of classes: {len(detector.DISEASE_MAPPING)}")

# Run prediction
print("\nRunning prediction on test image...")
result = analyze_disease_image('test_leaf.jpg')

print("\n=== Prediction Result ===")
print(f"Disease: {result['name']}")
print(f"Type: {result['type']}")
print(f"Confidence: {result['confidence']}%")
print(f"Model used: {result['model_used']}")
print(f"Is mock: {result.get('is_mock', False)}")
print(f"\nTreatment recommendation:")
print(f"  {result['treatment']}")

# Cleanup
import os
os.remove('test_leaf.jpg')
print("\nTest completed successfully!")
