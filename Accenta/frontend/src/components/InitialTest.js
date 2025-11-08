import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AudioCapture from '../utils/audioCapture';
import { analysisService, ttsService } from '../services/api';

const TEST_PROMPTS = [
  "The quick brown fox jumps over the lazy dog",
  "She sells seashells by the seashore",
  "How much wood would a woodchuck chuck",
  "Peter Piper picked a peck of pickled peppers",
  "Red lorry, yellow lorry",
  "Unique New York",
  "Irish wristwatch",
  "Six thick thistle sticks",
  "The thirty-three thieves thought that they thrilled the throne",
  "I wish to wish the wish you wish to wish",
  "A proper copper coffee pot",
  "Betty Botter bought some butter",
  "Fuzzy Wuzzy was a bear",
  "Can you can a can as a canner can can a can?",
  "I scream, you scream, we all scream for ice cream",
  "How can a clam cram in a clean cream can?",
  "Lesser leather never weathered wetter weather better",
  "A big black bug bit a big black bear",
  "The sixth sick sheik's sixth sheep's sick",
  "Which witch is which?",
  "Round the rugged rock the ragged rascal ran",
  "Three free throws",
  "Theophilus Thistle, the successful thistle-sifter",
  "I thought a thought but the thought I thought wasn't the thought I thought",
  "If two witches would watch two watches",
  "A skunk sat on a stump and thunk the stump stunk",
  "Toy boat, toy boat, toy boat",
  "Red leather, yellow leather",
  "The great Greek grape growers grow great Greek grapes",
  "I slit the sheet, the sheet I slit",
];

const InitialTest = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { language, accent } = location.state || {};
  const [currentPrompt, setCurrentPrompt] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioCapture, setAudioCapture] = useState(null);
  const [testResults, setTestResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (!language || !accent) {
      navigate('/language-selection');
      return;
    }

    // Initialize audio capture
    const initAudio = async () => {
      try {
        const capture = new AudioCapture();
        await capture.initialize();
        setAudioCapture(capture);
      } catch (error) {
        alert('Microphone access required. Please allow microphone access and refresh.');
      }
    };

    initAudio();

    return () => {
      if (audioCapture) {
        audioCapture.cleanup();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const playPrompt = async () => {
    if (!accent) return;
    
    setIsPlaying(true);
    try {
      // Use ElevenLabs TTS via backend
      // Extract accent name (e.g., "American English" -> "american")
      const accentName = accent.name.toLowerCase().replace(' english', '').replace('english', '').trim();
      const audioBlob = await ttsService.generateSpeech(
        TEST_PROMPTS[currentPrompt],
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
        const utterance = new SpeechSynthesisUtterance(TEST_PROMPTS[currentPrompt]);
        utterance.lang = language.id === 'english' ? 'en-US' : language.id;
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
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = async () => {
    if (!audioCapture || !isRecording) return;
    
    setIsRecording(false);
    setIsProcessing(true);

    try {
      const audioBlob = await audioCapture.stopRecording();
      
      // Create form data for API
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.wav');
      formData.append('user_id', JSON.parse(localStorage.getItem('user')).user_id);
      formData.append('session_id', `test_${Date.now()}`);
      formData.append('language', language.name);
      formData.append('target_accent', accent.name);

      // Analyze the recording
      const result = await analysisService.analyzeAccent(formData);
      
      setTestResults([...testResults, {
        prompt: TEST_PROMPTS[currentPrompt],
        result: result,
        promptIndex: currentPrompt,
      }]);

      // Move to next prompt
      if (currentPrompt < TEST_PROMPTS.length - 1) {
        setCurrentPrompt(currentPrompt + 1);
      } else {
        // Test complete
        finishTest();
      }
    } catch (error) {
      console.error('Error analyzing recording:', error);
      alert('Error analyzing recording. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const finishTest = () => {
    // Calculate average score
    const avgScore = testResults.length > 0
      ? testResults.reduce((sum, r) => sum + (r.result.accent_score || 0), 0) / testResults.length
      : 0;

    // Navigate to dashboard with results
    navigate('/dashboard', {
      state: {
        testComplete: true,
        language: language,
        accent: accent,
        initialScore: avgScore,
        results: testResults,
      },
    });
  };

  const progress = ((currentPrompt + 1) / TEST_PROMPTS.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-white mb-2">
            <span className="text-lg font-semibold">Initial Assessment</span>
            <span className="text-lg font-semibold">
              {currentPrompt + 1} / {TEST_PROMPTS.length}
            </span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-3">
            <div
              className="bg-white h-3 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {TEST_PROMPTS[currentPrompt]}
            </h2>
            <p className="text-gray-600">
              Listen to the phrase, then repeat it in {accent.name} accent
            </p>
          </div>

          {/* Audio Controls */}
          <div className="flex justify-center gap-4 mb-8">
            <button
              onClick={playPrompt}
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
                disabled={isPlaying || isProcessing || !audioCapture}
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

          {isProcessing && (
            <div className="text-center text-gray-600">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accenta-primary"></div>
              <p className="mt-2">Analyzing your pronunciation...</p>
            </div>
          )}

          {/* Results Summary */}
          {testResults.length > 0 && (
            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">Progress</h3>
              <p className="text-sm text-gray-600">
                Completed: {testResults.length} prompts
              </p>
            </div>
          )}
        </div>

        {/* Skip Button (for testing) */}
        <div className="text-center mt-4">
          <button
            onClick={() => setCurrentPrompt(Math.min(currentPrompt + 1, TEST_PROMPTS.length - 1))}
            className="text-white/80 hover:text-white text-sm"
          >
            Skip (for testing)
          </button>
        </div>
      </div>
    </div>
  );
};

export default InitialTest;

