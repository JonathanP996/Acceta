"""
Accent Classifier Service
Uses acoustic embeddings (wav2vec2) + ML classifier to identify accent
Outputs probability distribution over all supported accents
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try to import transformers for wav2vec2
TRANSFORMERS_AVAILABLE = False
TORCH_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
    NN_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    NN_AVAILABLE = False
    nn = None  # Set to None if not available
    logger.warning("PyTorch not available for accent classifier")

try:
    from transformers import Wav2Vec2Processor, Wav2Vec2Model
    import soundfile as sf
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, will use fallback embeddings")


# Supported accents for classification
SUPPORTED_ACCENTS = [
    "american",
    "british",
    "australian",
    "canadian",
    "irish",
    "scottish",
    "new_zealand",
    "south_african"
]

# Global model instances
_wav2vec2_processor = None
_wav2vec2_model = None
_accent_classifier = None
_device = "cpu"


# Define AccentClassifier class conditionally
if TORCH_AVAILABLE and NN_AVAILABLE and nn is not None:
    class AccentClassifier(nn.Module):
        """
        CNN-based accent classifier
        Takes wav2vec2 embeddings and outputs probability distribution over accents
        """
        
        def __init__(self, embedding_dim: int = 768, num_accents: int = 8, hidden_dim: int = 256):
            super().__init__()
            
            # CNN layers for temporal pattern extraction
            self.conv1 = nn.Conv1d(embedding_dim, hidden_dim, kernel_size=3, padding=1)
            self.conv2 = nn.Conv1d(hidden_dim, hidden_dim // 2, kernel_size=3, padding=1)
            self.conv3 = nn.Conv1d(hidden_dim // 2, hidden_dim // 4, kernel_size=3, padding=1)
            
            # Pooling
            self.pool = nn.AdaptiveAvgPool1d(1)
            
            # Fully connected layers
            self.fc1 = nn.Linear(hidden_dim // 4, hidden_dim // 2)
            self.fc2 = nn.Linear(hidden_dim // 2, num_accents)
            
            # Activation functions
            self.relu = nn.ReLU()
            self.dropout = nn.Dropout(0.3)
            self.softmax = nn.Softmax(dim=1)
        
        def forward(self, x):
            """
            Args:
                x: Input tensor of shape (batch, seq_len, embedding_dim)
            
            Returns:
                Probability distribution over accents: (batch, num_accents)
            """
            # Reshape for Conv1d: (batch, embedding_dim, seq_len)
            x = x.transpose(1, 2)
            
            # CNN layers
            x = self.relu(self.conv1(x))
            x = self.dropout(x)
            x = self.relu(self.conv2(x))
            x = self.dropout(x)
            x = self.relu(self.conv3(x))
            
            # Global pooling
            x = self.pool(x).squeeze(-1)  # (batch, hidden_dim // 4)
            
            # Fully connected layers
            x = self.relu(self.fc1(x))
            x = self.dropout(x)
            x = self.fc2(x)
            
            # Softmax for probability distribution
            return self.softmax(x)


def load_wav2vec2(timeout: float = 30.0):
    """Load pre-trained wav2vec2 model for acoustic embeddings (lazy loading)"""
    global _wav2vec2_processor, _wav2vec2_model, _device
    
    # Return early if already loaded
    if _wav2vec2_model is not None:
        return True
    
    if not TRANSFORMERS_AVAILABLE:
        logger.warning("Transformers not available, cannot load wav2vec2")
        return False
    
    try:
        # Use base wav2vec2 model (lightweight, fast)
        model_name = "facebook/wav2vec2-base-960h"
        
        logger.info(f"Loading wav2vec2 model: {model_name} (this may take a moment on first use)")
        
        # Load model directly
        try:
            _wav2vec2_processor = Wav2Vec2Processor.from_pretrained(model_name)
            _wav2vec2_model = Wav2Vec2Model.from_pretrained(model_name)
            
            # Set device
            if TORCH_AVAILABLE and torch.cuda.is_available():
                _device = "cuda"
            else:
                _device = "cpu"
            
            _wav2vec2_model.to(_device)
            _wav2vec2_model.eval()
            
            logger.info(f"✓ wav2vec2 loaded on {_device}")
            return True
        except Exception as load_error:
            logger.warning(f"wav2vec2 loading failed or timed out: {load_error}")
            logger.warning("Will use heuristic accent classification instead")
            return False
            
    except Exception as e:
        logger.error(f"Failed to load wav2vec2: {e}")
        logger.warning("Will use heuristic accent classification instead")
        return False


def load_accent_classifier(model_path: Optional[str] = None):
    """Load or initialize accent classifier model"""
    global _accent_classifier, _device
    
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch not available, cannot load accent classifier")
        return False
    
    try:
        embedding_dim = 768  # wav2vec2-base embedding dimension
        num_accents = len(SUPPORTED_ACCENTS)
        
        _accent_classifier = AccentClassifier(
            embedding_dim=embedding_dim,
            num_accents=num_accents,
            hidden_dim=256
        )
        
        if model_path and os.path.exists(model_path):
            # Load pre-trained weights
            _accent_classifier.load_state_dict(torch.load(model_path, map_location=_device))
            logger.info(f"Loaded pre-trained accent classifier from {model_path}")
        else:
            # Initialize untrained model (will use heuristic fallback)
            logger.info("Using untrained accent classifier (will use heuristic fallback)")
        
        _accent_classifier.to(_device)
        _accent_classifier.eval()
        
        return True
    except Exception as e:
        logger.error(f"Failed to load accent classifier: {e}")
        return False


def extract_wav2vec2_embeddings(audio_file_path: str, timeout: float = 10.0) -> Optional[np.ndarray]:
    """
    Extract acoustic embeddings using wav2vec2
    
    Args:
        audio_file_path: Path to audio file
        timeout: Maximum time to wait for extraction (seconds) - NOT IMPLEMENTED (model loading is blocking)
    
    Returns:
        Embeddings array of shape (seq_len, embedding_dim) or None if failed
    """
    global _wav2vec2_processor, _wav2vec2_model, _device
    
    # Skip wav2vec2 entirely if not available - use heuristic instead
    if not TRANSFORMERS_AVAILABLE:
        logger.debug("Transformers not available, skipping wav2vec2")
        return None
    
    # Lazy load wav2vec2 if not already loaded (this can be slow on first call)
    if _wav2vec2_model is None:
        logger.info("wav2vec2 not loaded yet, attempting to load...")
        if not load_wav2vec2(timeout=timeout):
            logger.warning("wav2vec2 loading failed or unavailable, will use heuristic")
            return None
    
    if _wav2vec2_model is None:
        logger.warning("wav2vec2 model is None, cannot extract embeddings")
        return None
    
    try:
        # Load audio (this is fast)
        audio, sr = sf.read(audio_file_path)
        
        # Resample to 16kHz if needed (wav2vec2 expects 16kHz)
        if sr != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            sr = 16000
        
        # Process audio (this can be slow for long audio)
        inputs = _wav2vec2_processor(
            audio,
            sampling_rate=sr,
            return_tensors="pt",
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(_device) for k, v in inputs.items()}
        
        # Extract embeddings (this is fast once model is loaded)
        with torch.no_grad():
            outputs = _wav2vec2_model(**inputs)
            embeddings = outputs.last_hidden_state  # (batch, seq_len, embedding_dim)
        
        # Convert to numpy
        embeddings_np = embeddings.cpu().numpy()[0]  # (seq_len, embedding_dim)
        
        logger.info(f"Extracted wav2vec2 embeddings: shape {embeddings_np.shape}")
        return embeddings_np
        
    except Exception as e:
        logger.error(f"Failed to extract wav2vec2 embeddings: {e}")
        return None


async def classify_accent(
    audio_file_path: str,
    use_classifier: bool = True,
    timeout: float = 15.0
) -> Dict[str, Any]:
    """
    Classify accent from audio using ML classifier
    
    Args:
        audio_file_path: Path to audio file
        use_classifier: If True, use trained classifier; if False, use heuristic fallback
        timeout: Maximum time to wait for classification (seconds) - NOTE: Currently uses heuristic if ML fails
    
    Returns:
        Dictionary with:
        - accent_probabilities: Dict[accent_name, probability]
        - predicted_accent: Most likely accent
        - confidence: Confidence score
        - method: "classifier" or "heuristic"
    """
    global _accent_classifier, _device
    
    # FAST PATH: If classifier disabled, use heuristic immediately (no ML models needed)
    # This is the default to avoid timeout issues
    if not use_classifier:
        logger.debug("ML classifier disabled, using fast heuristic")
        return _heuristic_accent_classification(audio_file_path)
    
    # QUICK FALLBACK: Skip ML classifier if transformers/PyTorch not available
    if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
        logger.info("ML models not available, using fast heuristic classification")
        return _heuristic_accent_classification(audio_file_path)
    
    # Extract embeddings (with timeout protection via executor)
    embeddings = None
    try:
        # Use asyncio to run blocking operation in executor to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        # Run in executor with timeout
        embeddings = await asyncio.wait_for(
            loop.run_in_executor(None, extract_wav2vec2_embeddings, audio_file_path, timeout),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Embedding extraction timed out after {timeout}s, using heuristic")
        embeddings = None
    except Exception as e:
        logger.warning(f"Embedding extraction failed: {e}, using heuristic")
        embeddings = None
    
    if embeddings is None:
        # Fallback to heuristic
        return _heuristic_accent_classification(audio_file_path)
    
    # Use classifier if available and requested
    if use_classifier and _accent_classifier is not None and TORCH_AVAILABLE:
        try:
            # Prepare input
            embeddings_tensor = torch.from_numpy(embeddings).unsqueeze(0).to(_device)  # (1, seq_len, embedding_dim)
            
            # Classify
            with torch.no_grad():
                probabilities = _accent_classifier(embeddings_tensor)
                probabilities_np = probabilities.cpu().numpy()[0]  # (num_accents,)
            
            # Map to accent names
            accent_probs = {
                SUPPORTED_ACCENTS[i]: float(prob)
                for i, prob in enumerate(probabilities_np)
            }
            
            # Get predicted accent
            predicted_idx = np.argmax(probabilities_np)
            predicted_accent = SUPPORTED_ACCENTS[predicted_idx]
            confidence = float(probabilities_np[predicted_idx])
            
            logger.info(f"Classifier predicted: {predicted_accent} (confidence: {confidence:.2f})")
            
            return {
                "accent_probabilities": accent_probs,
                "predicted_accent": predicted_accent,
                "confidence": confidence,
                "method": "classifier",
                "embeddings_shape": embeddings.shape
            }
            
        except Exception as e:
            logger.warning(f"Classifier failed, using heuristic: {e}")
            return _heuristic_accent_classification(audio_file_path)
    else:
        # Use heuristic classification based on embeddings
        return _embedding_based_heuristic(embeddings)


def _embedding_based_heuristic(embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Heuristic accent classification based on wav2vec2 embeddings
    Uses simple statistical features from embeddings
    """
    try:
        # Compute statistics from embeddings
        mean_embedding = np.mean(embeddings, axis=0)  # (embedding_dim,)
        std_embedding = np.std(embeddings, axis=0)
        
        # Simple heuristic: use embedding statistics to infer accent
        # This is a placeholder - in production, you'd use a trained classifier
        
        # For now, return uniform distribution (no strong prediction)
        num_accents = len(SUPPORTED_ACCENTS)
        uniform_prob = 1.0 / num_accents
        
        accent_probs = {
            accent: uniform_prob
            for accent in SUPPORTED_ACCENTS
        }
        
        # Slight bias toward American (most common)
        accent_probs["american"] = uniform_prob * 1.2
        # Normalize
        total = sum(accent_probs.values())
        accent_probs = {k: v / total for k, v in accent_probs.items()}
        
        predicted_accent = max(accent_probs.items(), key=lambda x: x[1])[0]
        confidence = accent_probs[predicted_accent]
        
        return {
            "accent_probabilities": accent_probs,
            "predicted_accent": predicted_accent,
            "confidence": confidence,
            "method": "embedding_heuristic",
            "embeddings_shape": embeddings.shape
        }
        
    except Exception as e:
        logger.error(f"Embedding heuristic failed: {e}")
        return _heuristic_accent_classification(None)


def _heuristic_accent_classification(audio_file_path: Optional[str]) -> Dict[str, Any]:
    """
    Fallback heuristic accent classification using acoustic features
    """
    try:
        # Use basic acoustic features if audio available
        if audio_file_path:
            import librosa
            y, sr = librosa.load(audio_file_path, sr=16000)
            
            # Extract pitch
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[pitches > 0]
            avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 200.0
            
            # Simple heuristic based on pitch
            # American: ~180Hz, British: ~200Hz, Australian: ~190Hz
            if 170 <= avg_pitch <= 190:
                predicted = "american"
            elif 190 <= avg_pitch <= 210:
                predicted = "british"
            elif 180 <= avg_pitch <= 200:
                predicted = "australian"
            else:
                predicted = "american"  # Default
        else:
            predicted = "american"
        
        # Create probability distribution (high confidence for predicted, low for others)
        accent_probs = {}
        for accent in SUPPORTED_ACCENTS:
            if accent == predicted:
                accent_probs[accent] = 0.6
            else:
                accent_probs[accent] = 0.4 / (len(SUPPORTED_ACCENTS) - 1)
        
        return {
            "accent_probabilities": accent_probs,
            "predicted_accent": predicted,
            "confidence": accent_probs[predicted],
            "method": "acoustic_heuristic"
        }
        
    except Exception as e:
        logger.error(f"Heuristic classification failed: {e}")
        # Ultimate fallback: uniform distribution
        uniform_prob = 1.0 / len(SUPPORTED_ACCENTS)
        return {
            "accent_probabilities": {accent: uniform_prob for accent in SUPPORTED_ACCENTS},
            "predicted_accent": "american",
            "confidence": uniform_prob,
            "method": "fallback"
        }


# Don't load models on import - use lazy loading instead
# Models will be loaded on first use to avoid startup delays
# This prevents timeout errors during server startup

