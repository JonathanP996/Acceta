"""
Train Accent Evaluator Model
Trains a lightweight neural network to predict accent scores from acoustic feature distances
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent))
from models.accent_evaluator import AccentEvaluator, create_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccentDataset(Dataset):
    """Dataset for accent evaluation training"""
    
    def __init__(self, features: np.ndarray, scores: np.ndarray):
        """
        Initialize dataset
        
        Args:
            features: Array of shape (n_samples, 5) with feature distances
            scores: Array of shape (n_samples,) with ground truth scores (0-1)
        """
        self.features = torch.FloatTensor(features)
        self.scores = torch.FloatTensor(scores).unsqueeze(1)  # Add dimension for batch
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.scores[idx]


def load_data(csv_path: str) -> tuple:
    """
    Load training data from CSV
    
    Args:
        csv_path: Path to CSV file with columns: mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff, score
    
    Returns:
        Tuple of (features, scores) as numpy arrays
    """
    logger.info(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Extract features and scores
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
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 200,
    learning_rate: float = 1e-3,
    early_stop_patience: int = 20,
    device: str = 'cpu'
) -> dict:
    """
    Train the model
    
    Args:
        model: AccentEvaluator model
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        num_epochs: Maximum number of epochs
        learning_rate: Learning rate for optimizer
        early_stop_patience: Number of epochs to wait before early stopping
        device: Device to train on ('cpu' or 'cuda')
    
    Returns:
        Dictionary with training history
    """
    model = model.to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'best_val_loss': float('inf'),
        'best_epoch': 0
    }
    
    # Early stopping
    patience_counter = 0
    
    logger.info(f"Starting training on {device}")
    logger.info(f"Training samples: {len(train_loader.dataset)}")
    logger.info(f"Validation samples: {len(val_loader.dataset)}")
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        
        for features, scores in train_loader:
            features = features.to(device)
            scores = scores.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            predictions = model(features)
            loss = criterion(predictions, scores)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for features, scores in val_loader:
                features = features.to(device)
                scores = scores.to(device)
                
                predictions = model(features)
                loss = criterion(predictions, scores)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        
        # Update history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        
        # Check for improvement
        if val_loss < history['best_val_loss']:
            history['best_val_loss'] = val_loss
            history['best_epoch'] = epoch
            patience_counter = 0
        else:
            patience_counter += 1
        
        # Log progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(
                f"Epoch {epoch+1}/{num_epochs} - "
                f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}, "
                f"Best Val Loss: {history['best_val_loss']:.6f} (epoch {history['best_epoch']+1})"
            )
        
        # Early stopping
        if patience_counter >= early_stop_patience:
            logger.info(f"Early stopping at epoch {epoch+1} (no improvement for {early_stop_patience} epochs)")
            break
    
    logger.info(f"Training completed. Best validation loss: {history['best_val_loss']:.6f} at epoch {history['best_epoch']+1}")
    
    return history


def evaluate_model(model: nn.Module, test_loader: DataLoader, device: str = 'cpu') -> dict:
    """
    Evaluate model on test set
    
    Args:
        model: Trained model
        test_loader: DataLoader for test data
        device: Device to evaluate on
    
    Returns:
        Dictionary with evaluation metrics
    """
    model.eval()
    model = model.to(device)
    
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for features, scores in test_loader:
            features = features.to(device)
            scores = scores.to(device)
            
            predictions = model(features)
            
            all_predictions.extend(predictions.cpu().numpy())
            all_targets.extend(scores.cpu().numpy())
    
    all_predictions = np.array(all_predictions).flatten()
    all_targets = np.array(all_targets).flatten()
    
    # Calculate metrics
    mse = np.mean((all_predictions - all_targets) ** 2)
    mae = np.mean(np.abs(all_predictions - all_targets))
    rmse = np.sqrt(mse)
    
    # R-squared
    ss_res = np.sum((all_targets - all_predictions) ** 2)
    ss_tot = np.sum((all_targets - np.mean(all_targets)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    metrics = {
        'mse': float(mse),
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2)
    }
    
    logger.info(f"Test Metrics:")
    logger.info(f"  MSE: {mse:.6f}")
    logger.info(f"  MAE: {mae:.6f}")
    logger.info(f"  RMSE: {rmse:.6f}")
    logger.info(f"  R²: {r2:.4f}")
    
    return metrics


def plot_training_history(history: dict, save_path: str = None):
    """
    Plot training history
    
    Args:
        history: Training history dictionary
        save_path: Path to save plot (optional)
    """
    plt.figure(figsize=(10, 6))
    plt.plot(history['train_loss'], label='Train Loss', alpha=0.7)
    plt.plot(history['val_loss'], label='Validation Loss', alpha=0.7)
    plt.axvline(x=history['best_epoch'], color='r', linestyle='--', label=f'Best Epoch ({history["best_epoch"]+1})')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (MSE)')
    plt.title('Training History')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path)
        logger.info(f"Saved training plot to {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Train Accent Evaluator Model')
    parser.add_argument('--data', type=str, required=True, help='Path to training CSV file')
    parser.add_argument('--output', type=str, default='accent_model.pt', help='Output model path')
    parser.add_argument('--epochs', type=int, default=200, help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--patience', type=int, default=20, help='Early stopping patience')
    parser.add_argument('--test-split', type=float, default=0.2, help='Test set split ratio')
    parser.add_argument('--val-split', type=float, default=0.2, help='Validation set split ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--plot', action='store_true', help='Plot training history')
    parser.add_argument('--device', type=str, default='auto', choices=['auto', 'cpu', 'cuda'], help='Device to use')
    
    args = parser.parse_args()
    
    # Set random seeds for reproducibility
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    
    logger.info(f"Using device: {device}")
    
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
    val_size = args.val_split / (1 - args.test_split)  # Adjust for already split data
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val,
        test_size=val_size,
        random_state=args.seed
    )
    
    logger.info(f"Data splits: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Create datasets
    train_dataset = AccentDataset(X_train, y_train)
    val_dataset = AccentDataset(X_val, y_val)
    test_dataset = AccentDataset(X_test, y_test)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Create model
    model = create_model()
    logger.info(f"Model architecture:\n{model}")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,} (Trainable: {trainable_params:,})")
    
    # Train model
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=args.epochs,
        learning_rate=args.lr,
        early_stop_patience=args.patience,
        device=device
    )
    
    # Load best model (we'll save the current one, which should be close to best)
    # In a production system, you'd save checkpoints during training
    
    # Evaluate on test set
    logger.info("\nEvaluating on test set...")
    metrics = evaluate_model(model, test_loader, device=device)
    
    # Save model and scaler
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model state
    torch.save({
        'model_state_dict': model.state_dict(),
        'scaler_mean': scaler.mean_,
        'scaler_scale': scaler.scale_,
        'input_dim': 5,
        'hidden_dim1': 32,
        'hidden_dim2': 16,
        'metrics': metrics
    }, args.output)
    
    logger.info(f"Model saved to {args.output}")
    
    # Save scaler separately for easy loading
    scaler_path = str(output_path.with_suffix('.scaler.npy'))
    np.save(scaler_path, {
        'mean': scaler.mean_,
        'scale': scaler.scale_
    })
    logger.info(f"Scaler saved to {scaler_path}")
    
    # Plot training history
    if args.plot:
        plot_path = str(output_path.with_suffix('.png'))
        plot_training_history(history, save_path=plot_path)
    
    logger.info("\n✅ Training completed successfully!")


if __name__ == '__main__':
    main()

