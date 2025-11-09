import numpy as np
import librosa
import soundfile as sf
from scipy.signal import resample
import os

def preprocess_audio(file_path, target_sample_rate=44100, n_mfcc=13):
    """
    Preprocess audio file for accent classification.
    EXACTLY matches the preprocess_audio function from the notebook (Cell with inference function).
    Handles various audio formats including webm/ogg from browser recordings.
    
    Args:
        file_path: Path to the audio file
        target_sample_rate: Target sample rate (default 44100)
        n_mfcc: Number of MFCC coefficients (default 13)
    
    Returns:
        Preprocessed MFCC features ready for model prediction
    """
    # Check file extension to determine reading method
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # For webm/ogg/opus files (browser recordings), use librosa directly
    # For other formats, match the notebook exactly: use librosa.load() which auto-resamples
    if file_ext in ['.webm', '.ogg', '.opus']:
        # Browser recordings - librosa handles these formats
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True, res_type='kaiser_fast')
    else:
        # Match notebook exactly: use librosa.load() which automatically resamples to target_sample_rate
        # This is what the notebook's preprocess_audio function does
        y, sr = librosa.load(file_path, sr=target_sample_rate)
    
    # Extract the first 5 seconds (matching notebook exactly)
    samples_5_sec = target_sample_rate * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    
    # Extract MFCC (matching notebook exactly)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # Normalize MFCC (matching notebook exactly)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    
    # Calculate mean of each MFCC coefficient across time (same as in training)
    mfcc_mean = np.mean(mfcc, axis=1)
    
    # Reshape to match training data format: (1, n_features, 1)
    mfcc_mean = mfcc_mean.reshape(1, -1, 1)
    
    return mfcc_mean

