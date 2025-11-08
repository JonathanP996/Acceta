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
  const [showIntro, setShowIntro] = useState(true);
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
          // Use language ID (ISO-639-1 code) instead of name for Whisper API
          // Map language IDs to ISO-639-1 codes
          const languageCodeMap = {
            'english': 'en',
            'spanish': 'es',
            'french': 'fr',
            'german': 'de',
            'italian': 'it',
            'portuguese': 'pt',
            'chinese': 'zh',
            'mandarin': 'zh',
            'japanese': 'ja',
            'korean': 'ko',
            'russian': 'ru',
            'arabic': 'ar',
            'hindi': 'hi',
          };
          const languageCode = languageCodeMap[language.id] || language.id;
          formData.append('language', languageCode);
          formData.append('target_accent', accent.name);
          formData.append('expected_text', TEST_PROMPTS[currentPrompt]); // Send the expected phrase

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
      // Show user-friendly error message
      const errorMessage = error.response?.data?.detail || error.message || 'Error analyzing recording. Please try again.';
      alert(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const finishTest = () => {
    // Calculate average score
    const avgScore = testResults.length > 0
      ? testResults.reduce((sum, r) => sum + (r.result.accent_score || 0), 0) / testResults.length
      : 0;

    // Mark that user has completed initial test and has a profile
    localStorage.setItem('hasCompletedInitialTest', 'true');
    localStorage.setItem('hasVisitedDashboard', 'true');

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

  const handleBack = () => {
    // Don't allow exit while recording
    if (isRecording) {
      alert('Please stop recording before exiting.');
      return;
    }

    // If on intro screen, go back to accent selection
    if (showIntro) {
      navigate('/accent-selection/' + (language?.id || 'english'), { state: { language } });
      return;
    }

    // If on test screen, show confirmation dialog if there's progress
    if (testResults.length > 0 || currentPrompt > 0) {
      const confirmed = window.confirm(
        'Are you sure you want to exit? Your progress will be lost.'
      );
      if (confirmed) {
        // Clean up audio if needed
        if (audioCapture) {
          audioCapture.cleanup();
        }
        navigate('/accent-selection/' + (language?.id || 'english'), { state: { language } });
      }
    } else {
      // No progress yet, just go back
      if (audioCapture) {
        audioCapture.cleanup();
      }
      navigate('/accent-selection/' + (language?.id || 'english'), { state: { language } });
    }
  };

  const progress = ((currentPrompt + 1) / TEST_PROMPTS.length) * 100;

  // Intro/Onboarding Screen
  if (showIntro) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4">
        <div className="max-w-3xl mx-auto">
          {/* Back Button */}
          <button
            onClick={handleBack}
            className="mb-4 flex items-center gap-2 text-white hover:text-white/80 transition-colors bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg backdrop-blur-sm"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back</span>
          </button>
          
          <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-accenta-primary rounded-full mb-4">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Welcome to Your Initial Assessment
              </h1>
              <p className="text-xl text-gray-600">
                Let's establish your baseline pronunciation
              </p>
            </div>

            {/* What is it */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-6 h-6 text-accenta-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                What is this?
              </h2>
              <p className="text-gray-700 leading-relaxed">
                The Initial Assessment is a comprehensive pronunciation test that evaluates your current accent and pronunciation skills. 
                You'll be asked to repeat {TEST_PROMPTS.length} carefully selected phrases that test different aspects of pronunciation, 
                including vowel sounds, consonant clusters, rhythm, and intonation.
              </p>
            </div>

            {/* Purpose */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-6 h-6 text-accenta-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Why is this important?
              </h2>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-accenta-primary/10 rounded-full flex items-center justify-center mt-0.5">
                    <span className="text-accenta-primary font-semibold text-sm">1</span>
                  </div>
                  <div>
                    <p className="font-medium">Establishes Your Baseline</p>
                    <p className="text-sm text-gray-600">We'll measure your starting point so you can track your progress over time.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-accenta-primary/10 rounded-full flex items-center justify-center mt-0.5">
                    <span className="text-accenta-primary font-semibold text-sm">2</span>
                  </div>
                  <div>
                    <p className="font-medium">Personalizes Your Learning</p>
                    <p className="text-sm text-gray-600">Identifies specific areas where you need the most practice.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-accenta-primary/10 rounded-full flex items-center justify-center mt-0.5">
                    <span className="text-accenta-primary font-semibold text-sm">3</span>
                  </div>
                  <div>
                    <p className="font-medium">Creates Your Learning Path</p>
                    <p className="text-sm text-gray-600">Helps us recommend the best practice exercises for your skill level.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* How to do it */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-6 h-6 text-accenta-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                How to complete the test
              </h2>
              <div className="space-y-4">
                <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-accenta-primary text-white rounded-full flex items-center justify-center font-bold">
                    1
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 mb-1">Listen to the phrase</p>
                    <p className="text-sm text-gray-600">Click the "Play Phrase" button to hear how it should sound in {accent?.name || 'your target accent'}.</p>
                  </div>
                </div>
                <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-accenta-primary text-white rounded-full flex items-center justify-center font-bold">
                    2
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 mb-1">Repeat what you heard</p>
                    <p className="text-sm text-gray-600">Click "Start Recording" and speak the phrase clearly. Try to match the accent and pronunciation as closely as possible.</p>
                  </div>
                </div>
                <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-accenta-primary text-white rounded-full flex items-center justify-center font-bold">
                    3
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 mb-1">Stop recording</p>
                    <p className="text-sm text-gray-600">Click "Stop Recording" when you're done. Your pronunciation will be analyzed automatically.</p>
                  </div>
                </div>
                <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-accenta-primary text-white rounded-full flex items-center justify-center font-bold">
                    4
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 mb-1">Continue to the next phrase</p>
                    <p className="text-sm text-gray-600">Repeat this process for all {TEST_PROMPTS.length} phrases. Take your time and speak naturally!</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="mb-8 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
              <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Tips for best results
              </h3>
              <ul className="text-sm text-blue-800 space-y-1 ml-7">
                <li>• Find a quiet environment where you won't be interrupted</li>
                <li>• Use a good quality microphone if possible</li>
                <li>• Speak clearly and at a natural pace</li>
                <li>• You can replay the phrase as many times as you need</li>
                <li>• Don't worry about perfection - this is just a baseline!</li>
              </ul>
            </div>

            {/* Start Button */}
            <div className="text-center">
              <button
                onClick={() => setShowIntro(false)}
                className="px-8 py-4 bg-accenta-primary text-white rounded-lg font-semibold text-lg hover:bg-accenta-secondary transition-colors duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center gap-2 mx-auto"
              >
                <span>Start Assessment</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
              <p className="text-sm text-gray-500 mt-4">
                This will take approximately {Math.ceil(TEST_PROMPTS.length * 0.5)} minutes
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <button
          onClick={handleBack}
          disabled={isRecording || isProcessing}
          className="mb-4 flex items-center gap-2 text-white hover:text-white/80 transition-colors bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg backdrop-blur-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>Exit Test</span>
        </button>

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

          {/* Show feedback for current/last result */}
          {testResults.length > 0 && testResults[testResults.length - 1]?.result && (
            <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Your Results</h3>
              
              {/* Text Match Warning */}
              {testResults[testResults.length - 1].result.text_match_warning && (
                <div className="mb-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 rounded">
                  <p className="text-yellow-800 font-semibold">
                    ⚠️ {testResults[testResults.length - 1].result.text_match_warning}
                  </p>
                  {testResults[testResults.length - 1].result.word_accuracy !== undefined && (
                    <p className="text-sm text-yellow-700 mt-1">
                      Word match: {testResults[testResults.length - 1].result.word_accuracy}%
                    </p>
                  )}
                </div>
              )}
              
              {/* Word Accuracy (if available and good) */}
              {testResults[testResults.length - 1].result.word_accuracy !== undefined && !testResults[testResults.length - 1].result.text_match_warning && (
                <div className="mb-4 p-3 bg-green-50 rounded">
                  <p className="text-sm text-green-700">
                    ✅ Word accuracy: {testResults[testResults.length - 1].result.word_accuracy}%
                  </p>
                </div>
              )}
              
              {/* Scoring Breakdown (Detailed Analysis) */}
              {testResults[testResults.length - 1].result.scoring_breakdown && (
                <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">📊 Detailed Scoring Breakdown</h4>
                  
                  {/* Speaking Rate */}
                  {testResults[testResults.length - 1].result.scoring_breakdown.speaking_rate && (
                    <div className="mb-3 p-2 bg-white rounded">
                      <p className="text-xs font-semibold text-gray-700 mb-1">Speaking Rate:</p>
                      <p className="text-xs text-gray-600">
                        {testResults[testResults.length - 1].result.scoring_breakdown.speaking_rate.words_per_second} words/sec • {' '}
                        {testResults[testResults.length - 1].result.scoring_breakdown.speaking_rate.phonemes_per_second} phonemes/sec • {' '}
                        {testResults[testResults.length - 1].result.scoring_breakdown.speaking_rate.total_duration}s duration
                      </p>
                    </div>
                  )}
                  
                  {/* Global Features */}
                  {testResults[testResults.length - 1].result.scoring_breakdown.global_features && (
                    <div className="mb-3 p-2 bg-white rounded">
                      <p className="text-xs font-semibold text-gray-700 mb-1">Your Voice Features:</p>
                      <div className="text-xs text-gray-600 space-y-1">
                        {testResults[testResults.length - 1].result.scoring_breakdown.global_features.pitch_analysis && (
                          <p>
                            Pitch: {testResults[testResults.length - 1].result.scoring_breakdown.global_features.pitch_analysis.your_pitch_hz} Hz
                            {' '}(Reference: {testResults[testResults.length - 1].result.scoring_breakdown.global_features.pitch_analysis.reference_range})
                            {' '}• Match: {Math.round(testResults[testResults.length - 1].result.scoring_breakdown.global_features.pitch_analysis.match_probability * 100)}%
                          </p>
                        )}
                        {testResults[testResults.length - 1].result.scoring_breakdown.global_features.intensity && (
                          <p>
                            Intensity: {testResults[testResults.length - 1].result.scoring_breakdown.global_features.intensity}
                            {' '}(Normalized: {testResults[testResults.length - 1].result.scoring_breakdown.global_features.intensity_normalized})
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Summary */}
                  {testResults[testResults.length - 1].result.scoring_breakdown.summary && (
                    <div className="p-2 bg-blue-50 rounded">
                      <p className="text-xs font-semibold text-blue-900 mb-1">Analysis Summary:</p>
                      <p className="text-xs text-blue-700">
                        Analyzed {testResults[testResults.length - 1].result.scoring_breakdown.summary.total_phonemes_analyzed} phonemes • {' '}
                        Average deviation: {testResults[testResults.length - 1].result.scoring_breakdown.summary.average_deviation} • {' '}
                        {testResults[testResults.length - 1].result.scoring_breakdown.summary.native_boost_applied ? '✅ Native speaker boost applied' : ''}
                        {testResults[testResults.length - 1].result.scoring_breakdown.summary.user_baseline_used ? ' • ✅ Personalized baseline used' : ''}
                      </p>
                    </div>
                  )}
                  
                  {/* Expandable Details */}
                  <details className="mt-2">
                    <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                      Show detailed per-phoneme analysis ({testResults[testResults.length - 1].result.scoring_breakdown.per_phoneme_details?.length || 0} phonemes)
                    </summary>
                    <div className="mt-2 max-h-60 overflow-y-auto space-y-2">
                      {testResults[testResults.length - 1].result.scoring_breakdown.per_phoneme_details?.slice(0, 10).map((detail, idx) => (
                        <div key={idx} className="p-2 bg-white rounded text-xs">
                          <p className="font-semibold">{detail.phoneme}: {detail.final_score.accent_score}%</p>
                          <p className="text-gray-600">
                            Pitch: {detail.features.pitch_hz}Hz ({detail.probabilities.pitch_prob * 100}% match) • {' '}
                            Duration: {detail.features.duration_seconds}s ({detail.probabilities.duration_prob * 100}% match) • {' '}
                            Intensity: {detail.probabilities.intensity_prob * 100}% match
                          </p>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
              
              {/* Accent Score */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-700">Accent Accuracy</span>
                  <span className="text-2xl font-bold text-accenta-primary">
                    {testResults[testResults.length - 1].result.accent_score?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-accenta-primary h-3 rounded-full transition-all duration-500"
                    style={{ width: `${testResults[testResults.length - 1].result.accent_score || 0}%` }}
                  />
                </div>
              </div>

              {/* Feedback Summary */}
              {testResults[testResults.length - 1].result.feedback_summary && (
                <div className="mb-4 p-4 bg-white rounded-lg">
                  <p className="text-gray-800">{testResults[testResults.length - 1].result.feedback_summary}</p>
                </div>
              )}

              {/* Strengths */}
              {testResults[testResults.length - 1].result.strengths && testResults[testResults.length - 1].result.strengths.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-green-700 mb-2">✅ Strengths</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {testResults[testResults.length - 1].result.strengths.map((strength, idx) => (
                      <li key={idx} className="text-sm text-green-600">{strength}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Weaknesses */}
              {testResults[testResults.length - 1].result.weaknesses && testResults[testResults.length - 1].result.weaknesses.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-orange-700 mb-2">⚠️ Areas to Improve</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {testResults[testResults.length - 1].result.weaknesses.map((weakness, idx) => (
                      <li key={idx} className="text-sm text-orange-600">{weakness}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Exercises */}
              {testResults[testResults.length - 1].result.personalized_exercises && testResults[testResults.length - 1].result.personalized_exercises.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-blue-700 mb-2">💡 Practice Tips</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {testResults[testResults.length - 1].result.personalized_exercises.map((exercise, idx) => (
                      <li key={idx} className="text-sm text-blue-600">{exercise}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Results Summary */}
          {testResults.length > 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
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

