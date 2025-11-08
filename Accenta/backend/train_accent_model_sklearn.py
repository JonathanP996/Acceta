"""
Train Accent Evaluator Model (Scikit-learn version)
Works with Python 3.13 - uses scikit-learn instead of PyTorch
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
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
    logger.info(f"Feature ranges: {features.min(axis=0)} to {features.max(axis=0)}")
    logger.info(f"Score range: {scores.min():.3f} to {scores.max():.3f}")
    
    return features, scores


def train_model(
    X_train, y_train, X_val, y_val,
    hidden_layer_sizes=(32, 16),
    max_iter=200,
    learning_rate_init=1e-3,
    early_stopping=True,
    n_iter_no_change=20
):
    """Train MLP regressor"""
    logger.info(f"Training model with hidden layers: {hidden_layer_sizes}")
    logger.info(f"Max iterations: {max_iter}, Early stopping patience: {n_iter_no_change}")
    
    model = MLPRegressor(
        hidden_layer_sizes=hidden_layer_sizes,
        activation='relu',
        solver='adam',
        alpha=0.0001,  # L2 regularization
        batch_size=32,
        learning_rate='constant',
        learning_rate_init=learning_rate_init,
        max_iter=max_iter,
        shuffle=True,
        random_state=42,
        tol=1e-6,
        verbose=True,
        warm_start=False,
        momentum=0.9,
        nesterovs_momentum=True,
        early_stopping=early_stopping,
        validation_fraction=0.1 if not X_val is None else 0.0,
        n_iter_no_change=n_iter_no_change,
        max_fun=15000
    )
    
    # Train
    if X_val is not None:
        # Use validation set
        model.fit(X_train, y_train)
    else:
        # Use built-in validation
        model.fit(X_train, y_train)
    
    return model


def evaluate_model(model, X_test, y_test, scaler):
    """Evaluate model on test set"""
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    
    # Clip predictions to [0, 1]
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


def plot_training_history(model, save_path: str = None):
    """Plot training history"""
    if not hasattr(model, 'loss_curve_'):
        logger.warning("Model doesn't have loss curve (may not have validation set)")
        return
    
    plt.figure(figsize=(10, 6))
    plt.plot(model.loss_curve_, label='Training Loss', alpha=0.7)
    if hasattr(model, 'validation_scores_') and model.validation_scores_ is not None:
        # Only plot if validation_scores_ exists and is not None
        try:
            plt.plot(model.validation_scores_, label='Validation Score', alpha=0.7)
        except (ValueError, TypeError):
            logger.warning("Could not plot validation scores")
    plt.xlabel('Iteration')
    plt.ylabel('Loss')
    plt.title('Training History')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path)
        logger.info(f"Saved training plot to {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Train Accent Evaluator Model (Scikit-learn)')
    parser.add_argument('--data', type=str, required=True, help='Path to training CSV file')
    parser.add_argument('--output', type=str, default='accent_model_sklearn.pkl', help='Output model path')
    parser.add_argument('--epochs', type=int, default=200, help='Maximum iterations')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--test-split', type=float, default=0.2, help='Test set split ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--plot', action='store_true', help='Plot training history')
    parser.add_argument('--large-model', action='store_true', help='Use larger model (64, 32, 16) for longer training')
    parser.add_argument('--no-early-stop', action='store_true', help='Disable early stopping (train for full epochs)')
    
    args = parser.parse_args()
    
    # Set random seed
    np.random.seed(args.seed)
    
    # Load data
    features, scores = load_data(args.data)
    
    # Normalize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Split data: train -> (train + val), test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        features_scaled, scores,
        test_size=args.test_split,
        random_state=args.seed
    )
    
    # Split train_val: train, val
    val_size = 0.2 / (1 - args.test_split)  # Adjust for already split data
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val,
        test_size=val_size,
        random_state=args.seed
    )
    
    logger.info(f"Data splits: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Choose model architecture
    if args.large_model:
        hidden_layers = (64, 32, 16)  # Larger model
        logger.info("Using LARGE model architecture: (64, 32, 16)")
    else:
        hidden_layers = (32, 16)  # Standard model
        logger.info("Using standard model architecture: (32, 16)")
    
    # Train model
    model = train_model(
        X_train, y_train, X_val, y_val,
        hidden_layer_sizes=hidden_layers,
        max_iter=args.epochs,
        learning_rate_init=args.lr,
        early_stopping=not args.no_early_stop,
        n_iter_no_change=20 if not args.no_early_stop else args.epochs
    )
    
    # Evaluate
    logger.info("\nEvaluating on test set...")
    metrics = evaluate_model(model, X_test, y_test, scaler)
    
    # Save model and scaler
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_data = {
        'model': model,
        'scaler': scaler,
        'metrics': metrics
    }
    joblib.dump(model_data, args.output)
    logger.info(f"Model saved to {args.output}")
    
    # Plot training history
    if args.plot:
        plot_path = str(output_path.with_suffix('.png'))
        plot_training_history(model, save_path=plot_path)
    
    logger.info("\n✅ Training completed successfully!")


if __name__ == '__main__':
    main()

