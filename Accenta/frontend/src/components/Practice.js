import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AudioCapture from '../utils/audioCapture';
import WaveformVisualization from './WaveformVisualization';
import { ttsService } from '../services/api';

export const PRACTICE_PHRASES = [
  "Hello, how are you today?",
  "I would like a cup of coffee",
  "The weather is beautiful",
  "Can you help me please?",
  "Thank you very much",
  "I'm learning a new language",
  "What time is it?",
  "I love practicing pronunciation",
  "This is challenging but fun",
  "I'm making great progress",
  "Practice makes perfect",
  "I can do this",
  "Every day I improve",
  "Pronunciation is important",
  "I'm getting better",
  "Keep practicing",
  "You're doing great",
  "Don't give up",
  "Success takes time",
  "I believe in myself",
];

const Practice = ({ profile: propProfile, customPhrases, isCurated }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile: locationProfile } = location.state || {};
  const profile = propProfile || locationProfile;
  const phrases = customPhrases || PRACTICE_PHRASES;
  const [currentPhrase, setCurrentPhrase] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioCapture, setAudioCapture] = useState(null);
  const [audioData, setAudioData] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const [showWaveform, setShowWaveform] = useState(false);
  const [timedMode, setTimedMode] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(30);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!profile) {
      navigate('/dashboard');
      return;
    }

    const initAudio = async () => {
      try {
        const capture = new AudioCapture();
        await capture.initialize();
        setAudioCapture(capture);
      } catch (error) {
        alert('Microphone access required for practice mode.');
      }
    };

    initAudio();

    return () => {
      if (audioCapture) {
        audioCapture.cleanup();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (timedMode && isRecording) {
      timerRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            stopRecording();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setTimeRemaining(30);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timedMode, isRecording]);

  const playPhrase = async () => {
    setIsPlaying(true);
    try {
      // Use ElevenLabs TTS via backend
      // Extract accent name (e.g., "American English" -> "american")
      const accentName = profile?.accent 
        ? profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim()
        : null;
      const audioBlob = await ttsService.generateSpeech(
        phrases[currentPhrase],
        null, // voice_id - will use default
        accentName // accent name for voice selection
      );
      
      // Create audio element and play
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = (error) => {
        console.error('Error playing audio:', error);
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
    } catch (error) {
      console.error('Error generating/playing TTS:', error);
      setIsPlaying(false);
      // Fallback to Web Speech API if TTS fails
      try {
        const utterance = new SpeechSynthesisUtterance(phrases[currentPhrase]);
        utterance.onend = () => setIsPlaying(false);
        speechSynthesis.speak(utterance);
      } catch (fallbackError) {
        console.error('Fallback TTS also failed:', fallbackError);
        setIsPlaying(false);
      }
    }
  };

  const startRecording = () => {
    if (!audioCapture) return;
    try {
      audioCapture.startRecording();
      setIsRecording(true);
      setAttempts(attempts + 1);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = async () => {
    if (!audioCapture || !isRecording) return;
    
    setIsRecording(false);

    try {
      const audioBlob = await audioCapture.stopRecording();
      setAudioData(audioBlob);
      setShowWaveform(true);
      
      // In production, analyze the recording here
      // For now, simulate analysis
      setTimeout(() => {
        // Mock: if attempts > 3, move to next phrase
        if (attempts >= 3) {
          nextPhrase();
        }
      }, 2000);
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  const nextPhrase = () => {
    if (currentPhrase < phrases.length - 1) {
      setCurrentPhrase(currentPhrase + 1);
      setAttempts(0);
      setShowWaveform(false);
      setAudioData(null);
    } else {
      // Practice complete
      navigate('/dashboard', { state: { practiceComplete: true, isCurated } });
    }
  };

  const retry = () => {
    setAttempts(0);
    setShowWaveform(false);
    setAudioData(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-white hover:text-gray-200 flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <div className="flex items-center gap-4">
            <label className="flex items-center text-white">
              <input
                type="checkbox"
                checked={timedMode}
                onChange={(e) => setTimedMode(e.target.checked)}
                className="mr-2"
              />
              Timed Mode
            </label>
            <span className="text-white font-semibold">
              {currentPhrase + 1} / {phrases.length}
            </span>
          </div>
        </div>

        {/* Timer */}
        {timedMode && isRecording && (
          <div className="mb-4 text-center">
            <div className="inline-block bg-white/20 rounded-full px-6 py-2">
              <span className="text-white text-2xl font-bold">{timeRemaining}s</span>
            </div>
          </div>
        )}

        {/* Main Practice Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-6">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {phrases[currentPhrase]}
            </h2>
            <p className="text-gray-600">
              {profile?.accent} accent practice
            </p>
          </div>

          {/* Audio Controls */}
          <div className="flex justify-center gap-4 mb-8">
            <button
              onClick={playPhrase}
              disabled={isPlaying || isRecording}
              className="px-6 py-3 bg-accenta-primary text-white rounded-lg font-semibold hover:bg-accenta-secondary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
              {isPlaying ? 'Playing...' : 'Play Phrase'}
            </button>

            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={isPlaying || !audioCapture}
                className="px-6 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 012 0v2a1 1 0 11-2 0V9zm5-1a1 1 0 10-2 0v2a1 1 0 102 0V8z" clipRule="evenodd" />
                </svg>
                Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 flex items-center gap-2 animate-pulse"
              >
                <div className="w-3 h-3 bg-white rounded-full" />
                Recording... Click to Stop
              </button>
            )}
          </div>

          {/* Attempts Counter */}
          {attempts > 0 && (
            <div className="text-center text-gray-600 mb-4">
              Attempt {attempts} of 3
            </div>
          )}

          {/* Waveform Visualization */}
          {showWaveform && audioData && (
            <div className="mt-8">
              <WaveformVisualization
                audioBlob={audioData}
                phrase={phrases[currentPhrase]}
                onRetry={retry}
                onNext={nextPhrase}
                attempts={attempts}
              />
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="bg-white/20 rounded-full h-3">
          <div
            className="bg-white h-3 rounded-full transition-all duration-300"
            style={{ width: `${((currentPhrase + 1) / phrases.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default Practice;

