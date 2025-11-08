# Accenta Frontend

React + TailwindCSS frontend for the Accenta accent learning platform.

## Features Implemented

### ✅ Authentication
- Login page
- Signup page
- Protected routes
- User session management

### ✅ Language & Accent Selection
- Language selection with search
- Popularity-based sorting
- Accent selection with difficulty indicators

### ✅ Initial Testing Mode
- 30 call-and-response prompts
- Web Audio API recording
- Progress tracking
- ElevenLabs TTS integration (via backend)

### ✅ Dashboard
- User welcome screen
- Active accent profiles
- Quick actions
- Progress overview

### ✅ Profile Page
- User account information
- Skill ratings (5 levels: Beginner → Master)
- Progress timeline with recordings
- Struggle areas tracking
- Practice statistics

### ✅ Practice Mode
- Call-and-response practice
- Web Audio API capture
- Waveform visualization with D3.js
- Problem area highlighting
- Retry mechanism (3 attempts)
- Timed mode toggle
- Progress tracking

### ✅ Waveform Visualization
- D3.js-based waveform display
- Problem area highlighting
- Hover tooltips with tips
- Audio playback controls

## Getting Started

```bash
cd frontend
npm install
npm start
```

The app will open at http://localhost:3000

## Environment Variables

Create a `.env` file in the frontend directory:

```
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/
│   ├── Auth/
│   │   ├── Login.js
│   │   └── Signup.js
│   ├── LanguageSelection.js
│   ├── AccentSelection.js
│   ├── InitialTest.js
│   ├── Dashboard.js
│   ├── Profile.js
│   ├── Practice.js
│   └── WaveformVisualization.js
├── services/
│   └── api.js
├── utils/
│   └── audioCapture.js
├── data/
│   ├── languages.js
│   └── skills.js
├── config/
│   └── api.js
├── App.js
└── index.js
```

## Features in Progress

- WebSocket integration for real-time feedback
- Curated practice tracks
- Multiple language/accent profile switching
- Advanced waveform analysis

## Dependencies

- React 19
- React Router DOM
- TailwindCSS
- Axios
- D3.js
- Web Audio API

