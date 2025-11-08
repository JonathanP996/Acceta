# Accent Evaluator Model

Lightweight neural network for predicting accent scores from acoustic feature distances.

## Overview

The `AccentEvaluator` model is a simple regression network that takes 5 normalized feature distances as input and predicts an accent score between 0-1 (or 0-100 when scaled).

### Input Features (5 dimensions)
- `mfcc_dist`: Distance in MFCC space (normalized 0-1)
- `pitch_diff`: Pitch difference (normalized 0-1)
- `formant_diff`: Formant difference (normalized 0-1)
- `duration_diff`: Duration difference (normalized 0-1)
- `intensity_diff`: Intensity difference (normalized 0-1)

### Output
- Score between 0 and 1 (can be scaled to 0-100)
- Higher score = better accent match
- Lower score = greater accent deviation

## Architecture

```
Input (5) → Linear(32) → ReLU → Dropout(0.1)
         → Linear(16) → ReLU → Dropout(0.1)
         → Linear(1) → Sigmoid
         → Output (0-1)
```

**Total Parameters**: ~1,200 (very lightweight!)

## Usage

### 1. Generate Synthetic Training Data

```bash
python generate_synthetic_data.py --output accent_training_data.csv --samples 1000
```

### 2. Train the Model

```bash
python train_accent_model.py \
    --data accent_training_data.csv \
    --output models/accent_model.pt \
    --epochs 200 \
    --lr 1e-3 \
    --batch-size 32 \
    --plot
```

### 3. Use for Inference

```python
from accent_infer import AccentScorePredictor

# Load model
predictor = AccentScorePredictor('models/accent_model.pt')

# Predict score
score = predictor.predict_score(
    mfcc_dist=0.12,
    pitch_diff=0.05,
    formant_diff=0.07,
    duration_diff=0.04,
    intensity_diff=0.02,
    scale_to_100=True
)

print(f"Accent Score: {score:.2f}/100")
```

Or from command line:

```bash
python accent_infer.py \
    --model models/accent_model.pt \
    --mfcc-dist 0.12 \
    --pitch-diff 0.05 \
    --formant-diff 0.07 \
    --duration-diff 0.04 \
    --intensity-diff 0.02
```

## Integration with AccentMap

The model can be integrated into the existing accent evaluation pipeline:

1. Extract acoustic features using `services/features.py`
2. Compute feature distances (user vs reference)
3. Use `AccentScorePredictor` to get ML-based score
4. Combine with existing probabilistic heuristic for final score

## Training Tips

- **Data**: Start with 1k synthetic samples, expand with real data
- **Training Time**: < 1 hour on CPU, < 10 minutes on GPU
- **Early Stopping**: Model uses patience=20 epochs
- **Validation**: 20% of data held out for validation
- **Test**: 20% of data held out for final evaluation

## Model Files

- `accent_model.pt`: Saved model state (PyTorch checkpoint)
- `accent_model.scaler.npy`: Feature scaler (for normalization)
- `accent_model.png`: Training history plot (if --plot flag used)

## Future Enhancements

- Collect real training data from user sessions
- Fine-tune with human-graded examples
- Add more features (rhythm, stress patterns)
- Ensemble with existing heuristic scoring

