ACCENTA

What Inspired Us

Language learning apps have revolutionized how we acquire new languages, but they often fall short when it comes to pronunciation and accent training. Traditional apps like Duolingo excel at vocabulary and grammar, but they lack the nuanced feedback needed to master authentic accents.

This gap inspired Accenta — a platform that bridges the divide between language learning and accent mastery. We wanted to create a tool that doesn’t just teach you what to say, but how to say it with authentic pronunciation. Accenta complements Duolingo — you can learn structure there, and perfect pronunciation here.

⸻

What We Learned

Machine Learning & Audio Processing • Trained custom CNN models using TensorFlow to detect accents from audio samples • Extracted MFCC (Mel-frequency cepstral coefficients) features for analysis • Implemented phoneme-level analysis with the phonemizer library (espeak backend) • Managed imbalanced datasets using class weighting and oversampling

AI Integration • Integrated Google Gemini for conversational practice • Handled AI safety filters and implemented fallback modes • Used prompt engineering for constructive feedback

Audio Technology • Used Whisper for multilingual transcription • ElevenLabs for natural-sounding speech generation • Built real-time visualization with Web Audio API

Full-Stack Development • FastAPI backend using async requests • React frontend with real-time audio control • Robust audio permission handling across browsers

⸻

How We Built It

Architecture Overview

Backend (FastAPI + Python) • Accent detection with CNN model • Phoneme extraction and feedback system • Gemini-based conversational feedback • ElevenLabs for text-to-speech • Whisper transcription API

Frontend (React) • Practice mode with reference audio comparison • Live chat with Wally, an AI tutor • Phoneme-level visualization and feedback • Real-time waveform animation

⸻

Key Features 1. Real-Time Accent Evaluation: Model analyzes speech and provides accuracy score for target accent. 2. Phoneme-Level Feedback: Compares your pronunciation phoneme-by-phoneme and pinpoints weak sounds. 3. AI-Powered Conversations: Practice freely with Gemini-powered tutor who gives accent advice mid-chat. 4. Multi-Language Support: English, Spanish, Mandarin, Japanese, French, German, Italian, Portuguese. 5. Accent Variety: Train on American, British, Australian, and more.

⸻

Technical Challenges & Solutions

Accent Detection Accuracy • Problem: Model confused between accents • Solution: Balanced dataset and accent-specific training

Real-Time Audio Processing • Problem: Browser restrictions • Solution: Fallbacks for Safari, error-safe permission handling

AI Consistency • Problem: Gemini drifted languages mid-session • Solution: Context preservation and reinforced language tags

Phoneme Extraction • Problem: Espeak dependencies • Solution: Dynamic language code resolution and fallbacks

API Key Reloading • Problem: Backend needed restart for new keys • Solution: On-request key reloading
