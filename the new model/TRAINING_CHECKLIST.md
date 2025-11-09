# Training Checklist - English-Focused Accent Detection

## 🎯 Quick Start

```bash
cd "the new model"
python train_model_english_focused_v2.py
```

## ✅ Pre-Training Checklist

- [ ] **Audio data available**: Check `./archive/recordings/recordings/` has MP3 files
- [ ] **Dependencies installed**: `pip install tensorflow numpy librosa scikit-learn pandas tqdm`
- [ ] **Python version**: Python 3.11 or 3.12 (TensorFlow compatibility)
- [ ] **Disk space**: At least 500MB free (for model file)
- [ ] **Time**: Training takes 2-4 hours depending on hardware

## 📋 All 8 Strategies Implemented

### ✅ Strategy 1: 15 Phonetically Distinct Classes
- **Status**: ✅ Implemented
- **Classes**: english, mandarin, japanese, korean, arabic, hindi, russian, spanish, french, german, italian, thai, turkish, malayalam, tamil
- **Why**: Fewer classes = clearer decision boundaries

### ✅ Strategy 2: English Oversampling (694+ samples)
- **Status**: ✅ Implemented
- **Target**: 20% more than max count (minimum 694)
- **Code**: `ENGLISH_OVERSAMPLE_FACTOR = 1.2`
- **Why**: More English examples = better learning

### ✅ Strategy 3: English Class Weight Boost (2x)
- **Status**: ✅ Implemented
- **Boost**: 2.0x (English misclassifications penalized 2x more)
- **Code**: `ENGLISH_BOOST_FACTOR = 2.0`
- **Why**: Forces model to learn English better

### ✅ Strategy 4: Longer Training (250 epochs)
- **Status**: ✅ Implemented
- **Epochs**: 250
- **Code**: `EPOCHS = 250`
- **Why**: More time to learn English patterns

### ✅ Strategy 5: Larger Architecture
- **Status**: ✅ Implemented
- **Architecture**:
  - 3 Conv1D layers (64, 128, 256 filters)
  - BatchNormalization after each Conv1D
  - 2 Dense layers (512, 256)
  - Dropout (0.3-0.5)
- **Why**: More capacity = better pattern learning

### ✅ Strategy 6: EarlyStopping (patience=20)
- **Status**: ✅ Implemented
- **Patience**: 20 epochs
- **Code**: `EARLY_STOP_PATIENCE = 20`
- **Why**: Allows longer training without overfitting

### ✅ Strategy 7: ReduceLROnPlateau (patience=7)
- **Status**: ✅ Implemented
- **Patience**: 7 epochs
- **Factor**: 0.5 (reduce LR by 50%)
- **Code**: `LR_REDUCE_PATIENCE = 7`
- **Why**: Fine-tunes model gradually

### ✅ Strategy 8: Consistent Preprocessing
- **Status**: ✅ Implemented
- **Method**: `librosa.load()` (matches `preprocess.py` exactly)
- **Sample Rate**: 44100 Hz
- **MFCC**: 13 coefficients
- **Why**: Training and inference must match exactly

## 📊 Expected Results

After training with all 8 strategies:

- **English Accuracy**: 95%+ on test set
- **English Recall**: 90%+ (correctly identifies English when it's English)
- **English Precision**: 90%+ (when it says English, it's usually correct)
- **Overall Accuracy**: 95%+ across all 15 classes

## 🔍 Post-Training Verification

After training completes, verify:

1. **Model file created**: `cnn_tunning.h5` exists
2. **Encoder file created**: `label_encoder.pkl` exists
3. **English metrics**: Check console output for English precision/recall
4. **Test accuracy**: Should be > 95%

## 🚨 Troubleshooting

### Issue: English accuracy still low (< 90%)

**Solutions:**
1. Increase `ENGLISH_BOOST_FACTOR` to 3.0 or 4.0
2. Increase `ENGLISH_OVERSAMPLE_FACTOR` to 1.5 (50% more)
3. Add more English training data
4. Increase `EPOCHS` to 300

### Issue: Model overfitting

**Solutions:**
1. Increase Dropout (0.3 → 0.4, 0.5 → 0.6)
2. Reduce model size slightly
3. Add more data augmentation

### Issue: Training too slow

**Solutions:**
1. Reduce `EPOCHS` to 200 (still good)
2. Reduce `BATCH_SIZE` to 16 (if memory issues)
3. Use GPU if available

### Issue: Inference doesn't match training accuracy

**Solutions:**
1. Verify `preprocess.py` matches training preprocessing exactly
2. Check sample rate is 44100 Hz
3. Ensure MFCC normalization matches

## 📁 Files Created

After training:
- `cnn_tunning.h5` - Trained model (50-100MB)
- `label_encoder.pkl` - Label encoder
- `best_model.h5` - Best model checkpoint (if early stopping triggered)

## 🔄 Next Steps After Training

1. **Copy model files** to `Accenta/backend/models/`:
   ```bash
   cp cnn_tunning.h5 Accenta/backend/models/
   cp label_encoder.pkl Accenta/backend/models/
   ```

2. **Restart backend** to load new model:
   ```bash
   cd Accenta/backend
   python -m uvicorn app:app --reload
   ```

3. **Test with archive files**:
   ```bash
   python test_accent_detector.py --languages english --sample-size 30
   ```

4. **Test with browser recordings** (record your voice and check detection)

## 📝 Key Parameters Reference

```python
TOP_N_CLASSES = 15
ENGLISH_OVERSAMPLE_FACTOR = 1.2  # 20% more than max
ENGLISH_BOOST_FACTOR = 2.0       # 2x class weight boost
EPOCHS = 250                     # Longer training
EARLY_STOP_PATIENCE = 20        # More patience
LR_REDUCE_PATIENCE = 7           # Learning rate reduction
TARGET_SAMPLE_RATE = 44100       # Consistent preprocessing
N_MFCC = 13                      # Consistent preprocessing
```

## ✅ Success Criteria

Training is successful if:
- [ ] English precision > 90%
- [ ] English recall > 90%
- [ ] Overall test accuracy > 95%
- [ ] Model file created and loads without errors
- [ ] Inference matches training accuracy

---

**Last Updated**: After implementing all 8 strategies
**Script**: `train_model_english_focused_v2.py`

