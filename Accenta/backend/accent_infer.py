"""
Accent Score Inference
Load trained model and predict accent scores from feature distances
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import torch
import numpy as np

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent))
from models.accent_evaluator import AccentEvaluator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccentScorePredictor:
    """
    Wrapper class for loading and using the trained accent evaluator model
    """
    
    def __init__(self, model_path: str, scaler_path: str = None):
        """
        Initialize predictor with trained model
        
        Args:
            model_path: Path to saved model (.pt file)
            scaler_path: Path to saved scaler (.npy file). If None, tries to load from model_path
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Loading model on {self.device}")
        
        # Load model checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Create model
        input_dim = checkpoint.get('input_dim', 5)
        hidden_dim1 = checkpoint.get('hidden_dim1', 32)
        hidden_dim2 = checkpoint.get('hidden_dim2', 16)
        
        self.model = AccentEvaluator(
            input_dim=input_dim,
            hidden_dim1=hidden_dim1,
            hidden_dim2=hidden_dim2
        )
        
        # Load model weights
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        self.model = self.model.to(self.device)
        
        logger.info("Model loaded successfully")
        
        # Load scaler
        if scaler_path is None:
            # Try to find scaler file next to model
            scaler_path = str(Path(model_path).with_suffix('.scaler.npy'))
        
        if os.path.exists(scaler_path):
            scaler_data = np.load(scaler_path, allow_pickle=True).item()
            self.scaler_mean = scaler_data['mean']
            self.scaler_scale = scaler_data['scale']
            logger.info("Scaler loaded successfully")
        elif 'scaler_mean' in checkpoint and 'scaler_scale' in checkpoint:
            # Load from checkpoint if available
            self.scaler_mean = checkpoint['scaler_mean']
            self.scaler_scale = checkpoint['scaler_scale']
            logger.info("Scaler loaded from checkpoint")
        else:
            logger.warning("No scaler found - using raw features (may affect accuracy)")
            self.scaler_mean = np.zeros(5)
            self.scaler_scale = np.ones(5)
        
        # Print model info
        if 'metrics' in checkpoint:
            logger.info(f"Model metrics: {checkpoint['metrics']}")
    
    def predict_score(
        self,
        mfcc_dist: float,
        pitch_diff: float,
        formant_diff: float,
        duration_diff: float,
        intensity_diff: float,
        scale_to_100: bool = True
    ) -> float:
        """
        Predict accent score from feature distances
        
        Args:
            mfcc_dist: Distance in MFCC space (normalized)
            pitch_diff: Pitch difference (normalized)
            formant_diff: Formant difference (normalized)
            duration_diff: Duration difference (normalized)
            intensity_diff: Intensity difference (normalized)
            scale_to_100: If True, return score in 0-100 range (default: True)
        
        Returns:
            Predicted accent score (0-1 or 0-100)
        """
        # Prepare features
        features = np.array([[mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff]])
        
        # Normalize features
        features_normalized = (features - self.scaler_mean) / self.scaler_scale
        
        # Convert to tensor
        features_tensor = torch.FloatTensor(features_normalized).to(self.device)
        
        # Predict
        with torch.no_grad():
            output = self.model(features_tensor)
            score = output.item()
        
        # Scale to 0-100 if requested
        if scale_to_100:
            score = score * 100.0
        
        return score
    
    def predict_score_from_list(self, features: list[float], scale_to_100: bool = True) -> float:
        """
        Predict accent score from feature list
        
        Args:
            features: List of 5 feature values [mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff]
            scale_to_100: If True, return score in 0-100 range (default: True)
        
        Returns:
            Predicted accent score (0-1 or 0-100)
        """
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
    parser = argparse.ArgumentParser(description='Predict accent score from feature distances')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model (.pt file)')
    parser.add_argument('--scaler', type=str, default=None, help='Path to scaler file (optional)')
    parser.add_argument('--mfcc-dist', type=float, help='MFCC distance')
    parser.add_argument('--pitch-diff', type=float, help='Pitch difference')
    parser.add_argument('--formant-diff', type=float, help='Formant difference')
    parser.add_argument('--duration-diff', type=float, help='Duration difference')
    parser.add_argument('--intensity-diff', type=float, help='Intensity difference')
    parser.add_argument('--features', type=str, help='Comma-separated list of 5 features')
    parser.add_argument('--scale', type=bool, default=True, help='Scale output to 0-100 (default: True)')
    
    args = parser.parse_args()
    
    # Load predictor
    predictor = AccentScorePredictor(args.model, args.scaler)
    
    # Get features
    if args.features:
        # Parse from comma-separated string
        features = [float(x.strip()) for x in args.features.split(',')]
        if len(features) != 5:
            raise ValueError("Must provide exactly 5 features")
        score = predictor.predict_score_from_list(features, scale_to_100=args.scale)
    elif all([args.mfcc_dist is not None, args.pitch_diff is not None, 
              args.formant_diff is not None, args.duration_diff is not None, 
              args.intensity_diff is not None]):
        # Parse from individual arguments
        score = predictor.predict_score(
            mfcc_dist=args.mfcc_dist,
            pitch_diff=args.pitch_diff,
            formant_diff=args.formant_diff,
            duration_diff=args.duration_diff,
            intensity_diff=args.intensity_diff,
            scale_to_100=args.scale
        )
    else:
        # Interactive mode
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
    
    # Print result
    scale_text = "0-100" if args.scale else "0-1"
    print(f"\n🎯 Predicted Accent Score: {score:.2f} ({scale_text})")
    
    return score


if __name__ == '__main__':
    main()

