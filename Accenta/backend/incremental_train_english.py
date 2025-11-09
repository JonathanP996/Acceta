#!/usr/bin/env python3
"""
Incremental Training Script for English Accent Detection

This script:
1. Loads the existing trained model
2. Adds more English files to boost English detection
3. Does incremental training (fine-tuning) with English class weight boost
4. Saves the updated model

This should improve English accent detection accuracy from 69% to higher.
"""

import os
import sys
import re
import random
import numpy as np
import pandas as pd
import librosa
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import pickle
from tqdm import tqdm
from collections import Counter
import shutil

# Import preprocessing function
sys.path.insert(0, str(Path(__file__).parent))
from services.preprocess import preprocess_audio

print("=" * 80)
print("🔄 INCREMENTAL TRAINING - ENGLISH ACCENT DETECTION")
print("=" * 80)

# Configuration
TARGET_SAMPLE_RATE = 44100
N_MFCC = 13
INCREMENTAL_EPOCHS = 50  # More epochs for English improvement
BATCH_SIZE = 32
RANDOM_STATE = 42
LEARNING_RATE = 0.0001  # Lower learning rate for fine-tuning
ENGLISH_BOOST_FACTOR = 5.0  # Boost English weight 5x to prioritize English learning
NUM_ENGLISH_SAMPLES = 200  # More English files for better learning

# Paths
AUDIO_DIR = Path('../../archive/recordings/recordings')
MODEL_PATH = 'models/cnn_tunning.h5'
ENCODER_PATH = 'models/label_encoder.pkl'
BACKUP_MODEL_PATH = 'models/cnn_tunning_backup_english.h5'
BACKUP_ENCODER_PATH = 'models/label_encoder_backup_english.pkl'

def main():
    # Step 1: Backup existing model
    print("\n📦 Step 1: Backing up existing model...")
    if os.path.exists(MODEL_PATH):
        shutil.copy(MODEL_PATH, BACKUP_MODEL_PATH)
        print(f"✅ Model backed up to {BACKUP_MODEL_PATH}")
    if os.path.exists(ENCODER_PATH):
        shutil.copy(ENCODER_PATH, BACKUP_ENCODER_PATH)
        print(f"✅ Encoder backed up to {BACKUP_ENCODER_PATH}")

    # Step 2: Load existing model and encoder
    print("\n📂 Step 2: Loading existing model and encoder...")
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    if not os.path.exists(ENCODER_PATH):
        raise FileNotFoundError(f"Encoder not found: {ENCODER_PATH}")

    model = load_model(MODEL_PATH)
    print(f"✅ Model loaded from {MODEL_PATH}")

    with open(ENCODER_PATH, 'rb') as f:
        label_encoder = pickle.load(f)
    print(f"✅ Label encoder loaded. Classes: {list(label_encoder.classes_)}")

    # Verify English is in the classes
    if 'english' not in label_encoder.classes_:
        raise ValueError("'english' class not found in label encoder!")

    # Step 3: Load additional English files for training
    print(f"\n🎤 Step 3: Loading additional English accent recordings...")
    
    # Find all English files
    all_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    english_files = [f for f in all_files if re.match(r'^english\d+\.mp3$', f, re.IGNORECASE)]
    
    print(f"  Found {len(english_files)} English files in archive")
    
    # Select a diverse set of English files (not just first N)
    # Mix early, middle, and late files for diversity
    if len(english_files) >= NUM_ENGLISH_SAMPLES:
        # Sample from different parts of the list
        sorted_files = sorted(english_files)
        step = len(sorted_files) // NUM_ENGLISH_SAMPLES
        selected_files = sorted_files[::step][:NUM_ENGLISH_SAMPLES]
        print(f"  Selected {len(selected_files)} diverse English files for training")
    else:
        selected_files = english_files
        print(f"  Using all {len(selected_files)} available English files")
    
    english_features = []
    english_labels = []

    for filename in tqdm(selected_files, desc="  Processing English files"):
        file_path = AUDIO_DIR / filename
        if not file_path.exists():
            print(f"⚠️  Warning: {filename} not found, skipping...")
            continue
        
        try:
            # Preprocess using the same function as training
            # These are regular recordings, not microphone recordings
            features = preprocess_audio(str(file_path), is_microphone_recording=False)
            english_features.append(features.flatten())  # Flatten to match training format
            english_labels.append('english')
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue

    if len(english_features) == 0:
        raise ValueError("No English accent files were successfully processed!")

    print(f"\n✅ Successfully processed {len(english_features)} English accent files")

    # Step 4: Load existing training data (for validation)
    print("\n📊 Step 4: Loading sample of existing training data for validation...")
    # Load a sample of existing files to maintain validation set
    audio_list = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3') and not f.startswith('english')]
    labels = [re.sub(r'\d+', '', audio[:-4]) for audio in audio_list]

    # Filter to only classes in the encoder
    valid_files = []
    valid_labels = []
    for audio, label in zip(audio_list, labels):
        if label in label_encoder.classes_:
            valid_files.append(audio)
            valid_labels.append(label)

    # Group files by label and sample at least 2 per class
    random.seed(RANDOM_STATE)
    files_by_label = {}
    for filename, label in zip(valid_files, valid_labels):
        if label not in files_by_label:
            files_by_label[label] = []
        files_by_label[label].append(filename)

    # Sample at least 2 files per class (more for classes with many files)
    sampled_files = []
    sampled_labels = []
    for label, files in files_by_label.items():
        # Sample at least 2, but up to 20 per class to keep it balanced
        sample_size = min(max(2, len(files)), 20)
        sampled = random.sample(files, sample_size)
        sampled_files.extend(sampled)
        sampled_labels.extend([label] * len(sampled))

    print(f"  Loading {len(sampled_files)} existing files for validation...")
    existing_features = []
    existing_labels = []

    for filename, label in tqdm(zip(sampled_files, sampled_labels), total=len(sampled_files), desc="  Processing"):
        file_path = AUDIO_DIR / filename
        try:
            # Regular files, not microphone recordings
            features = preprocess_audio(str(file_path), is_microphone_recording=False)
            existing_features.append(features.flatten())
            existing_labels.append(label)
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue

    print(f"✅ Loaded {len(existing_features)} existing samples")

    # Step 5: Combine data
    print("\n🔄 Step 5: Combining new and existing data...")
    all_features = np.array(english_features + existing_features)
    all_labels = np.array(english_labels + existing_labels)

    print(f"  Total samples: {len(all_features)}")
    print(f"  English samples: {len(english_features)}")
    print(f"  Existing samples: {len(existing_features)}")

    # Encode labels
    y_encoded = label_encoder.transform(all_labels)
    y_onehot = to_categorical(y_encoded, num_classes=len(label_encoder.classes_))

    # Reshape for CNN
    X = all_features.reshape(all_features.shape[0], all_features.shape[1], 1)

    # Step 6: Split data
    print("\n📊 Step 6: Splitting data...")
    # Check if we can use stratified split (need at least 2 samples per class)
    label_counts = Counter(all_labels)
    min_count = min(label_counts.values())

    if min_count >= 2:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_onehot, test_size=0.2, random_state=RANDOM_STATE, stratify=y_encoded
        )
        print(f"  Using stratified split")
    else:
        # Fallback to regular split if some classes have < 2 samples
        print(f"  Warning: Some classes have < 2 samples, using regular split")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_onehot, test_size=0.2, random_state=RANDOM_STATE
        )
    print(f"  Training: {X_train.shape[0]}, Test: {X_test.shape[0]}")

    # Step 7: Compute class weights (boost English significantly)
    print("\n⚖️  Step 7: Computing class weights...")
    class_weights = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
    class_weight_dict = {}

    for i, class_name in enumerate(label_encoder.classes_):
        base_weight = class_weights[i]
        if class_name == 'english':
            # Boost English weight significantly for fine-tuning
            boosted_weight = base_weight * ENGLISH_BOOST_FACTOR
            class_weight_dict[i] = boosted_weight
            print(f"  {class_name:12} | {base_weight:.4f} -> {boosted_weight:.4f} ({ENGLISH_BOOST_FACTOR}x boost)")
        else:
            class_weight_dict[i] = base_weight
            print(f"  {class_name:12} | {base_weight:.4f}")

    # Step 8: Compile model with lower learning rate for fine-tuning
    print("\n🔧 Step 8: Compiling model for fine-tuning...")
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),  # Lower LR for fine-tuning
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    print(f"  Learning rate: {LEARNING_RATE}")

    # Step 9: Setup callbacks
    print("\n⏱️  Step 9: Setting up callbacks...")
    early_stop = EarlyStopping(
        monitor='val_accuracy',  # Monitor accuracy instead of loss
        patience=15,  # Much more patience for incremental training
        restore_best_weights=True,
        verbose=1,
        mode='max'  # Maximize accuracy
    )
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=6,  # More patience before reducing LR
        min_lr=1e-7,
        verbose=1
    )

    # Step 10: Incremental training
    print(f"\n🚀 Step 10: Starting incremental training ({INCREMENTAL_EPOCHS} epochs)...")
    print(f"  This will fine-tune the model on {len(english_features)} additional English recordings")
    print(f"  English class weight boosted {ENGLISH_BOOST_FACTOR}x to prioritize English learning")
    print("  Lower learning rate ensures we don't overwrite existing knowledge\n")

    history = model.fit(
        X_train, y_train,
        epochs=INCREMENTAL_EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_test, y_test),
        callbacks=[early_stop, reduce_lr],
        class_weight=class_weight_dict,
        verbose=1
    )

    # Step 11: Evaluate
    print("\n📈 Step 11: Evaluating fine-tuned model...")
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"  Test Loss: {loss:.4f}")
    print(f"  Test Accuracy: {accuracy*100:.2f}%")

    # Check English performance specifically
    y_pred_probs = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = np.argmax(y_test, axis=1)

    if 'english' in label_encoder.classes_:
        english_idx = list(label_encoder.classes_).index('english')
        english_mask = y_true == english_idx
        if english_mask.sum() > 0:
            english_accuracy = (y_pred[english_mask] == y_true[english_mask]).mean()
            print(f"\n🎯 English Performance:")
            print(f"  English samples in test set: {english_mask.sum()}")
            print(f"  English accuracy: {english_accuracy*100:.2f}%")

    # Step 12: Save updated model
    print("\n💾 Step 12: Saving updated model...")
    os.makedirs('models', exist_ok=True)
    model.save(MODEL_PATH)
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(label_encoder, f)

    print(f"\n✅ Incremental training complete!")
    print(f"  Model saved to {MODEL_PATH}")
    print(f"  Encoder saved to {ENCODER_PATH}")
    print(f"  Backup saved to {BACKUP_MODEL_PATH}")
    print(f"\n  The model has been fine-tuned on {len(english_features)} additional English recordings")
    print(f"  English class weight was boosted {ENGLISH_BOOST_FACTOR}x during training")
    print(f"  This should improve English accent detection accuracy!")

if __name__ == "__main__":
    main()

