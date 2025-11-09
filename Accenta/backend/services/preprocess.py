import numpy as np
import librosa
import soundfile as sf
from scipy.signal import resample
import os

def preprocess_audio(file_path, target_sample_rate=44100, n_mfcc=13, min_duration=0.5):
    """
    Preprocess audio file for accent classification.
    Improved version with better normalization and duration handling.
    Handles various audio formats including webm/ogg from browser recordings.
    
    Args:
        file_path: Path to the audio file
        target_sample_rate: Target sample rate (default 44100)
        n_mfcc: Number of MFCC coefficients (default 13)
        min_duration: Minimum audio duration in seconds (default 1.0)
        max_duration: Maximum audio duration to use in seconds (default 10.0)
    
    Returns:
        Preprocessed MFCC features ready for model prediction
    """
    # Check file extension to determine reading method
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # For webm/ogg/opus files (browser recordings), use high-quality resampling
    # CRITICAL: Also treat .wav files that are small or named "recording.wav" as browser recordings
    # (These are converted from WebM in the browser and need better resampling)
    is_browser_recording = (
        file_ext in ['.webm', '.ogg', '.opus'] or
        (file_ext == '.wav' and ('recording' in os.path.basename(file_path).lower() or 
                                 os.path.getsize(file_path) < 500000))  # Small WAV = likely browser recording
    )
    
    if is_browser_recording:
        # Browser recordings - use high-quality resampling for better accuracy
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True, res_type='kaiser_best')
    else:
        # Match notebook exactly: use librosa.load() which automatically resamples to target_sample_rate
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True)
    
    # Validate minimum duration
    duration = len(y) / sr
    if duration < min_duration:
        raise ValueError(f"Audio too short: {duration:.2f}s (minimum: {min_duration}s)")
    
    # Extract the first 5 seconds (matching original training exactly)
    # This is critical - the model was trained on 5-second clips
    samples_5_sec = target_sample_rate * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    # If audio is shorter than 5 seconds, use all of it
    
    # Extract MFCC (matching original training parameters)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # Normalize MFCC (matching original, but with safety check)
    mfcc_mean_global = np.mean(mfcc)
    mfcc_std_global = np.std(mfcc)
    
    # Add small epsilon to prevent division by zero
    epsilon = 1e-8
    if mfcc_std_global < epsilon:
        mfcc_std_global = epsilon
    
    # Normalize globally (matching original training)
    mfcc_normalized = (mfcc - mfcc_mean_global) / mfcc_std_global
    
    # Calculate mean of each MFCC coefficient across time (same as in training)
    mfcc_mean_final = np.mean(mfcc_normalized, axis=1)
    
    # Handle any NaN or Inf values (safety check)
    mfcc_mean_final = np.nan_to_num(mfcc_mean_final, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Reshape to match training data format: (1, n_features, 1)
    mfcc_mean_final = mfcc_mean_final.reshape(1, -1, 1)
    
    return mfcc_mean_final

