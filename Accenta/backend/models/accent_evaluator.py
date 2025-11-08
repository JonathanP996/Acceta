"""
Accent Evaluator Model Architecture
Lightweight neural network for predicting accent scores from acoustic feature distances
"""

import torch
import torch.nn as nn


class AccentEvaluator(nn.Module):
    """
    Simple regression network that predicts accent score (0-1) from feature distances.
    
    Input features (5 dimensions):
    - mfcc_dist: Distance in MFCC space (normalized)
    - pitch_diff: Pitch difference (normalized)
    - formant_diff: Formant difference (normalized)
    - duration_diff: Duration difference (normalized)
    - intensity_diff: Intensity difference (normalized)
    
    Output:
    - Score between 0 and 1 (can be scaled to 0-100)
    """
    
    def __init__(self, input_dim: int = 5, hidden_dim1: int = 32, hidden_dim2: int = 16):
        """
        Initialize the model
        
        Args:
            input_dim: Number of input features (default: 5)
            hidden_dim1: Size of first hidden layer (default: 32)
            hidden_dim2: Size of second hidden layer (default: 16)
        """
        super(AccentEvaluator, self).__init__()
        
        self.net = nn.Sequential(
            # Input layer
            nn.Linear(input_dim, hidden_dim1),
            nn.ReLU(),
            nn.Dropout(0.1),  # Small dropout for regularization
            
            # First hidden layer
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            # Output layer (single value, 0-1)
            nn.Linear(hidden_dim2, 1),
            nn.Sigmoid()  # Ensures output is between 0 and 1
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input tensor of shape (batch_size, input_dim)
        
        Returns:
            Tensor of shape (batch_size, 1) with scores between 0 and 1
        """
        return self.net(x)
    
    def predict_score(self, features: list[float], scale_to_100: bool = True) -> float:
        """
        Predict accent score from feature list
        
        Args:
            features: List of 5 feature values [mfcc_dist, pitch_diff, formant_diff, duration_diff, intensity_diff]
            scale_to_100: If True, scale output to 0-100 range (default: True)
        
        Returns:
            Predicted accent score (0-1 or 0-100)
        """
        self.eval()  # Set to evaluation mode
        
        with torch.no_grad():
            # Convert to tensor
            x = torch.tensor([features], dtype=torch.float32)
            
            # Predict
            output = self.forward(x)
            score = output.item()
            
            # Scale to 0-100 if requested
            if scale_to_100:
                score = score * 100.0
            
            return score


def create_model(input_dim: int = 5, hidden_dim1: int = 32, hidden_dim2: int = 16) -> AccentEvaluator:
    """
    Factory function to create a new model instance
    
    Args:
        input_dim: Number of input features
        hidden_dim1: Size of first hidden layer
        hidden_dim2: Size of second hidden layer
    
    Returns:
        New AccentEvaluator model
    """
    return AccentEvaluator(input_dim=input_dim, hidden_dim1=hidden_dim1, hidden_dim2=hidden_dim2)

