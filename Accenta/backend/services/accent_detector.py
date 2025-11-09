"""
Accent Detection Module
Use this module to integrate accent detection into your app.

Example usage:
    from services.accent_detector import AccentDetector
    
    detector = AccentDetector()
    result = detector.predict('path/to/audio.mp3')
    print(f"Accent: {result['accent']}, Confidence: {result['confidence']}%")
"""

import os
import numpy as np
import pickle
from pathlib import Path
from tensorflow.keras.models import load_model
from .preprocess import preprocess_audio


class AccentDetector:
    """Accent detection class for easy integration"""
    
    def __init__(self, model_path=None, encoder_path=None):
        """
        Initialize the accent detector.
        
        Args:
            model_path: Path to the trained model file (cnn_tunning.h5)
                      If None, will look in backend/models/
            encoder_path: Path to the label encoder file (label_encoder.pkl)
                         If None, will look in backend/models/
        """
        self.model = None
        self.label_encoder = None
        
        # Set default paths relative to backend directory
        if model_path is None:
            # backend/services/accent_detector.py -> backend/services -> backend -> backend/models
            backend_dir = Path(__file__).parent.parent
            model_path = backend_dir / "models" / "cnn_tunning.h5"
        
        if encoder_path is None:
            backend_dir = Path(__file__).parent.parent
            encoder_path = backend_dir / "models" / "label_encoder.pkl"
        
        self.model_path = str(model_path)
        self.encoder_path = str(encoder_path)
        
        self._load_model()
        self._load_encoder()
    
    def _load_model(self):
        """Load the trained model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                "Please ensure the model file is in the correct location."
            )
        self.model = load_model(self.model_path)
        print(f"✅ Model loaded from {self.model_path}")
    
    def _load_encoder(self):
        """Load the label encoder"""
        if not os.path.exists(self.encoder_path):
            raise FileNotFoundError(
                f"Label encoder file not found: {self.encoder_path}\n"
                "Please ensure the encoder file is in the correct location."
            )
        with open(self.encoder_path, 'rb') as f:
            self.label_encoder = pickle.load(f)
        print(f"✅ Label encoder loaded. Classes: {list(self.label_encoder.classes_)}")
    
    def predict(self, audio_path, top_n=3, is_microphone_recording=False):
        """
        Predict accent from an audio file.
        
        Args:
            audio_path: Path to the audio file (mp3, wav, m4a, flac, webm, ogg, opus)
            top_n: Number of top predictions to return (default: 3)
            is_microphone_recording: If True, uses high-quality resampling for microphone recordings
        
        Returns:
            dict with keys:
                - accent: Predicted accent name
                - confidence: Confidence percentage (0-100)
                - top_n: List of top N predictions with confidence scores
        """
        if self.model is None or self.label_encoder is None:
            raise RuntimeError("Model or encoder not loaded. Call __init__ first.")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Preprocess audio (pass is_microphone_recording flag for proper resampling)
        audio_data = preprocess_audio(audio_path, is_microphone_recording=is_microphone_recording)
        
        # Make prediction
        predictions = self.model.predict(audio_data, verbose=0)
        predicted_class_idx = np.argmax(predictions, axis=1)[0]
        confidence = float(predictions[0][predicted_class_idx] * 100)
        predicted_class = self.label_encoder.classes_[predicted_class_idx]
        
        # Get top N predictions
        top_n_indices = np.argsort(predictions[0])[-top_n:][::-1]
        top_n_predictions = []
        for idx in top_n_indices:
            class_name = self.label_encoder.classes_[idx]
            top_n_predictions.append({
                'accent': class_name,
                'confidence': float(predictions[0][idx] * 100)
            })
        
        return {
            'accent': predicted_class,
            'confidence': round(confidence, 2),
            'top_n': top_n_predictions
        }
    
    def get_supported_classes(self):
        """Get list of supported accent classes"""
        if self.label_encoder is None:
            return []
        return list(self.label_encoder.classes_)
    
    def predict_from_bytes(self, audio_bytes, file_extension='.mp3', is_microphone_recording=False):
        """
        Predict accent from audio bytes (useful for web uploads).
        
        Args:
            audio_bytes: Audio file as bytes
            file_extension: File extension (e.g., '.mp3', '.wav', '.webm')
            is_microphone_recording: If True, uses high-quality resampling for microphone recordings
        
        Returns:
            Same as predict() method
        """
        import tempfile
        
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Pass is_microphone_recording flag for proper preprocessing
            result = self.predict(tmp_path, is_microphone_recording=is_microphone_recording)
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        return result

