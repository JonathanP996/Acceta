"""
Generate Synthetic Training Data for Accent Evaluator
Creates CSV file with feature distances and corresponding accent scores
"""

import os
import sys
import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_synthetic_data(
    n_samples: int = 1000,
    noise_level: float = 0.1,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic training data
    
    The relationship between features and scores is:
    - Lower distances → Higher scores (better pronunciation)
    - Higher distances → Lower scores (worse pronunciation)
    
    We'll create a realistic relationship where:
    score = f(mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff)
    
    Args:
        n_samples: Number of samples to generate
        noise_level: Amount of noise to add (0-1)
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with columns: mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff, score
    """
    np.random.seed(seed)
    
    logger.info(f"Generating {n_samples} synthetic samples...")
    
    # Generate feature distances (normalized 0-1 range)
    # These represent how far the user's features are from the reference
    
    # MFCC distance: 0-1 (0 = perfect match, 1 = very different)
    mfcc_dist = np.random.beta(2, 5, n_samples)  # Skewed towards lower values (most are good)
    
    # Pitch difference: 0-1 (normalized)
    pitch_diff = np.random.beta(2, 5, n_samples)
    
    # Formant difference: 0-1
    formant_diff = np.random.beta(2, 5, n_samples)
    
    # Duration difference: 0-1
    duration_diff = np.random.beta(2, 5, n_samples)
    
    # Intensity difference: 0-1
    intensity_diff = np.random.beta(2, 5, n_samples)
    
    # Calculate ground truth score using a realistic formula
    # Score decreases as distances increase
    # Weights: MFCC and pitch are most important (40% each), others less important
    
    # Base score from weighted average of distances (inverted)
    base_score = (
        0.40 * (1.0 - mfcc_dist) +
        0.40 * (1.0 - pitch_diff) +
        0.10 * (1.0 - formant_diff) +
        0.05 * (1.0 - duration_diff) +
        0.05 * (1.0 - intensity_diff)
    )
    
    # Add some non-linearity (scores drop faster for larger deviations)
    # Apply exponential decay for larger deviations
    score = base_score.copy()
    for i in range(n_samples):
        avg_dist = np.mean([
            mfcc_dist[i], pitch_diff[i], formant_diff[i], 
            duration_diff[i], intensity_diff[i]
        ])
        
        # If average distance is high, penalize more
        if avg_dist > 0.5:
            score[i] = score[i] * (1.0 - 0.3 * (avg_dist - 0.5))
    
    # Add noise
    noise = np.random.normal(0, noise_level * 0.1, n_samples)
    score = score + noise
    
    # Clip to valid range [0, 1]
    score = np.clip(score, 0.0, 1.0)
    
    # Create some edge cases:
    # - Perfect matches (all distances near 0) → score near 1.0
    # - Very poor matches (all distances near 1) → score near 0.0
    
    # Add some perfect examples
    n_perfect = int(n_samples * 0.1)  # 10% perfect
    perfect_indices = np.random.choice(n_samples, n_perfect, replace=False)
    mfcc_dist[perfect_indices] = np.random.uniform(0.0, 0.1, n_perfect)
    pitch_diff[perfect_indices] = np.random.uniform(0.0, 0.1, n_perfect)
    formant_diff[perfect_indices] = np.random.uniform(0.0, 0.1, n_perfect)
    duration_diff[perfect_indices] = np.random.uniform(0.0, 0.1, n_perfect)
    intensity_diff[perfect_indices] = np.random.uniform(0.0, 0.1, n_perfect)
    score[perfect_indices] = np.random.uniform(0.9, 1.0, n_perfect)
    
    # Add some poor examples
    n_poor = int(n_samples * 0.1)  # 10% poor
    poor_indices = np.random.choice(n_samples, n_poor, replace=False)
    # Make sure we don't overlap with perfect indices
    poor_indices = [idx for idx in poor_indices if idx not in perfect_indices]
    if len(poor_indices) > 0:
        mfcc_dist[poor_indices] = np.random.uniform(0.7, 1.0, len(poor_indices))
        pitch_diff[poor_indices] = np.random.uniform(0.7, 1.0, len(poor_indices))
        formant_diff[poor_indices] = np.random.uniform(0.7, 1.0, len(poor_indices))
        duration_diff[poor_indices] = np.random.uniform(0.7, 1.0, len(poor_indices))
        intensity_diff[poor_indices] = np.random.uniform(0.7, 1.0, len(poor_indices))
        score[poor_indices] = np.random.uniform(0.0, 0.3, len(poor_indices))
    
    # Create DataFrame
    df = pd.DataFrame({
        'mfcc_dist': mfcc_dist,
        'pitch_diff': pitch_diff,
        'formant_diff': formant_diff,
        'duration_diff': duration_diff,
        'intensity_diff': intensity_diff,
        'score': score
    })
    
    # Log statistics
    logger.info(f"Generated {len(df)} samples")
    logger.info(f"Feature ranges:")
    logger.info(f"  MFCC dist: {df['mfcc_dist'].min():.3f} - {df['mfcc_dist'].max():.3f}")
    logger.info(f"  Pitch diff: {df['pitch_diff'].min():.3f} - {df['pitch_diff'].max():.3f}")
    logger.info(f"  Formant diff: {df['formant_diff'].min():.3f} - {df['formant_diff'].max():.3f}")
    logger.info(f"  Duration diff: {df['duration_diff'].min():.3f} - {df['duration_diff'].max():.3f}")
    logger.info(f"  Intensity diff: {df['intensity_diff'].min():.3f} - {df['intensity_diff'].max():.3f}")
    logger.info(f"Score range: {df['score'].min():.3f} - {df['score'].max():.3f} (mean: {df['score'].mean():.3f})")
    
    return df


def generate_from_real_features(
    reference_features_path: str,
    user_features_path: str,
    output_path: str
):
    """
    Generate training data by comparing real feature extractions
    
    This function would:
    1. Load reference audio features (e.g., from TTS or native speakers)
    2. Load user audio features
    3. Compute distances between them
    4. Generate scores based on expert evaluation or heuristics
    
    Args:
        reference_features_path: Path to reference features JSON/CSV
        user_features_path: Path to user features JSON/CSV
        output_path: Path to save output CSV
    """
    # This is a placeholder for future implementation
    # You would load actual feature extractions and compute distances
    logger.warning("Real feature comparison not yet implemented")
    logger.info("Using synthetic data generation instead")
    
    df = generate_synthetic_data(n_samples=1000)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved synthetic data to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic training data for accent evaluator')
    parser.add_argument('--output', type=str, default='accent_training_data.csv', help='Output CSV path')
    parser.add_argument('--samples', type=int, default=1000, help='Number of samples to generate')
    parser.add_argument('--noise', type=float, default=0.1, help='Noise level (0-1)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Generate data
    df = generate_synthetic_data(
        n_samples=args.samples,
        noise_level=args.noise,
        seed=args.seed
    )
    
    # Save to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"✅ Saved {len(df)} samples to {output_path}")
    logger.info(f"\nFirst 5 rows:")
    print(df.head().to_string())
    
    logger.info(f"\nStatistics:")
    print(df.describe().to_string())


if __name__ == '__main__':
    main()

