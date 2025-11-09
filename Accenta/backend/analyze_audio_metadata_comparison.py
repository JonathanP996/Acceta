#!/usr/bin/env python3
"""
Compare metadata between Jonathan's microphone files and regular training files
This will help us understand what normalization is needed
"""

import librosa
import numpy as np
from pathlib import Path
import json
from collections import defaultdict

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")

# Jonathan's microphone files (first 3)
JONATHAN_MIC_FILES = [
    "JonathanEnergetic.mp3",
    "JonathanMonotone.mp3",
    "JonathanMixed.mp3"
]

# Sample of regular English training files
REGULAR_ENGLISH_FILES = [
    "english1.mp3",
    "english2.mp3",
    "english3.mp3",
    "english10.mp3",
    "english20.mp3",
    "english30.mp3",
    "english50.mp3",
    "english100.mp3"
]

def analyze_audio_metadata(file_path):
    """Analyze comprehensive audio metadata"""
    try:
        # Load with original sample rate first
        y_orig, sr_orig = librosa.load(str(file_path), sr=None)
        
        # Load at target rate (44.1kHz)
        y, sr = librosa.load(str(file_path), sr=44100)
        
        duration = len(y) / sr
        
        # Basic stats
        rms = np.sqrt(np.mean(y**2))
        peak = np.max(np.abs(y))
        dynamic_range = peak / (rms + 1e-10)
        
        # Spectral characteristics
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # Noise floor estimation
        frame_length = 2048
        hop_length = 512
        rms_frames = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        noise_floor = np.percentile(rms_frames, 10)
        signal_power = np.mean(rms_frames[rms_frames > noise_floor * 2])
        snr_estimate = 20 * np.log10(signal_power / (noise_floor + 1e-10))
        
        # Frequency content
        fft = np.fft.rfft(y)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(y), 1/sr)
        
        # Energy in different bands
        low_energy = np.sum(magnitude[freqs < 1000]) / np.sum(magnitude)
        mid_energy = np.sum(magnitude[(freqs >= 1000) & (freqs < 4000)]) / np.sum(magnitude)
        high_energy = np.sum(magnitude[freqs >= 4000]) / np.sum(magnitude)
        
        # MFCC characteristics (what the model actually sees)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfccs, axis=1)
        mfcc_std = np.std(mfccs, axis=1)
        
        return {
            'file': file_path.name,
            'original_sr': sr_orig,
            'target_sr': sr,
            'duration': duration,
            'rms': rms,
            'peak': peak,
            'dynamic_range': dynamic_range,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_bandwidth': spectral_bandwidth,
            'zero_crossing_rate': zero_crossing_rate,
            'noise_floor': noise_floor,
            'snr_estimate': snr_estimate,
            'low_energy': low_energy,
            'mid_energy': mid_energy,
            'high_energy': high_energy,
            'mfcc_mean': mfcc_mean.tolist(),
            'mfcc_std': mfcc_std.tolist()
        }
    except Exception as e:
        print(f"Error analyzing {file_path.name}: {e}")
        return None

def main():
    print("=" * 80)
    print("AUDIO METADATA COMPARISON: MIC vs TRAINING FILES")
    print("=" * 80)
    print()
    
    # Analyze Jonathan's mic files
    print("📱 Analyzing Jonathan's microphone files...")
    jonathan_results = []
    for filename in JONATHAN_MIC_FILES:
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            print(f"  Analyzing {filename}...")
            result = analyze_audio_metadata(file_path)
            if result:
                jonathan_results.append(result)
        else:
            print(f"  ⚠️  {filename} not found")
    
    # Analyze regular English files
    print("\n📚 Analyzing regular English training files...")
    regular_results = []
    for filename in REGULAR_ENGLISH_FILES:
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            print(f"  Analyzing {filename}...")
            result = analyze_audio_metadata(file_path)
            if result:
                regular_results.append(result)
        else:
            print(f"  ⚠️  {filename} not found")
    
    if not jonathan_results or not regular_results:
        print("❌ Not enough files analyzed!")
        return
    
    print()
    print("=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    # Calculate averages
    def avg_key(results, key):
        return np.mean([r[key] for r in results])
    
    def std_key(results, key):
        return np.std([r[key] for r in results])
    
    print("\n📊 Key Differences:")
    print("-" * 80)
    
    metrics = [
        ('RMS Level', 'rms'),
        ('Peak Level', 'peak'),
        ('Dynamic Range', 'dynamic_range'),
        ('Spectral Centroid (Hz)', 'spectral_centroid'),
        ('Spectral Rolloff (Hz)', 'spectral_rolloff'),
        ('Spectral Bandwidth (Hz)', 'spectral_bandwidth'),
        ('Zero Crossing Rate', 'zero_crossing_rate'),
        ('Noise Floor', 'noise_floor'),
        ('SNR (dB)', 'snr_estimate'),
        ('Low Freq Energy (<1kHz)', 'low_energy'),
        ('Mid Freq Energy (1-4kHz)', 'mid_energy'),
        ('High Freq Energy (>4kHz)', 'high_energy'),
    ]
    
    print(f"{'Metric':<30} | {'Mic Files':<20} | {'Training Files':<20} | {'Difference':<15}")
    print("-" * 80)
    
    differences = {}
    for label, key in metrics:
        mic_avg = avg_key(jonathan_results, key)
        reg_avg = avg_key(regular_results, key)
        diff = ((mic_avg - reg_avg) / (reg_avg + 1e-10)) * 100
        
        differences[key] = {
            'mic_avg': mic_avg,
            'reg_avg': reg_avg,
            'diff_percent': diff
        }
        
        print(f"{label:<30} | {mic_avg:>18.6f} | {reg_avg:>18.6f} | {diff:>13.1f}%")
    
    # MFCC comparison
    print("\n🎵 MFCC Characteristics (what the model sees):")
    print("-" * 80)
    print("MFCC Coefficient | Mic Mean | Training Mean | Difference")
    print("-" * 80)
    
    mic_mfcc_means = np.mean([np.array(r['mfcc_mean']) for r in jonathan_results], axis=0)
    reg_mfcc_means = np.mean([np.array(r['mfcc_mean']) for r in regular_results], axis=0)
    mfcc_diffs = ((mic_mfcc_means - reg_mfcc_means) / (np.abs(reg_mfcc_means) + 1e-10)) * 100
    
    for i in range(13):
        print(f"MFCC {i+1:2d}            | {mic_mfcc_means[i]:>8.3f} | {reg_mfcc_means[i]:>13.3f} | {mfcc_diffs[i]:>10.1f}%")
    
    # Save results
    output_file = Path(__file__).parent / "audio_metadata_comparison.json"
    
    # Convert all numpy types to Python native types
    def convert_to_native(obj):
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return [convert_to_native(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(x) for x in obj]
        return obj
    
    with open(output_file, 'w') as f:
        json.dump(convert_to_native({
            'jonathan_files': jonathan_results,
            'regular_files': regular_results,
            'differences': differences,
            'mfcc_comparison': {
                'mic_mean': mic_mfcc_means.tolist(),
                'reg_mean': reg_mfcc_means.tolist(),
                'diff_percent': mfcc_diffs.tolist()
            }
        }), f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("NORMALIZATION RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n🔧 Suggested Normalization Steps:")
    if abs(differences['rms']['diff_percent']) > 10:
        print(f"  1. RMS Normalization: Mic files have {differences['rms']['diff_percent']:.1f}% different RMS")
        print(f"     → Normalize mic audio RMS to match training: {differences['reg_avg']['rms']:.6f}")
    
    if abs(differences['spectral_centroid']['diff_percent']) > 10:
        print(f"  2. Spectral Shaping: Mic files have {differences['spectral_centroid']['diff_percent']:.1f}% different spectral centroid")
        print(f"     → Apply EQ to shift frequency response")
    
    if abs(differences['noise_floor']['diff_percent']) > 20:
        print(f"  3. Noise Reduction: Mic files have {differences['noise_floor']['diff_percent']:.1f}% different noise floor")
        print(f"     → Apply noise gate or reduction")
    
    if abs(differences['dynamic_range']['diff_percent']) > 15:
        print(f"  4. Dynamic Range: Mic files have {differences['dynamic_range']['diff_percent']:.1f}% different dynamic range")
        print(f"     → Apply compression/expansion")
    
    print(f"\n  5. MFCC Normalization: Adjust MFCC features to match training distribution")
    print(f"     → Largest differences in: MFCC {np.argmax(np.abs(mfcc_diffs)) + 1} ({mfcc_diffs[np.argmax(np.abs(mfcc_diffs))]:.1f}%)")

if __name__ == "__main__":
    main()

