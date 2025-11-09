#!/usr/bin/env python3
"""
Analyze microphone audio characteristics from Jonathan's custom files
This will help us understand the audio quality differences and create appropriate augmentation
"""

import librosa
import numpy as np
from pathlib import Path
import soundfile as sf

ARCHIVE_DIR = Path("/Users/jsmat/gaTech/AI@GT/archive/recordings/recordings")
JONATHAN_FILES = [
    "JonathanEnergetic.mp3",
    "JonathanMonotone.mp3",
    "JonathanMixed.mp3",
    "JonathanEnergeticPrompt2.mp3",
    "JonathanEnergetic2.mp3"
]

def analyze_audio_characteristics(file_path):
    """Analyze audio characteristics of a file"""
    try:
        # Load audio
        y, sr = librosa.load(str(file_path), sr=None)  # Keep original sample rate
        duration = len(y) / sr
        
        # Basic stats
        rms = np.sqrt(np.mean(y**2))
        peak = np.max(np.abs(y))
        dynamic_range = peak / (rms + 1e-10)
        
        # Spectral characteristics
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # Noise floor estimation (using quiet segments)
        # Take the bottom 10% of RMS values as noise floor
        frame_length = 2048
        hop_length = 512
        rms_frames = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        noise_floor = np.percentile(rms_frames, 10)
        
        # SNR estimation (rough)
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
        
        return {
            'file': file_path.name,
            'sample_rate': sr,
            'duration': duration,
            'rms': rms,
            'peak': peak,
            'dynamic_range': dynamic_range,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'zero_crossing_rate': zero_crossing_rate,
            'noise_floor': noise_floor,
            'snr_estimate': snr_estimate,
            'low_energy': low_energy,
            'mid_energy': mid_energy,
            'high_energy': high_energy
        }
    except Exception as e:
        print(f"Error analyzing {file_path.name}: {e}")
        return None

def main():
    print("=" * 80)
    print("ANALYZING MICROPHONE AUDIO CHARACTERISTICS")
    print("=" * 80)
    print()
    
    results = []
    for filename in JONATHAN_FILES:
        file_path = ARCHIVE_DIR / filename
        if file_path.exists():
            print(f"Analyzing {filename}...")
            result = analyze_audio_characteristics(file_path)
            if result:
                results.append(result)
        else:
            print(f"⚠️  {filename} not found")
    
    if not results:
        print("❌ No files analyzed!")
        return
    
    print()
    print("=" * 80)
    print("CHARACTERISTICS SUMMARY")
    print("=" * 80)
    
    # Calculate averages
    avg_sample_rate = np.mean([r['sample_rate'] for r in results])
    avg_rms = np.mean([r['rms'] for r in results])
    avg_peak = np.mean([r['peak'] for r in results])
    avg_dynamic_range = np.mean([r['dynamic_range'] for r in results])
    avg_spectral_centroid = np.mean([r['spectral_centroid'] for r in results])
    avg_spectral_rolloff = np.mean([r['spectral_rolloff'] for r in results])
    avg_zcr = np.mean([r['zero_crossing_rate'] for r in results])
    avg_noise_floor = np.mean([r['noise_floor'] for r in results])
    avg_snr = np.mean([r['snr_estimate'] for r in results])
    avg_low_energy = np.mean([r['low_energy'] for r in results])
    avg_mid_energy = np.mean([r['mid_energy'] for r in results])
    avg_high_energy = np.mean([r['high_energy'] for r in results])
    
    print(f"\n📊 Average Characteristics:")
    print(f"  Sample Rate: {avg_sample_rate:.0f} Hz")
    print(f"  RMS Level: {avg_rms:.6f}")
    print(f"  Peak Level: {avg_peak:.6f}")
    print(f"  Dynamic Range: {avg_dynamic_range:.2f}")
    print(f"  Spectral Centroid: {avg_spectral_centroid:.1f} Hz")
    print(f"  Spectral Rolloff: {avg_spectral_rolloff:.1f} Hz")
    print(f"  Zero Crossing Rate: {avg_zcr:.6f}")
    print(f"  Noise Floor: {avg_noise_floor:.6f}")
    print(f"  Estimated SNR: {avg_snr:.1f} dB")
    print(f"  Low Freq Energy (<1kHz): {avg_low_energy*100:.1f}%")
    print(f"  Mid Freq Energy (1-4kHz): {avg_mid_energy*100:.1f}%")
    print(f"  High Freq Energy (>4kHz): {avg_high_energy*100:.1f}%")
    
    print("\n📋 Individual File Details:")
    print("-" * 80)
    for r in results:
        print(f"\n{r['file']}:")
        print(f"  SR: {r['sample_rate']:.0f}Hz, Duration: {r['duration']:.2f}s")
        print(f"  RMS: {r['rms']:.6f}, Peak: {r['peak']:.6f}, DR: {r['dynamic_range']:.2f}")
        print(f"  Noise Floor: {r['noise_floor']:.6f}, SNR: {r['snr_estimate']:.1f}dB")
        print(f"  Spectral: Centroid={r['spectral_centroid']:.1f}Hz, Rolloff={r['spectral_rolloff']:.1f}Hz")
    
    # Save results
    import json
    output_file = Path(__file__).parent / "mic_characteristics.json"
    with open(output_file, 'w') as f:
        json.dump({
            'averages': {
                'sample_rate': float(avg_sample_rate),
                'rms': float(avg_rms),
                'peak': float(avg_peak),
                'dynamic_range': float(avg_dynamic_range),
                'spectral_centroid': float(avg_spectral_centroid),
                'spectral_rolloff': float(avg_spectral_rolloff),
                'zero_crossing_rate': float(avg_zcr),
                'noise_floor': float(avg_noise_floor),
                'snr_estimate': float(avg_snr),
                'low_energy': float(avg_low_energy),
                'mid_energy': float(avg_mid_energy),
                'high_energy': float(avg_high_energy)
            },
            'individual': [{k: float(v) if isinstance(v, (np.float32, np.float64)) else v for k, v in r.items()} for r in results]
        }, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()

