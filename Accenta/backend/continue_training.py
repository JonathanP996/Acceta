"""
Continue Training Accent Evaluator Model
Loads existing model and continues training with more iterations
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(csv_path: str) -> tuple:
    """Load training data from CSV"""
    logger.info(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    feature_cols = ['mfcc_dist', 'pitch_diff', 'formant_diff', 'duration_diff', 'intensity_diff']
    
    if not all(col in df.columns for col in feature_cols):
        raise ValueError(f"CSV must contain columns: {feature_cols}")
    
    if 'score' not in df.columns:
        raise ValueError("CSV must contain 'score' column")
    
    features = df[feature_cols].values
    scores = df['score'].values
    
    # Normalize scores to 0-1 if they're in 0-100 range
    if scores.max() > 1.0:
        logger.info("Normalizing scores from 0-100 to 0-1 range")
        scores = scores / 100.0
    
    logger.info(f"Loaded {len(features)} samples")
    return features, scores


def continue_training(
    model: MLPRegressor,
    scaler: StandardScaler,
    X_train, y_train, X_val, y_val,
    additional_iterations: int = 2000,
    learning_rate_init: float = 1e-4
):
    """Continue training existing model with more iterations"""
    logger.info(f"Continuing training for {additional_iterations} more iterations...")
    
    # Enable warm_start to continue training
    model.warm_start = True
    model.max_iter = model.max_iter + additional_iterations
    
    # Optionally adjust learning rate
    if learning_rate_init != model.learning_rate_init:
        logger.info(f"Adjusting learning rate from {model.learning_rate_init} to {learning_rate_init}")
        model.learning_rate_init = learning_rate_init
    
    # Continue training
    model.fit(X_train, y_train)
    
    return model


def evaluate_model(model, X_test, y_test, scaler):
    """Evaluate model on test set"""
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    y_pred = np.clip(y_pred, 0, 1)
    
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Test Metrics:")
    logger.info(f"  MSE: {mse:.6f}")
    logger.info(f"  MAE: {mae:.6f}")
    logger.info(f"  RMSE: {rmse:.6f}")
    logger.info(f"  R²: {r2:.4f}")
    
    return {
        'mse': float(mse),
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2)
    }


def main():
    parser = argparse.ArgumentParser(description='Continue Training Accent Evaluator Model')
    parser.add_argument('--model', type=str, required=True, help='Path to existing model (.pkl file)')
    parser.add_argument('--data', type=str, required=True, help='Path to training CSV file')
    parser.add_argument('--output', type=str, default=None, help='Output model path (default: overwrite input)')
    parser.add_argument('--iterations', type=int, default=2000, help='Additional iterations to train')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--test-split', type=float, default=0.2, help='Test set split ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Load existing model
    logger.info(f"Loading existing model from {args.model}")
    model_data = joblib.load(args.model)
    model = model_data['model']
    scaler = model_data['scaler']
    old_metrics = model_data.get('metrics', {})
    
    logger.info(f"Model had {model.max_iter} max iterations")
    logger.info(f"Previous metrics: {old_metrics}")
    
    # Load data
    features, scores = load_data(args.data)
    
    # Normalize features (use existing scaler)
    features_scaled = scaler.transform(features)
    
    # Split data (same split as before)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        features_scaled, scores,
        test_size=args.test_split,
        random_state=args.seed
    )
    
    val_size = 0.2 / (1 - args.test_split)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val,
        test_size=val_size,
        random_state=args.seed
    )
    
    logger.info(f"Data splits: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Continue training
    model = continue_training(
        model, scaler,
        X_train, y_train, X_val, y_val,
        additional_iterations=args.iterations,
        learning_rate_init=args.lr
    )
    
    # Evaluate
    logger.info("\nEvaluating on test set...")
    new_metrics = evaluate_model(model, X_test, y_test, scaler)
    
    # Compare metrics
    logger.info("\n📊 Metrics Comparison:")
    if old_metrics:
        logger.info(f"  Previous RMSE: {old_metrics.get('rmse', 'N/A'):.6f}")
        logger.info(f"  New RMSE:      {new_metrics['rmse']:.6f}")
        improvement = old_metrics.get('rmse', 1.0) - new_metrics['rmse']
        if improvement > 0:
            logger.info(f"  ✅ Improved by: {improvement:.6f}")
        else:
            logger.info(f"  ⚠️  Changed by: {improvement:.6f}")
    
    # Save model
    output_path = args.output if args.output else args.model
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_data['model'] = model
    model_data['metrics'] = new_metrics
    model_data['previous_metrics'] = old_metrics
    
    joblib.dump(model_data, output_path)
    logger.info(f"Model saved to {output_path}")
    logger.info(f"Total iterations: {model.max_iter}")
    
    logger.info("\n✅ Continued training completed successfully!")


if __name__ == '__main__':
    main()

