"""
Example: Using the Accent Evaluator Model in AccentMap
Shows how to integrate the trained model with the existing accent evaluation pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from accent_infer import AccentScorePredictor


def example_integration():
    """
    Example showing how to use the accent evaluator model
    in the existing accent evaluation pipeline
    """
    
    # Load the trained model
    model_path = Path(__file__).parent.parent / "models" / "accent_model.pt"
    
    if not model_path.exists():
        print("⚠️  Model not found. Please train the model first:")
        print("   python train_accent_model.py --data accent_training_data.csv --output models/accent_model.pt")
        return
    
    print("Loading accent evaluator model...")
    predictor = AccentScorePredictor(str(model_path))
    
    # Example 1: Predict score from feature distances
    # These would come from comparing user audio vs reference audio
    print("\n📊 Example 1: Predicting accent score from feature distances")
    
    # Good pronunciation (low distances)
    score_good = predictor.predict_score(
        mfcc_dist=0.12,      # Small MFCC distance
        pitch_diff=0.05,     # Small pitch difference
        formant_diff=0.07,   # Small formant difference
        duration_diff=0.04,  # Small duration difference
        intensity_diff=0.02,  # Small intensity difference
        scale_to_100=True
    )
    print(f"   Good pronunciation → Score: {score_good:.2f}/100")
    
    # Poor pronunciation (high distances)
    score_poor = predictor.predict_score(
        mfcc_dist=0.65,      # Large MFCC distance
        pitch_diff=0.58,     # Large pitch difference
        formant_diff=0.72,   # Large formant difference
        duration_diff=0.55,  # Large duration difference
        intensity_diff=0.48, # Large intensity difference
        scale_to_100=True
    )
    print(f"   Poor pronunciation → Score: {score_poor:.2f}/100")
    
    # Example 2: Using feature list
    print("\n📊 Example 2: Using feature list")
    features = [0.15, 0.08, 0.10, 0.06, 0.03]
    score = predictor.predict_score_from_list(features, scale_to_100=True)
    print(f"   Features: {features}")
    print(f"   Predicted Score: {score:.2f}/100")
    
    # Example 3: Integration with existing pipeline
    print("\n📊 Example 3: Integration with existing accent evaluation")
    print("   In your accent evaluation code, you would:")
    print("   1. Extract acoustic features (MFCC, pitch, formants, etc.)")
    print("   2. Compute distances between user and reference features")
    print("   3. Use this model to predict accent score")
    print("   4. Combine with existing probabilistic heuristic")
    print("   5. Generate feedback using Gemini agent")
    
    print("\n✅ Example completed!")


if __name__ == '__main__':
    example_integration()

