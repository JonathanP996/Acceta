"""
Training script for English-focused accent detection model.
Implements ALL 8 strategies from the training document:
1. 15 phonetically distinct classes
2. English oversampling (694+ samples, 20% more than max)
3. 2x English class weight boost
4. 250 epochs training
5. Larger architecture (3 Conv1D, 2 Dense layers)
6. EarlyStopping with patience=20
7. ReduceLROnPlateau with patience=7
8. Consistent preprocessing (matches preprocess.py exactly)
"""
import os
import re
import numpy as np
import pandas as pd
import librosa
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import pickle
from tqdm import tqdm
from collections import Counter

print("=" * 80)
print("🚀 ENGLISH-FOCUSED ACCENT DETECTION MODEL TRAINING")
print("=" * 80)
print("Implementing all 8 strategies for optimal English detection")
print("=" * 80)

# ============================================================================
# CONFIGURATION (All 8 Strategies)
# ============================================================================

# Strategy 1: 15 Phonetically Distinct Classes
TOP_N_CLASSES = 15

# Strategy 2: English Oversampling Target (20% more than max)
ENGLISH_OVERSAMPLE_FACTOR = 1.2  # 20% more than max count

# Strategy 3: English Class Weight Boost
ENGLISH_BOOST_FACTOR = 2.0  # 2x boost

# Strategy 4: Longer Training
EPOCHS = 250

# Strategy 5: Model Architecture (larger)
# - 3 Conv1D layers (64, 128, 256)
# - 2 Dense layers (512, 256)

# Strategy 6: EarlyStopping
EARLY_STOP_PATIENCE = 20

# Strategy 7: ReduceLROnPlateau
LR_REDUCE_PATIENCE = 7
LR_REDUCE_FACTOR = 0.5

# Strategy 8: Consistent Preprocessing
TARGET_SAMPLE_RATE = 44100
N_MFCC = 13
BATCH_SIZE = 32
RANDOM_STATE = 42

# Select 15 languages that are phonetically DISTINCT from English
SELECTED_LANGUAGES = [
    'english',      # Must include
    'mandarin',     # Tonal, very different phonetic system
    'japanese',     # Different phonetic system
    'korean',       # Different phonetic system  
    'arabic',       # Semitic, very different
    'hindi',        # Indo-Aryan, different
    'russian',      # Slavic, different
    'spanish',      # Romance but still distinct
    'french',       # Romance but distinct
    'german',       # Germanic but distinct accent
    'italian',      # Romance
    'thai',         # Tonal, very different
    'turkish',      # Turkic, different
    'malayalam',    # Dravidian, user has accent in this
    'tamil',        # Dravidian, user has accent in this
]

# Paths
# Audio directory - adjust path as needed
AUDIO_DIR = '../archive/recordings/recordings'  # Relative to "the new model" directory
MODEL_PATH = 'cnn_tunning.h5'
ENCODER_PATH = 'label_encoder.pkl'

# ============================================================================
# STEP 1: Load Audio Files
# ============================================================================
print("\n" + "=" * 80)
print("📂 STEP 1: Loading audio files...")
print("=" * 80)

audio_list = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
print(f"Found {len(audio_list)} audio files")

# Extract labels from filenames
labels = [re.sub(r'\d+', '', audio[:-4]) for audio in audio_list]

# Count labels
label_counts = Counter(labels)
print(f"\nTotal unique labels: {len(label_counts)}")

# ============================================================================
# STEP 2: Filter to 15 Phonetically Distinct Classes
# ============================================================================
print("\n" + "=" * 80)
print(f"📊 STEP 2: Filtering to {TOP_N_CLASSES} phonetically distinct classes...")
print("=" * 80)

# Check which selected languages are available
available_languages = []
for lang in SELECTED_LANGUAGES:
    if lang in label_counts:
        count = label_counts[lang]
        available_languages.append((lang, count))
        print(f"  ✅ {lang:15s}: {count:4d} samples")
    else:
        print(f"  ⚠️  {lang:15s}: NOT FOUND")

# If we don't have 15, fill with top remaining classes
if len(available_languages) < TOP_N_CLASSES:
    remaining = [(name, count) for name, count in label_counts.items() 
                 if name not in [l[0] for l in available_languages] and count >= 5]
    remaining.sort(key=lambda x: -x[1])
    needed = TOP_N_CLASSES - len(available_languages)
    print(f"\n  Adding {needed} additional classes from remaining languages...")
    available_languages.extend(remaining[:needed])

top_class_names = [name for name, count in available_languages[:TOP_N_CLASSES]]

print(f"\n✅ Selected {len(top_class_names)} classes:")
for i, (name, count) in enumerate(available_languages[:TOP_N_CLASSES], 1):
    marker = "⭐" if name == 'english' else "  "
    print(f"  {marker} {i:2d}. {name:15s}: {count:4d} samples")

# Filter files
filtered_data = [(audio, label) for audio, label in zip(audio_list, labels) if label in top_class_names]
print(f"\nUsing {len(filtered_data)} files for training ({len(top_class_names)} classes)")

# ============================================================================
# STEP 3: Extract Features (Strategy 8: Consistent Preprocessing)
# ============================================================================
print("\n" + "=" * 80)
print("🎵 STEP 3: Extracting MFCC features...")
print("=" * 80)
print("ℹ️  Using librosa.load() to match preprocess.py exactly")

def extract_features(audio_file):
    """
    Extract MFCC features - EXACTLY matches preprocess.py
    This ensures training and inference use identical preprocessing.
    """
    # Use librosa.load() - matches preprocess.py exactly
    y, sr = librosa.load(audio_file, sr=TARGET_SAMPLE_RATE)
    
    # Extract the first 5 seconds (matching preprocess.py exactly)
    samples_5_sec = TARGET_SAMPLE_RATE * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    
    # Extract MFCC (matching preprocess.py exactly)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    
    # Normalize MFCC (matching preprocess.py exactly)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    
    # Calculate mean of each MFCC coefficient across time (same as in training)
    mfcc_mean = np.mean(mfcc, axis=1)
    
    return mfcc_mean

data = []
print("\nProcessing audio files...")
for audio, label in tqdm(filtered_data, desc="Extracting features"):
    audio_path = os.path.join(AUDIO_DIR, audio)
    try:
        feature = extract_features(audio_path)
        data.append((feature, label))
    except Exception as e:
        print(f"\n❌ Error processing {audio}: {e}")
        continue

print(f"\n✅ Successfully processed {len(data)} audio files")

# ============================================================================
# STEP 4: Convert to DataFrame
# ============================================================================
print("\n" + "=" * 80)
print("📊 STEP 4: Converting to DataFrame...")
print("=" * 80)

separated_data = []
label_arr = []

for f, l in data:
    mfcc_dict = {f'MFCC_{i+1}': f[i] for i in range(len(f))}
    label_arr.append(l)
    separated_data.append(mfcc_dict)

df_new = pd.DataFrame(separated_data)
df_new['label'] = label_arr

print(f"DataFrame shape: {df_new.shape}")

# ============================================================================
# STEP 5: Clean Data
# ============================================================================
print("\n" + "=" * 80)
print("🧹 STEP 5: Cleaning data...")
print("=" * 80)

df_cleaned = df_new.dropna()
print(f"After cleaning: {len(df_cleaned)} samples")
print(f"\nLabel distribution after cleaning:")
label_dist = df_cleaned['label'].value_counts()
print(label_dist)
print(f"\nNumber of classes after cleaning: {df_cleaned['label'].nunique()}")
print(f"Expected classes: {len(top_class_names)}")
if df_cleaned['label'].nunique() < len(top_class_names):
    missing = set(top_class_names) - set(df_cleaned['label'].unique())
    print(f"\n⚠️  WARNING: Missing classes after cleaning: {missing}")
    print("This may indicate feature extraction issues for some classes.")

# ============================================================================
# STEP 6: Balance Dataset with English Oversampling (Strategy 2)
# ============================================================================
print("\n" + "=" * 80)
print("🌈 STEP 6: Balancing dataset with English oversampling...")
print("=" * 80)
print(f"Strategy: Oversample English to {ENGLISH_OVERSAMPLE_FACTOR*100:.0f}% of max count")

accent_counts = df_cleaned['label'].value_counts()
print(f"\nLabel distribution:")
print(f"  Min: {accent_counts.min()}, Max: {accent_counts.max()}, Mean: {accent_counts.mean():.1f}")

# Strategy 2: Oversample English to 20% more than max
max_count = accent_counts.max()
target_count_others = max(int(max_count * 0.8), 100)
target_count_english = max(int(max_count * ENGLISH_OVERSAMPLE_FACTOR), 694)  # At least 694 as per document

print(f"\nOversampling targets:")
print(f"  English: {target_count_english} samples (20% more than max: {max_count})")
print(f"  Others: {target_count_others} samples (80% of max)")

oversampled_data = []
# Ensure we process ALL classes from top_class_names, not just what's in accent_counts
all_classes_to_process = set(top_class_names) | set(accent_counts.index.tolist())

for accent in sorted(all_classes_to_process):
    if accent not in accent_counts.index:
        print(f"     {accent:15s}: NOT FOUND in cleaned data (skipping)")
        continue
        
    count = accent_counts[accent]
    accent_data = df_cleaned[df_cleaned['label'] == accent]
    
    if len(accent_data) == 0:
        print(f"     {accent:15s}: No data available (skipping)")
        continue
    
    if accent == 'english':
        # Strategy 2: English oversampling to 694+ samples
        if count < target_count_english:
            oversampled_accent = accent_data.sample(
                n=target_count_english, 
                replace=True, 
                random_state=RANDOM_STATE
            )
            print(f"  ⭐ English: {count} → {target_count_english} samples (oversampled)")
        else:
            # If English already has enough, still boost it
            oversampled_accent = accent_data.sample(
                n=int(count * ENGLISH_OVERSAMPLE_FACTOR), 
                replace=True, 
                random_state=RANDOM_STATE
            )
            print(f"  ⭐ English: {count} → {len(oversampled_accent)} samples (boosted)")
        oversampled_data.append(oversampled_accent)
        print(f"     DEBUG: English DataFrame shape: {oversampled_accent.shape}, columns: {list(oversampled_accent.columns)[:3]}...")
    else:
        # Other classes: oversample to target_count_others
        if count < target_count_others:
            oversampled_accent = accent_data.sample(
                n=target_count_others, 
                replace=True, 
                random_state=RANDOM_STATE
            )
            print(f"     {accent:15s}: {count:4d} → {target_count_others:4d} samples")
            print(f"     DEBUG: {accent} DataFrame shape: {oversampled_accent.shape}, columns: {list(oversampled_accent.columns)[:3]}...")
        else:
            oversampled_accent = accent_data
            print(f"     {accent:15s}: {count:4d} → {count:4d} samples (no change)")
            print(f"     DEBUG: {accent} DataFrame shape: {oversampled_accent.shape}, columns: {list(oversampled_accent.columns)[:3]}...")
        oversampled_data.append(oversampled_accent)

print(f"\nDEBUG: Total DataFrames to concat: {len(oversampled_data)}")
for i, df in enumerate(oversampled_data):
    print(f"  DataFrame {i}: shape={df.shape}, labels={df['label'].unique()[:3] if 'label' in df.columns else 'NO LABEL COL'}")
    
balanced_df = pd.concat(oversampled_data, ignore_index=True)
print(f"DEBUG: After concat - shape: {balanced_df.shape}, unique labels: {balanced_df['label'].nunique()}")
print(f"DEBUG: Label distribution:\n{balanced_df['label'].value_counts()}")
df_shuffled = balanced_df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

print(f"\n✅ After balancing: {len(df_shuffled)} samples")
english_count = len(df_shuffled[df_shuffled['label'] == 'english'])
print(f"  ⭐ English samples: {english_count}")
print(f"  📊 Classes: {df_shuffled['label'].nunique()}")

# ============================================================================
# STEP 7: Prepare Features
# ============================================================================
print("\n" + "=" * 80)
print("✂️ STEP 7: Preparing features...")
print("=" * 80)

X = np.array(df_shuffled.drop('label', axis=1).values)
y = df_shuffled['label'].values

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
y_onehot = to_categorical(y_encoded)

print(f"Features shape: {X.shape}")
print(f"Number of classes: {len(label_encoder.classes_)}")
print(f"Classes: {sorted(label_encoder.classes_)}")

# ============================================================================
# STEP 8: Compute Class Weights with English Boost (Strategy 3)
# ============================================================================
print("\n" + "=" * 80)
print("⚖️ STEP 8: Computing class weights with English boost...")
print("=" * 80)

class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
class_weight_dict = {i: weight for i, weight in enumerate(class_weights)}

# Strategy 3: Boost English weight 2x
if 'english' in label_encoder.classes_:
    eng_idx = list(label_encoder.classes_).index('english')
    original_weight = class_weight_dict[eng_idx]
    class_weight_dict[eng_idx] = original_weight * ENGLISH_BOOST_FACTOR
    print(f"  ⭐ English class weight: {original_weight:.4f} → {class_weight_dict[eng_idx]:.4f} (boosted {ENGLISH_BOOST_FACTOR}x)")

# Reshape for CNN
X = X.reshape(X.shape[0], X.shape[1], 1)

# ============================================================================
# STEP 9: Split Data
# ============================================================================
print("\n" + "=" * 80)
print("📊 STEP 9: Splitting data...")
print("=" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_onehot, test_size=0.2, random_state=RANDOM_STATE, stratify=y_encoded
)
print(f"Training: {X_train.shape[0]} samples")
print(f"Test: {X_test.shape[0]} samples")

# ============================================================================
# STEP 10: Build Model (Strategy 5: Larger Architecture)
# ============================================================================
print("\n" + "=" * 80)
print("🏋️ STEP 10: Building improved model architecture...")
print("=" * 80)
print("Strategy 5: 3 Conv1D layers (64, 128, 256) + 2 Dense layers (512, 256)")

def create_improved_model(input_shape, num_classes):
    """
    Strategy 5: Larger architecture for better English detection
    - 3 Conv1D layers (64, 128, 256 filters)
    - BatchNormalization after each Conv1D
    - 2 Dense layers (512, 256)
    - Dropout (0.3-0.5)
    - Softmax output
    
    Note: Input shape is (13, 1) for 13 MFCC features, so we use padding='same'
    to prevent dimension reduction issues.
    """
    model = Sequential([
        # First Conv1D layer - use padding='same' to maintain size
        Conv1D(64, kernel_size=3, activation='relu', padding='same', input_shape=input_shape),
        BatchNormalization(),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),
        
        # Second Conv1D layer - use padding='same'
        Conv1D(128, kernel_size=3, activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),
        
        # Third Conv1D layer - use padding='same'
        Conv1D(256, kernel_size=3, activation='relu', padding='same'),
        BatchNormalization(),
        # No pooling here to avoid making dimensions too small
        Dropout(0.3),
        
        # Flatten
        Flatten(),
        
        # Dense layers
        Dense(512, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        
        Dense(256, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        
        # Output layer
        Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

input_shape = (X_train.shape[1], 1)
num_classes = y_train.shape[1]

model = create_improved_model(input_shape, num_classes)
print("\nModel architecture:")
model.summary()

# ============================================================================
# STEP 11: Setup Callbacks (Strategies 6 & 7)
# ============================================================================
print("\n" + "=" * 80)
print("⏱️ STEP 11: Setting up callbacks...")
print("=" * 80)
print(f"Strategy 6: EarlyStopping (patience={EARLY_STOP_PATIENCE})")
print(f"Strategy 7: ReduceLROnPlateau (patience={LR_REDUCE_PATIENCE}, factor={LR_REDUCE_FACTOR})")

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=EARLY_STOP_PATIENCE,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=LR_REDUCE_FACTOR,
    patience=LR_REDUCE_PATIENCE,
    min_lr=1e-6,
    verbose=1
)

checkpoint = ModelCheckpoint(
    'best_model.h5',
    monitor='val_loss',
    save_best_only=True,
    verbose=1
)

# ============================================================================
# STEP 12: Train Model (Strategy 4: 250 Epochs)
# ============================================================================
print("\n" + "=" * 80)
print(f"🚀 STEP 12: Training for up to {EPOCHS} epochs...")
print("=" * 80)
print("Strategy 4: Longer training (250 epochs)")
print("Strategy 3: English class weight boosted 2x")
print("Strategy 2: English oversampled to 694+ samples")
print("\nStarting training...\n")

history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_test, y_test),
    callbacks=[early_stop, reduce_lr, checkpoint],
    class_weight=class_weight_dict,  # Strategy 3: English-boosted weights
    verbose=1
)

# ============================================================================
# STEP 13: Evaluate Model
# ============================================================================
print("\n" + "=" * 80)
print("📈 STEP 13: Evaluating model...")
print("=" * 80)

loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Loss: {loss:.4f}")
print(f"Test Accuracy: {accuracy*100:.2f}%")

# Detailed evaluation
y_pred_probs = model.predict(X_test, verbose=0)
y_pred = np.argmax(y_pred_probs, axis=1)
y_true = np.argmax(y_test, axis=1)

print("\nClassification Report:")
report = classification_report(y_true, y_pred, target_names=label_encoder.classes_, output_dict=True, zero_division=0)
df_report = pd.DataFrame(report).transpose()
df_report = df_report.sort_values('support', ascending=False)
print(df_report)

# Check English specifically
if 'english' in label_encoder.classes_:
    eng_idx = list(label_encoder.classes_).index('english')
    eng_precision = report[label_encoder.classes_[eng_idx]]['precision']
    eng_recall = report[label_encoder.classes_[eng_idx]]['recall']
    eng_f1 = report[label_encoder.classes_[eng_idx]]['f1-score']
    eng_support = report[label_encoder.classes_[eng_idx]]['support']
    
    print("\n" + "=" * 80)
    print("🎯 ENGLISH PERFORMANCE (Target Metrics)")
    print("=" * 80)
    print(f"  Precision: {eng_precision:.4f} (Target: > 0.90)")
    print(f"  Recall:    {eng_recall:.4f} (Target: > 0.90)")
    print(f"  F1-Score:  {eng_f1:.4f} (Target: > 0.90)")
    print(f"  Support:   {eng_support:.0f} samples")
    
    if eng_recall >= 0.90 and eng_precision >= 0.90:
        print("\n  ✅ English detection meets target metrics!")
    else:
        print("\n  ⚠️  English detection below target metrics")
        print("     Consider: Increasing ENGLISH_BOOST_FACTOR or ENGLISH_OVERSAMPLE_FACTOR")

# Confusion matrix
print("\n" + "=" * 80)
print("📊 Confusion Matrix (Top 5 classes by support):")
print("=" * 80)
cm = confusion_matrix(y_true, y_pred)
top_classes = df_report.head(5).index.tolist()
top_indices = [list(label_encoder.classes_).index(c) for c in top_classes if c in label_encoder.classes_]
print(f"\nClasses: {[label_encoder.classes_[i] for i in top_indices]}")
print(cm[np.ix_(top_indices, top_indices)])

# ============================================================================
# STEP 14: Save Model
# ============================================================================
print("\n" + "=" * 80)
print("💾 STEP 14: Saving model...")
print("=" * 80)

model.save(MODEL_PATH)
with open(ENCODER_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)

print(f"\n✅ Training complete!")
print(f"  Model saved to: {MODEL_PATH}")
print(f"  Label encoder saved to: {ENCODER_PATH}")
print(f"  Total classes: {len(label_encoder.classes_)}")
print(f"  English samples in training: {english_count}")
print(f"  Final test accuracy: {accuracy*100:.2f}%")

print("\n" + "=" * 80)
print("📋 TRAINING SUMMARY")
print("=" * 80)
print("✅ Strategy 1: 15 phonetically distinct classes")
print("✅ Strategy 2: English oversampled to 694+ samples")
print("✅ Strategy 3: English class weight boosted 2x")
print("✅ Strategy 4: Trained for 250 epochs")
print("✅ Strategy 5: Larger architecture (3 Conv1D, 2 Dense)")
print("✅ Strategy 6: EarlyStopping (patience=20)")
print("✅ Strategy 7: ReduceLROnPlateau (patience=7)")
print("✅ Strategy 8: Consistent preprocessing (librosa.load)")
print("=" * 80)

