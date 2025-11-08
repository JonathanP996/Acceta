# Accenta - AI-Powered Accent Learning Platform

Accenta helps language learners master local dialects and accents through AI-powered pronunciation analysis and personalized feedback.

## Architecture

- **Frontend**: React + TailwindCSS with Web Audio API
- **Backend**: FastAPI with WebSocket support
- **AI Pipeline**: Whisper → MFA → Librosa → PyTorch → Gemini ADK Agent
- **TTS**: ElevenLabs for natural accent playback
- **Database**: MongoDB Atlas for user progress and memory
- **Visualization**: D3.js for accent map

## Quick Start

### Prerequisites

1. **Google Cloud SDK** - Install from downloaded tarball
2. **Node.js** (>=18) and npm
3. **Python** 3.10+
4. **MongoDB Atlas** account
5. **ElevenLabs** API key
6. **OpenAI** API key (for Whisper)

### Setup

1. **Install Google Cloud SDK**:
```bash
cd /path/to/google-cloud-cli-darwin-arm.tar.gz
tar -xzf google-cloud-cli-darwin-arm.tar.gz
./google-cloud-sdk/install.sh
./google-cloud-sdk/bin/gcloud init
```

2. **Create Service Account**:
```bash
gcloud iam service-accounts create accent-map-agent --display-name="AccentMap Agent"
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:accent-map-agent@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud iam service-accounts keys create service-account-accentmap.json \
  --iam-account=accent-map-agent@<PROJECT_ID>.iam.gserviceaccount.com
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

4. **Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

5. **Frontend Setup**:
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
Accenta/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── agent/            # ADK agent code
├── schemas/          # Pydantic models
├── tests/            # Test files
└── README.md
```

## API Endpoints

- `POST /analyze_accent` - Full accent analysis
- `WS /ws/practice/{session_id}` - Real-time practice streaming
- `POST /auth/login` - User authentication
- `POST /auth/signup` - User registration

## License

MIT

