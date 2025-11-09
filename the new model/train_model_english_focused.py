"""
English-Focused Training Script

Implements all 8 strategies to ensure English is accurately recognized:

1. 15 phonetically distinct classes

2. English oversampling

3. English class weight boost (2x)

4. Longer training (250 epochs)

5. Larger architecture

6. Early stopping with more patience

7. Learning rate reduction

8. Consistent preprocessing

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

print("🚀 Starting English-Focused Training...")

# Configuration
TARGET_SAMPLE_RATE = 44100
N_MFCC = 13
EPOCHS = 250  # More epochs for better learning
BATCH_SIZE = 32
RANDOM_STATE = 42
TOP_N_CLASSES = 15  # Reduced to 15 classes for better English detection
ENGLISH_BOOST_FACTOR = 2.0  # Boost English weight by 2x

# Select 15 languages that are phonetically DISTINCT from English
# This makes it easier for the model to identify English
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
AUDIO_DIR = '../archive/recordings/recordings'
MODEL_PATH = 'cnn_tunning.h5'
ENCODER_PATH = 'label_encoder.pkl'

# Step 1: Load ALL audio files
print("\n📂 Step 1: Loading audio files...")
audio_list = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
print(f"Found {len(audio_list)} audio files")

# Extract labels
labels = [re.sub(r'\d+', '', audio[:-4]) for audio in audio_list]

# Count labels
label_counts = Counter(labels)

# Step 2: Filter to selected 15 classes (phonetically distinct from English)
print(f"\n📊 Step 2: Filtering to {TOP_N_CLASSES} phonetically distinct classes...")

# Check which selected languages are available
available_languages = []
for lang in SELECTED_LANGUAGES:
    if lang in label_counts:
        count = label_counts[lang]
        if count >= 5:
            available_languages.append((lang, count))
        else:
            # Allow languages with fewer samples (will be oversampled)
            print(f"⚠️  {lang} has only {count} samples (will be oversampled)")
            available_languages.append((lang, count))
    else:
        print(f"⚠️  {lang} not available")

print(f"\nSelected {len(available_languages)} classes (phonetically distinct from English):")
for lang, count in available_languages:
    marker = "⭐" if lang == 'english' else "  "
    print(f"{marker} {lang:20s}: {count:4d} samples")

selected_class_names = [lang for lang, _ in available_languages]

# Filter files to only include selected classes
filtered_data = [(audio, label) for audio, label in zip(audio_list, labels) if label in selected_class_names]
print(f"\nUsing {len(filtered_data)} files for training ({len(selected_class_names)} classes)")

# Step 3: Extract features (using librosa to match inference preprocessing)
print("\n🎵 Step 3: Extracting MFCC features...")

def extract_features(audio_file):
    """Extract MFCC features - matches preprocess.py exactly"""
    # Use librosa.load() to match inference preprocessing
    y, sr = librosa.load(audio_file, sr=TARGET_SAMPLE_RATE)
    
    # Extract the first 5 seconds
    samples_5_sec = TARGET_SAMPLE_RATE * 5
    if len(y) > samples_5_sec:
        y = y[:samples_5_sec]
    
    # Extract MFCC
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    
    # Normalize MFCC (CRITICAL - must match inference)
    mfccs_normalized = (mfccs - np.mean(mfccs)) / np.std(mfccs)
    
    return mfccs_normalized

data = []
print("Processing audio files...")
for audio, label in tqdm(filtered_data, desc="Extracting features"):
    audio_path = os.path.join(AUDIO_DIR, audio)
    try:
        feature = extract_features(audio_path)
        data.append((feature, label))
    except Exception as e:
        print(f"Error processing {audio}: {e}")
        continue

print(f"Successfully processed {len(data)} audio files")

# Step 4: Convert to DataFrame
print("\n📊 Step 4: Converting to DataFrame...")
separated_data = []
label_arr = []

for f, l in data:
    mfcc_dict = {f'MFCC_{i+1}': np.mean(f[i]) for i in range(f.shape[0])}
    label_arr.append(l)
    separated_data.append(mfcc_dict)

df_new = pd.DataFrame(separated_data)
df_new['label'] = label_arr

print(f"DataFrame shape: {df_new.shape}")

# Step 5: Clean
print("\n🧹 Step 5: Cleaning data...")
df_cleaned = df_new.dropna()
print(f"After cleaning: {len(df_cleaned)} samples")

# Step 6: Balance dataset with English boost
print("\n🌈 Step 6: Balancing dataset with English boost...")
accent_counts = df_cleaned['label'].value_counts()
print(f"Label distribution:")
print(f"  Min: {accent_counts.min()}, Max: {accent_counts.max()}, Mean: {accent_counts.mean():.1f}")

# Oversample to balance classes
max_count = accent_counts.max()
target_count = max(int(max_count * 0.8), 100)  # 80% of max, or at least 100

# For English, oversample even more (20% boost)
english_count = accent_counts.get('english', 0)
if english_count > 0:
    english_target = max(int(english_count * 1.2), int(max_count * 0.9))  # 20% more or 90% of max
else:
    english_target = target_count

oversampled_data = []
for accent, count in accent_counts.items():
    accent_data = df_cleaned[df_cleaned['label'] == accent]
    if accent == 'english':
        # Special handling for English - oversample more
        if count < english_target:
            oversampled_accent = accent_data.sample(n=english_target, replace=True, random_state=RANDOM_STATE)
            oversampled_data.append(oversampled_accent)
        else:
            oversampled_data.append(accent_data)
    else:
        # Normal oversampling for other classes
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
print(f"Class distribution:")
print(df_shuffled['label'].value_counts())

# Step 7: Prepare features
print("\n✂️ Step 7: Preparing features...")
X = np.array(df_shuffled.drop('label', axis=1).values)
y = df_shuffled['label'].values

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
y_onehot = to_categorical(y_encoded)

print(f"Features shape: {X.shape}")
print(f"Number of classes: {len(label_encoder.classes_)}")
print(f"Classes: {sorted(label_encoder.classes_)}")

# Compute class weights with English boost
class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
class_weight_dict = {}
for i, class_name in enumerate(label_encoder.classes_):
    base_weight = class_weights[i]
    if class_name == 'english':
        # Boost English weight
        boosted_weight = base_weight * ENGLISH_BOOST_FACTOR
        class_weight_dict[i] = boosted_weight
        print(f"English class weight: {base_weight:.4f} -> {boosted_weight:.4f} (boosted {ENGLISH_BOOST_FACTOR}x)")
    else:
        class_weight_dict[i] = base_weight

# Reshape for CNN
X = X.reshape(X.shape[0], X.shape[1], 1)

# Step 8: Split with stratification
print("\n📊 Step 8: Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y_onehot, test_size=0.2, random_state=RANDOM_STATE, stratify=y_encoded
)
print(f"Training: {X_train.shape[0]}, Test: {X_test.shape[0]}")

# Step 9: Build improved model
print("\n🏋️ Step 9: Building improved model...")

def create_improved_model(input_shape, num_classes):
    """
    Improved architecture for English-focused classification:
    - 3 Conv1D layers for better feature extraction
    - Batch normalization for stable training
    - Dropout for regularization
    - Larger dense layers for better classification
    """
    model = Sequential()
    
    # First conv block
    model.add(Conv1D(filters=64, kernel_size=3, activation='relu', padding='same', input_shape=input_shape))
    model.add(BatchNormalization())
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.3))
    
    # Second conv block
    model.add(Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.3))
    
    # Third conv block
    model.add(Conv1D(filters=256, kernel_size=3, activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))
    
    # Flatten
    model.add(Flatten())
    
    # Dense layers
    model.add(Dense(512, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    
    model.add(Dense(256, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    
    # Output layer
    model.add(Dense(num_classes, activation='softmax'))
    
    # Compile with slightly lower learning rate for fine-tuning
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

# Callbacks with more patience for better learning
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=20,  # More patience (increased from 15)
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

# Step 10: Train
print(f"\n🚀 Step 10: Training for up to {EPOCHS} epochs with English focus...")
history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_test, y_test),
    callbacks=[early_stop, reduce_lr],
    class_weight=class_weight_dict,
    verbose=1
)

# Step 11: Evaluate
print("\n📈 Step 11: Evaluating model...")
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
print(df_report.head(20))

# Check English specifically
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

# Step 12: Save
print("\n💾 Step 12: Saving model...")
model.save(MODEL_PATH)
with open(ENCODER_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)

print(f"\n✅ Training complete!")
print(f"Model saved to {MODEL_PATH}")
print(f"Label encoder saved to {ENCODER_PATH}")
print(f"Total classes: {len(label_encoder.classes_)}")
