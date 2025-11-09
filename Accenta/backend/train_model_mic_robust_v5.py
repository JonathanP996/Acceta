"""
Microphone-Robust Training Script v5

Key changes from v4:
1. Keep ALL English training data (don't reduce by half)
2. Use lighter, more subtle augmentation
3. Include Jonathan files without heavy augmentation
4. Only augment a small percentage of English samples
"""

import os
import re
import numpy as np
import pandas as pd
import librosa
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import pickle
from tqdm import tqdm
from collections import Counter
import random

print("🚀 Starting Microphone-Robust Training (v5 - Conservative Approach)...")

# Configuration
TARGET_SAMPLE_RATE = 44100
N_MFCC = 13
EPOCHS = 250
BATCH_SIZE = 32
RANDOM_STATE = 42
TOP_N_CLASSES = 12
ENGLISH_BOOST_FACTOR = 2.0

# Lighter augmentation parameters (more subtle)
MIC_NOISE_FLOOR = 0.0003  # Reduced from 0.0006 (50% less noise)
MIC_SNR = 45.0  # Increased from 42.0 (better SNR)
AUGMENTATION_PROBABILITY = 0.2  # Only augment 20% of English samples (not 50%)

# Select 12 languages
SELECTED_LANGUAGES = [
    'english',
    'mandarin', 'japanese', 'korean', 'hindi', 'russian',
    'german', 'italian', 'thai', 'turkish', 'malayalam', 'tamil',
]

# Jonathan's microphone files (all English)
JONATHAN_FILES = [
    'JonathanEnergetic.mp3',
    'JonathanMonotone.mp3',
    'JonathanMixed.mp3',
    'JonathanEnergeticPrompt2.mp3',
    'JonathanEnergetic2.mp3'
]

# Paths
AUDIO_DIR = '../../archive/recordings/recordings'
MODEL_PATH = 'models/cnn_tunning.h5'
ENCODER_PATH = 'models/label_encoder.pkl'

def apply_light_mic_augmentation(y, sr, noise_floor=MIC_NOISE_FLOOR, snr_db=MIC_SNR):
    """
    Apply LIGHT microphone-like augmentation (more subtle):
    - Less noise
    - Gentler compression
    - Subtle frequency shaping
    """
    # 1. Add very light noise (reduced noise floor)
    noise_level = noise_floor * (10 ** (snr_db / 20))
    noise = np.random.normal(0, noise_level, len(y))
    y_noisy = y + noise
    
    # 2. Apply very gentle compression (less aggressive)
    threshold = 0.8  # Higher threshold (less compression)
    ratio = 2.0  # Lower ratio (gentler compression)
    compressed = np.copy(y_noisy)
    mask = np.abs(compressed) > threshold
    compressed[mask] = np.sign(compressed[mask]) * (
        threshold + (np.abs(compressed[mask]) - threshold) / ratio
    )
    
    # 3. Very subtle high-frequency rolloff (minimal effect)
    # Just a tiny bit of smoothing
    y_filtered = compressed * 0.95 + np.roll(compressed, 1) * 0.05
    
    # 4. Minimal amplitude variation
    gain_variation = 1.0 + np.random.uniform(-0.02, 0.02)  # Reduced from ±0.05
    y_final = y_filtered * gain_variation
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(y_final))
    if max_val > 0.95:
        y_final = y_final * (0.95 / max_val)
    
    return y_final

def extract_features(audio_file, apply_mic_aug=False):
    """Extract MFCC features with optional light microphone augmentation"""
    y, sr = librosa.load(audio_file, sr=TARGET_SAMPLE_RATE)
    
    # Apply light microphone augmentation if requested
    if apply_mic_aug:
        y = apply_light_mic_augmentation(y, sr)
    
    # Extract the first 5 seconds
    samples_5_sec = TARGET_SAMPLE_RATE * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    
    # Extract MFCC
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    
    # Normalize MFCC
    mfccs_normalized = (mfccs - np.mean(mfccs)) / np.std(mfccs)
    
    return mfccs_normalized

# Step 1: Load audio files
print("\n📂 Step 1: Loading audio files...")
audio_list = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
print(f"Found {len(audio_list)} audio files")

# Extract labels
labels = [re.sub(r'\d+', '', audio[:-4]) for audio in audio_list]

# Count labels
label_counts = Counter(labels)

# Step 2: Filter to selected classes
print(f"\n📊 Step 2: Filtering to {TOP_N_CLASSES} classes...")

available_languages = []
for lang in SELECTED_LANGUAGES:
    if lang in label_counts:
        count = label_counts[lang]
        available_languages.append((lang, count))
    else:
        print(f"⚠️  {lang} not available")

print(f"\nSelected {len(available_languages)} classes:")
for lang, count in available_languages:
    marker = "⭐" if lang == 'english' else "  "
    print(f"{marker} {lang:20s}: {count:4d} samples")

selected_class_names = [lang for lang, _ in available_languages]

# Step 3: Keep ALL English data + add Jonathan files
print("\n📊 Step 3: Keeping ALL English data + adding Jonathan files...")
english_files = [(audio, label) for audio, label in zip(audio_list, labels) 
                 if label == 'english' and audio not in JONATHAN_FILES]
other_files = [(audio, label) for audio, label in zip(audio_list, labels) 
               if label in selected_class_names and label != 'english']

# Add Jonathan files (these are real mic recordings - no augmentation needed)
jonathan_files = [(f, 'english') for f in JONATHAN_FILES if f in audio_list]
print(f"  Keeping all {len(english_files)} English files")
print(f"  Adding {len(jonathan_files)} Jonathan microphone files (no augmentation)")
english_files_final = english_files + jonathan_files

# Combine all files
filtered_data = english_files_final + other_files
print(f"\nTotal files for training: {len(filtered_data)}")
print(f"  English: {len(english_files_final)} ({len(english_files)} original + {len(jonathan_files)} mic files)")
print(f"  Other languages: {len(other_files)}")

# Step 4: Extract features with light augmentation
print("\n🎵 Step 4: Extracting MFCC features with LIGHT augmentation...")
print(f"  Applying light mic augmentation to {AUGMENTATION_PROBABILITY*100:.0f}% of regular English samples...")
print(f"  Jonathan files: NO augmentation (real mic recordings)")

data = []
jonathan_set = set(JONATHAN_FILES)
augmented_count = 0
regular_count = 0

for audio, label in tqdm(filtered_data, desc="Extracting features"):
    audio_path = os.path.join(AUDIO_DIR, audio)
    try:
        # Jonathan files: NO augmentation (they're already real mic recordings)
        # Regular English: only augment 20% of samples (light augmentation)
        is_jonathan = audio in jonathan_set
        apply_aug = (label == 'english') and (not is_jonathan) and (random.random() < AUGMENTATION_PROBABILITY)
        
        if apply_aug:
            augmented_count += 1
        elif label == 'english':
            regular_count += 1
        
        feature = extract_features(audio_path, apply_mic_aug=apply_aug)
        data.append((feature, label))
    except Exception as e:
        print(f"Error processing {audio}: {e}")
        continue

print(f"Successfully processed {len(data)} audio files")
print(f"  English samples: {regular_count} regular, {augmented_count} augmented, {len(jonathan_files)} Jonathan (no aug)")

# Step 5: Convert to DataFrame
print("\n📊 Step 5: Converting to DataFrame...")
separated_data = []
label_arr = []

for f, l in data:
    mfcc_dict = {f'MFCC_{i+1}': np.mean(f[i]) for i in range(f.shape[0])}
    label_arr.append(l)
    separated_data.append(mfcc_dict)

df_new = pd.DataFrame(separated_data)
df_new['label'] = label_arr

print(f"DataFrame shape: {df_new.shape}")

# Step 6: Clean
print("\n🧹 Step 6: Cleaning data...")
df_cleaned = df_new.dropna()
print(f"After cleaning: {len(df_cleaned)} samples")

# Step 7: Balance dataset
print("\n🌈 Step 7: Balancing dataset...")
accent_counts = df_cleaned['label'].value_counts()
print(f"Label distribution:")
print(f"  Min: {accent_counts.min()}, Max: {accent_counts.max()}, Mean: {accent_counts.mean():.1f}")

max_count = accent_counts.max()
target_count = max(int(max_count * 0.8), 100)

# For English, use a moderate target (we have more data now)
english_count = accent_counts.get('english', 0)
if english_count > 0:
    # Don't oversample too much since we have all the data
    english_target = max(int(english_count * 1.1), int(max_count * 0.85))
else:
    english_target = target_count

oversampled_data = []
for accent, count in accent_counts.items():
    accent_data = df_cleaned[df_cleaned['label'] == accent]
    if accent == 'english':
        if count < english_target:
            oversampled_accent = accent_data.sample(n=english_target, replace=True, random_state=RANDOM_STATE)
            oversampled_data.append(oversampled_accent)
        else:
            oversampled_data.append(accent_data)
    else:
        if count < target_count:
            oversampled_accent = accent_data.sample(n=target_count, replace=True, random_state=RANDOM_STATE)
            oversampled_data.append(oversampled_accent)
        else:
            oversampled_data.append(accent_data)

balanced_df = pd.concat(oversampled_data)
df_shuffled = balanced_df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

print(f"After balancing: {len(df_shuffled)} samples")
english_samples = len(df_shuffled[df_shuffled['label'] == 'english'])
print(f"English samples: {english_samples}")
print(f"Classes: {df_shuffled['label'].nunique()}")

# Step 8: Prepare features
print("\n✂️ Step 8: Preparing features...")
X = np.array(df_shuffled.drop('label', axis=1).values)
y = df_shuffled['label'].values

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
y_onehot = to_categorical(y_encoded)

print(f"Features shape: {X.shape}")
print(f"Number of classes: {len(label_encoder.classes_)}")
print(f"Classes: {sorted(label_encoder.classes_)}")

# Compute class weights
class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
class_weight_dict = {}

for i, class_name in enumerate(label_encoder.classes_):
    base_weight = class_weights[i]
    if class_name == 'english':
        boosted_weight = base_weight * ENGLISH_BOOST_FACTOR
        class_weight_dict[i] = boosted_weight
        print(f"English class weight: {base_weight:.4f} -> {boosted_weight:.4f} (boosted {ENGLISH_BOOST_FACTOR}x)")
    else:
        class_weight_dict[i] = base_weight

# Reshape for CNN
X = X.reshape(X.shape[0], X.shape[1], 1)

# Step 9: Split
print("\n📊 Step 9: Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y_onehot, test_size=0.2, random_state=RANDOM_STATE, stratify=y_encoded
)
print(f"Training: {X_train.shape[0]}, Test: {X_test.shape[0]}")

# Step 10: Build model
print("\n🏋️ Step 10: Building model...")

def create_improved_model(input_shape, num_classes):
    model = Sequential()
    
    model.add(Conv1D(filters=64, kernel_size=3, activation='relu', padding='same', input_shape=input_shape))
    model.add(BatchNormalization())
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.3))
    
    model.add(Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.3))
    
    model.add(Conv1D(filters=256, kernel_size=3, activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))
    
    model.add(Flatten())
    
    model.add(Dense(512, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    
    model.add(Dense(256, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    
    model.add(Dense(num_classes, activation='softmax'))
    
    model.compile(
        optimizer=Adam(learning_rate=0.0008),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

input_shape = (X_train.shape[1], 1)
num_classes = y_train.shape[1]

model = create_improved_model(input_shape, num_classes)
print("\nModel architecture:")
model.summary()

# Callbacks
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=20,
    restore_best_weights=True,
    verbose=1
)
reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=7,
    min_lr=1e-6,
    verbose=1
)

# Step 11: Train
print(f"\n🚀 Step 11: Training for up to {EPOCHS} epochs...")
history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_test, y_test),
    callbacks=[early_stop, reduce_lr],
    class_weight=class_weight_dict,
    verbose=1
)

# Step 12: Evaluate
print("\n📈 Step 12: Evaluating model...")
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Loss: {loss:.4f}")
print(f"Test Accuracy: {accuracy*100:.2f}%")

y_pred_probs = model.predict(X_test, verbose=0)
y_pred = np.argmax(y_pred_probs, axis=1)
y_true = np.argmax(y_test, axis=1)

print("\nClassification Report:")
report = classification_report(y_true, y_pred, target_names=label_encoder.classes_, output_dict=True, zero_division=0)
df_report = pd.DataFrame(report).transpose()
df_report = df_report.sort_values('support', ascending=False)
print(df_report.head(20))

if 'english' in label_encoder.classes_:
    eng_idx = list(label_encoder.classes_).index('english')
    eng_precision = report[label_encoder.classes_[eng_idx]]['precision']
    eng_recall = report[label_encoder.classes_[eng_idx]]['recall']
    eng_f1 = report[label_encoder.classes_[eng_idx]]['f1-score']
    eng_support = report[label_encoder.classes_[eng_idx]]['support']
    print(f"\n🎯 English Performance:")
    print(f"  Precision: {eng_precision:.4f} ({eng_precision*100:.2f}%)")
    print(f"  Recall: {eng_recall:.4f} ({eng_recall*100:.2f}%)")
    print(f"  F1-Score: {eng_f1:.4f} ({eng_f1*100:.2f}%)")
    print(f"  Support: {int(eng_support)} samples")

# Step 13: Save
print("\n💾 Step 13: Saving model...")
os.makedirs('models', exist_ok=True)
model.save(MODEL_PATH)
with open(ENCODER_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)

print(f"\n✅ Training complete!")
print(f"Model saved to {MODEL_PATH}")
print(f"Label encoder saved to {ENCODER_PATH}")
print(f"Total classes: {len(label_encoder.classes_)}")

