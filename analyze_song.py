import sys
import numpy as np
import pandas as pd
import librosa
import librosa.display
from scipy.signal import find_peaks

filename = sys.argv[1]

print(f"\nLoading: {filename}")

y, sr = librosa.load(filename, sr=None, mono=True)

duration = librosa.get_duration(y=y, sr=sr)

print(f"Duration: {duration:.2f} sec")

# BPM DETECTION
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
tempo = float(np.atleast_1d(tempo)[0])
print(f"Estimated BPM: {tempo:.1f}")

# RMS ENERGY
rms = librosa.feature.rms(y=y)[0]
avg_rms = np.mean(rms)
peak_rms = np.max(rms)
print(f"Average RMS: {avg_rms:.4f}")
print(f"Peak RMS: {peak_rms:.4f}")

# DYNAMIC RANGE
peak_amplitude = np.max(np.abs(y))
rms_signal = np.sqrt(np.mean(y**2))
crest_factor = peak_amplitude / rms_signal
dynamic_range_db = 20 * np.log10(peak_amplitude / (rms_signal + 1e-9))
print(f"Crest Factor: {crest_factor:.2f}")
print(f"Dynamic Range: {dynamic_range_db:.2f} dB")

# SPECTRAL FEATURES
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
zcr = librosa.feature.zero_crossing_rate(y)[0]
print(f"Spectral Centroid: {np.mean(centroid):.0f} Hz")
print(f"Bandwidth: {np.mean(bandwidth):.0f} Hz")
print(f"Rolloff: {np.mean(rolloff):.0f} Hz")
print(f"Brightness (ZCR): {np.mean(zcr)*100:.1f}/100")

# FREQUENCY BALANCE
S = np.abs(librosa.stft(y))
freqs = librosa.fft_frequencies(sr=sr)
bass_mask = freqs < 250
mid_mask = (freqs >= 250) & (freqs <= 4000)
treble_mask = freqs > 4000
bass_energy = np.sum(S[bass_mask])
mid_energy = np.sum(S[mid_mask])
treble_energy = np.sum(S[treble_mask])
total_energy = bass_energy + mid_energy + treble_energy
bass_pct = bass_energy / total_energy * 100
mid_pct = mid_energy / total_energy * 100
treble_pct = treble_energy / total_energy * 100
print("\nFrequency Balance")
print(f"Bass:   {bass_pct:.1f}%")
print(f"Mid:    {mid_pct:.1f}%")
print(f"Treble: {treble_pct:.1f}%")

# VOCAL PRESENCE ESTIMATION
vocal_mask = (freqs >= 300) & (freqs <= 3500)
vocal_energy = np.sum(S[vocal_mask])
vocal_presence = vocal_energy / np.sum(S) * 100
print(f"\nEstimated Vocal Presence: {vocal_presence:.1f}%")

# HARMONIC / PERCUSSIVE SPLIT
harmonic, percussive = librosa.effects.hpss(y)
harmonic_energy = np.sum(np.abs(harmonic))
percussive_energy = np.sum(np.abs(percussive))
hp_total = harmonic_energy + percussive_energy
harm_pct = harmonic_energy / hp_total * 100
perc_pct = percussive_energy / hp_total * 100
print("\nMix Composition")
print(f"Harmonic:  {harm_pct:.1f}%")
print(f"Percussive:{perc_pct:.1f}%")

# CHROMA DENSITY
chroma = librosa.feature.chroma_stft(y=y, sr=sr)
chroma_density = np.mean(np.sum(chroma, axis=0))
print(f"\nChord Density: {chroma_density:.2f}")

# EMOTIONAL TIMELINE
print("\n" + "="*70)
print("EMOTIONAL / PRODUCTION TIMELINE")
print("="*70)

window_seconds = 5

for start in np.arange(0, duration, window_seconds):
    end = min(start + window_seconds, duration)
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    segment = y[start_sample:end_sample]
    if len(segment) < sr:
        continue
    seg_rms = np.mean(librosa.feature.rms(y=segment))
    seg_centroid = np.mean(librosa.feature.spectral_centroid(y=segment, sr=sr))
    seg_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=segment, sr=sr))

    if seg_rms < avg_rms * 0.7:
        energy_label = "Low"
    elif seg_rms < avg_rms * 1.3:
        energy_label = "Medium"
    else:
        energy_label = "High"

    if seg_centroid < 2000:
        brightness = "Dark"
    elif seg_centroid < 4000:
        brightness = "Balanced"
    else:
        brightness = "Bright"

    if seg_bandwidth < 1500:
        density = "Sparse"
    elif seg_bandwidth < 3000:
        density = "Moderate"
    else:
        density = "Dense"

    print(
        f"{start:5.0f}-{end:5.0f}s | "
        f"{energy_label:6s} | "
        f"{brightness:8s} | "
        f"{density}"
    )

# SECTION DETECTION
print("\n" + "="*70)
print("LIKELY SECTION CHANGES")
print("="*70)

energy_curve = rms
peaks, _ = find_peaks(energy_curve, distance=20, prominence=np.std(energy_curve))
times = librosa.frames_to_time(peaks, sr=sr)

for t in times:
    print(f"Potential transition at {int(t//60)}:{int(t%60):02d}")

# MFCC SIGNATURE
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
mfcc_signature = np.mean(mfcc, axis=1)
print("\nMFCC Signature")
print(mfcc_signature)

# AUTO INTERPRETATION
print("\n" + "="*70)
print("AUTOMATED PRODUCTION NOTES")
print("="*70)

if bass_pct > 40:
    print("- Bass-forward mix")
if vocal_presence > 40:
    print("- Significant vocal content")
if perc_pct > 40:
    print("- Drum-driven arrangement")
if np.mean(centroid) < 2500:
    print("- Dark tonal balance")
if np.mean(centroid) > 5000:
    print("- Bright tonal balance")
if crest_factor < 4:
    print("- Highly compressed modern master")
if crest_factor > 8:
    print("- Dynamic, less-compressed master")
if tempo > 130:
    print("- Fast modern trap / rap tempo range")
if tempo < 90:
    print("- Slow atmospheric tempo range")

print("\nAnalysis Complete.")
