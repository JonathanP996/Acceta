"""
Accent Score Inference (Scikit-learn version)
Load trained model and predict accent scores
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import numpy as np
import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccentScorePredictor:
    """Wrapper for scikit-learn accent evaluator model"""
    
    def __init__(self, model_path: str):
        """Load trained model"""
        logger.info(f"Loading model from {model_path}")
        model_data = joblib.load(model_path)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        
        if 'metrics' in model_data:
            logger.info(f"Model metrics: {model_data['metrics']}")
        
        logger.info("Model loaded successfully")
    
    def predict_score(
        self,
        mfcc_dist: float,
        pitch_diff: float,
        formant_diff: float,
        duration_diff: float,
        intensity_diff: float,
        scale_to_100: bool = True
    ) -> float:
        """Predict accent score from feature distances"""
        features = np.array([[mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff]])
        
        # Normalize features
        features_normalized = self.scaler.transform(features)
        
        # Predict
        score = self.model.predict(features_normalized)[0]
        
        # Clip to [0, 1]
        score = np.clip(score, 0.0, 1.0)
        
        # Scale to 0-100 if requested
        if scale_to_100:
            score = score * 100.0
        
        return float(score)
    
    def predict_score_from_list(self, features: list[float], scale_to_100: bool = True) -> float:
        """Predict from feature list"""
        if len(features) != 5:
            raise ValueError(f"Expected 5 features, got {len(features)}")
        
        return self.predict_score(
            mfcc_dist=features[0],
            pitch_diff=features[1],
            formant_diff=features[2],
            duration_diff=features[3],
            intensity_diff=features[4],
            scale_to_100=scale_to_100
        )


def main():
    parser = argparse.ArgumentParser(description='Predict accent score')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--mfcc-dist', type=float, help='MFCC distance')
    parser.add_argument('--pitch-diff', type=float, help='Pitch difference')
    parser.add_argument('--formant-diff', type=float, help='Formant difference')
    parser.add_argument('--duration-diff', type=float, help='Duration difference')
    parser.add_argument('--intensity-diff', type=float, help='Intensity difference')
    parser.add_argument('--features', type=str, help='Comma-separated list of 5 features')
    parser.add_argument('--scale', type=bool, default=True, help='Scale to 0-100')
    
    args = parser.parse_args()
    
    predictor = AccentScorePredictor(args.model)
    
    if args.features:
        features = [float(x.strip()) for x in args.features.split(',')]
        if len(features) != 5:
            raise ValueError("Must provide exactly 5 features")
        score = predictor.predict_score_from_list(features, scale_to_100=args.scale)
    elif all([args.mfcc_dist is not None, args.pitch_diff is not None, 
              args.formant_diff is not None, args.duration_diff is not None, 
              args.intensity_diff is not None]):
        score = predictor.predict_score(
            mfcc_dist=args.mfcc_dist,
            pitch_diff=args.pitch_diff,
            formant_diff=args.formant_diff,
            duration_diff=args.duration_diff,
            intensity_diff=args.intensity_diff,
            scale_to_100=args.scale
        )
    else:
        print("Enter feature values:")
        mfcc_dist = float(input("MFCC distance: "))
        pitch_diff = float(input("Pitch difference: "))
        formant_diff = float(input("Formant difference: "))
        duration_diff = float(input("Duration difference: "))
        intensity_diff = float(input("Intensity difference: "))
        
        score = predictor.predict_score(
            mfcc_dist=mfcc_dist,
            pitch_diff=pitch_diff,
            formant_diff=formant_diff,
            duration_diff=duration_diff,
            intensity_diff=intensity_diff,
            scale_to_100=args.scale
        )
    
    scale_text = "0-100" if args.scale else "0-1"
    print(f"\n🎯 Predicted Accent Score: {score:.2f} ({scale_text})")
    
    return score


if __name__ == '__main__':
    main()

