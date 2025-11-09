from flask import Flask, request, jsonify
from flask_cors import CORS
from accent_detector import AccentDetector
import os
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

# Initialize detector (loads model once at startup)
print("🚀 Initializing Accent Detection Service...")
detector = AccentDetector()
print("✅ Service ready!")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'accent-detection',
        'supported_classes': detector.get_supported_classes()
    })

@app.route('/detect-accent', methods=['POST'])
def detect_accent():
    """
    API endpoint for accent detection.
    Handles both file uploads and microphone recordings (webm/ogg/opus).
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get file extension to determine format
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # If no extension, try to detect from content type
    if not file_ext:
        content_type = file.content_type or ''
        if 'webm' in content_type:
            file_ext = '.webm'
        elif 'ogg' in content_type or 'opus' in content_type:
            file_ext = '.ogg'
        elif 'wav' in content_type:
            file_ext = '.wav'
        elif 'mp3' in content_type:
            file_ext = '.mp3'
        else:
            # Default to webm for microphone recordings
            file_ext = '.webm'
    
    # Save temporarily (cross-platform safe)
    temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
    
    try:
        # Save uploaded file
        file.save(temp_path)
        
        # Make prediction
        result = detector.predict(temp_path)
        return jsonify(result)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during prediction: {error_details}")
        return jsonify({
            'error': str(e),
            'details': error_details if app.debug else None
        }), 500
    finally:
        # Clean up
        os.close(temp_fd)
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    print("🎙️ Accent Detection Service starting on http://localhost:5001")
    print("📡 Endpoints:")
    print("   GET  /health - Health check")
    print("   POST /detect-accent - Detect accent from audio file")
    print("\n💡 Supported formats: mp3, wav, m4a, flac, webm, ogg, opus")
    print("💡 Microphone recordings (webm/ogg) are fully supported!")
    app.run(debug=True, host='0.0.0.0', port=5001)

