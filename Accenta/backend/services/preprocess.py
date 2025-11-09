import numpy as np
import librosa
import soundfile as sf
from scipy.signal import resample, butter, filtfilt
import os

def normalize_microphone_audio(y, sr):
    """
    Normalize microphone audio to fix mic characteristics without forcing English characteristics.
    Based on metadata analysis showing mic files have:
    - Less high-frequency content (needs gentle boost)
    - More low-frequency content (needs gentle reduction)
    
    This function applies GENTLE corrections that work for all languages:
    1. Gentle high-frequency boost (2-8 kHz) - much lighter than before
    2. Gentle low-frequency reduction (< 1 kHz) - much lighter than before
    3. Preserve original RMS level (don't force to English levels)
    """
    nyquist = sr / 2
    
    # Store original RMS to preserve it
    original_rms = np.sqrt(np.mean(y**2))
    
    # 1. Very gentle reduction of low-frequency emphasis (< 1 kHz)
    # Use a very gentle high-pass filter (1st order, lower cutoff)
    low_cutoff_reduce = 600 / nyquist  # Even lower cutoff, very gentle
    b_low, a_low = butter(1, low_cutoff_reduce, btype='high')  # 1st order, gentler
    y_low_filtered = filtfilt(b_low, a_low, y)
    # Mix original with filtered (90% original, 10% filtered) - very gentle reduction
    y = 0.9 * y + 0.1 * y_low_filtered
    
    # 2. Very gentle boost of high-frequencies (2-8 kHz) - minimal
    high_low = 2000 / nyquist
    high_high = 8000 / nyquist
    b_high, a_high = butter(1, [high_low, high_high], btype='band')  # 1st order, gentler
    high_freq_boost = filtfilt(b_high, a_high, y)
    y = y + (high_freq_boost * 0.08)  # Only 8% boost (was 15%) - very minimal
    
    # 3. Restore original RMS level (don't force to English levels)
    current_rms = np.sqrt(np.mean(y**2))
    if current_rms > 0 and original_rms > 0:
        rms_scale = original_rms / current_rms
        y = y * rms_scale
    
    # 4. Prevent clipping (soft limiting)
    max_val = np.max(np.abs(y))
    if max_val > 0.95:  # If close to clipping
        y = y * (0.95 / max_val)
    
    return y

def preprocess_audio(file_path, target_sample_rate=44100, n_mfcc=13, is_microphone_recording=False):
    """
    Preprocess audio file for accent classification.
    EXACTLY matches the preprocess_audio function from the working Flask app.
    Handles various audio formats including webm/ogg from browser recordings.
    
    Args:
        file_path: Path to the audio file
        target_sample_rate: Target sample rate (default 44100)
        n_mfcc: Number of MFCC coefficients (default 13)
        is_microphone_recording: If True, uses high-quality resampling for microphone recordings
    
    Returns:
        Preprocessed MFCC features ready for model prediction
    """
    # Check file extension to determine reading method
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # CRITICAL: Match working Flask app EXACTLY
    # Uses kaiser_best (not kaiser_fast!) for microphone recordings
    if file_ext in ['.webm', '.ogg', '.opus']:
        # Browser recordings - use high-quality resampling (kaiser_best)
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True, res_type='kaiser_best')
    elif file_ext == '.wav' and is_microphone_recording:
        # WAV files from microphone (converted from WebM) - use high-quality resampling
        # This handles sample rate mismatches and conversion artifacts better
        y, sr = librosa.load(file_path, sr=target_sample_rate, mono=True, res_type='kaiser_best')
    else:
        # Match notebook exactly: use librosa.load() which automatically resamples to target_sample_rate
        # Default resampling for MP3 and other file uploads (matches training)
        y, sr = librosa.load(file_path, sr=target_sample_rate)
    
    # Extract the first 5 seconds (matching notebook exactly)
    # This is critical - the model was trained on 5-second clips
    samples_5_sec = target_sample_rate * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    # If audio is shorter than 5 seconds, use all of it
    
    # CRITICAL: Normalize microphone recordings to match training file characteristics
    # This addresses the spectral differences between mic and training files
    # DISABLED: Normalization was causing all inputs to be classified as English
    # The model works better without normalization for microphone recordings
    # if is_microphone_recording:
    #     y = normalize_microphone_audio(y, sr)
    
    # Log audio characteristics for debugging
    if is_microphone_recording:
        import logging
        logger = logging.getLogger(__name__)
        rms = np.sqrt(np.mean(y**2))
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        logger.info(f"🎤 Microphone audio characteristics: RMS={rms:.6f}, Spectral Centroid={spectral_centroid:.1f}Hz, Length={len(y)/sr:.2f}s")
    
    # Extract MFCC (matching notebook exactly)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # REMOVED: MFCC normalization - was causing English misclassification
    # mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    
    # Calculate mean of each MFCC coefficient across time (same as in training)
    mfcc_mean = np.mean(mfcc, axis=1)
    
    # Reshape to match training data format: (1, n_features, 1)
    mfcc_mean = mfcc_mean.reshape(1, -1, 1)
    
    return mfcc_mean

