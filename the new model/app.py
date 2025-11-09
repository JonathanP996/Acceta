from flask import Flask, render_template, request, jsonify
import os
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder
from preprocess import preprocess_audio
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'flac', 'webm', 'ogg', 'opus'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables for model and label encoder
model = None
label_encoder = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_model_and_encoder():
    """Load the trained model and label encoder"""
    global model, label_encoder
    
    # Try to load the model (user will need to train it first or provide it)
    model_path = 'cnn_tunning.h5'
    if os.path.exists(model_path):
        model = load_model(model_path)
        print(f"Model loaded from {model_path}")
    else:
        print(f"Warning: Model file {model_path} not found. Please train the model first.")
        model = None
    
    # Try to load the label encoder
    encoder_path = 'label_encoder.pkl'
    if os.path.exists(encoder_path):
        with open(encoder_path, 'rb') as f:
            label_encoder = pickle.load(f)
        print(f"Label encoder loaded from {encoder_path}")
        print(f"Classes: {label_encoder.classes_}")
    else:
        print(f"Warning: Label encoder file {encoder_path} not found.")
        print("You can create it by running: python save_label_encoder.py")
        label_encoder = None

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle audio file upload and prediction"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload MP3, WAV, M4A, or FLAC files.'}), 400
    
    if model is None:
        return jsonify({'error': 'Model not loaded. Please train the model first.'}), 500
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Preprocess the audio
        audio_data = preprocess_audio(filepath)
        
        # Make prediction
        predictions = model.predict(audio_data, verbose=0)
        predicted_class_idx = np.argmax(predictions, axis=1)[0]
        confidence = float(predictions[0][predicted_class_idx] * 100)
        
        # Get class name (if label encoder is available)
        if label_encoder is not None and hasattr(label_encoder, 'classes_'):
            predicted_class = label_encoder.classes_[predicted_class_idx]
        else:
            # Fallback: use index if label encoder not available
            predicted_class = f"Class {predicted_class_idx}"
        
        # Get top 3 predictions
        top_3_indices = np.argsort(predictions[0])[-3:][::-1]
        top_3_predictions = []
        for idx in top_3_indices:
            if label_encoder is not None and hasattr(label_encoder, 'classes_'):
                class_name = label_encoder.classes_[idx]
            else:
                class_name = f"Class {idx}"
            top_3_predictions.append({
                'accent': class_name,
                'confidence': float(predictions[0][idx] * 100)
            })
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'predicted_accent': predicted_class,
            'confidence': round(confidence, 2),
            'top_3': top_3_predictions
        })
    
    except Exception as e:
        # Clean up file on error
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Error processing audio: {str(e)}'}), 500

if __name__ == '__main__':
    load_model_and_encoder()
    app.run(debug=True, host='0.0.0.0', port=8080)

