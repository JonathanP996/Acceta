# Accent Evaluator Model - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Generate Training Data

```bash
cd Accenta/backend
python generate_synthetic_data.py --output accent_training_data.csv --samples 1000
```

This creates a CSV with 1000 synthetic samples of feature distances and scores.

### Step 2: Train the Model

```bash
python train_accent_model.py \
    --data accent_training_data.csv \
    --output models/accent_model.pt \
    --epochs 200 \
    --plot
```

This trains the model and saves it to `models/accent_model.pt`.

### Step 3: Test Inference

```bash
python accent_infer.py \
    --model models/accent_model.pt \
    --mfcc-dist 0.12 \
    --pitch-diff 0.05 \
    --formant-diff 0.07 \
    --duration-diff 0.04 \
    --intensity-diff 0.02
```

Expected output: `🎯 Predicted Accent Score: ~85-95/100`

## 📁 Files Created

After training, you'll have:
- `models/accent_model.pt` - Trained model (PyTorch checkpoint)
- `models/accent_model.scaler.npy` - Feature scaler
- `models/accent_model.png` - Training history plot

## 🧪 Example Usage in Python

```python
from accent_infer import AccentScorePredictor

# Load model
predictor = AccentScorePredictor('models/accent_model.pt')

# Predict score
score = predictor.predict_score(
    mfcc_dist=0.15,
    pitch_diff=0.08,
    formant_diff=0.10,
    duration_diff=0.06,
    intensity_diff=0.03,
    scale_to_100=True
)

print(f"Accent Score: {score:.2f}/100")
```

## 📊 Understanding the Features

The model takes 5 normalized feature distances (0-1 range):

1. **mfcc_dist**: How different the spectral shape is (0 = identical, 1 = very different)
2. **pitch_diff**: How different the pitch is (0 = same pitch, 1 = very different)
3. **formant_diff**: How different the vowel quality is (0 = same formants, 1 = very different)
4. **duration_diff**: How different the timing is (0 = same duration, 1 = very different)
5. **intensity_diff**: How different the loudness is (0 = same intensity, 1 = very different)

**Lower distances = Better pronunciation = Higher score**

## 🔧 Training Options

```bash
python train_accent_model.py \
    --data accent_training_data.csv \
    --output models/accent_model.pt \
    --epochs 200 \              # Number of training epochs
    --lr 1e-3 \                 # Learning rate
    --batch-size 32 \           # Batch size
    --patience 20 \              # Early stopping patience
    --test-split 0.2 \          # Test set size (20%)
    --val-split 0.2 \            # Validation set size (20%)
    --plot                       # Generate training plot
```

## 📈 Expected Training Time

- **CPU**: ~30-60 minutes for 1000 samples
- **GPU**: ~5-10 minutes for 1000 samples
- **Colab GPU**: ~5 minutes

## 🎯 Integration with AccentMap

The model can be integrated into the existing pipeline:

1. Extract features using `services/features.py`
2. Compute distances (user vs reference)
3. Use `AccentScorePredictor` for ML-based score
4. Combine with existing heuristic for final score

See `models/example_usage.py` for a complete example.

## 🐛 Troubleshooting

**Error: "Model not found"**
- Make sure you've trained the model first
- Check that `models/accent_model.pt` exists

**Error: "CUDA out of memory"**
- Reduce batch size: `--batch-size 16`
- Use CPU: `--device cpu`

**Low accuracy**
- Generate more training data: `--samples 5000`
- Train longer: `--epochs 500`
- Check data quality

## 📚 Next Steps

1. Collect real training data from user sessions
2. Fine-tune with human-graded examples
3. Add more features (rhythm, stress patterns)
4. Ensemble with existing heuristic scoring

See `models/README.md` for detailed documentation.

