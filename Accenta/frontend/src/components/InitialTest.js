import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AudioCapture from '../utils/audioCapture';
import { analysisService, ttsService, authService, getUserStorageKey } from '../services/api';
import { getTestPrompts } from '../data/languagePrompts';
import { getSkillLevel, SKILL_LEVELS } from '../data/skills';

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
  const [isMounted, setIsMounted] = useState(false);
  const [hasPlayedOnce, setHasPlayedOnce] = useState(false);
  const [waveformTime, setWaveformTime] = useState(0);
  const waveformAnimationRef = useRef(null);
  const [audioDataArray, setAudioDataArray] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [profileSettings, setProfileSettings] = useState({
    colorScheme: 'blueOrange',
  });
  
  // Get language-specific test prompts - limit to 5 questions
  const allPrompts = language ? getTestPrompts(language.id) : getTestPrompts('english');
  const TEST_PROMPTS = allPrompts.slice(0, 5);

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

  // Load profile settings from localStorage (email-specific)
  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (currentUser?.email) {
      const storageKey = getUserStorageKey('profileSettings', currentUser.email);
      const savedSettings = localStorage.getItem(storageKey);
      if (savedSettings) {
        try {
          const parsed = JSON.parse(savedSettings);
          setProfileSettings(parsed);
        } catch (error) {
          console.error('Error loading profile settings:', error);
        }
      }
    }
  }, []);

  // Fade in animation on mount
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Color scheme configurations (matching Dashboard)
  const colorSchemes = {
    blueOrange: {
      gradient: 'from-blue-900 via-cyan-800 to-orange-800',
      backgroundGradient: 'from-blue-900 via-cyan-800 to-orange-800',
    },
    pink: {
      gradient: 'from-pink-50 via-rose-50 to-fuchsia-50',
      backgroundGradient: 'from-pink-400 via-rose-400 to-fuchsia-400',
    },
    purple: {
      gradient: 'from-purple-50 via-indigo-50 to-pink-50',
      backgroundGradient: 'from-purple-400 via-indigo-400 to-pink-400',
    },
    blue: {
      gradient: 'from-blue-50 via-cyan-50 to-teal-50',
      backgroundGradient: 'from-blue-400 via-cyan-400 to-teal-400',
    },
    green: {
      gradient: 'from-green-50 via-emerald-50 to-teal-50',
      backgroundGradient: 'from-green-400 via-emerald-400 to-teal-400',
    },
  };

  const currentColorScheme = colorSchemes[profileSettings.colorScheme] || colorSchemes.blueOrange;

  // Color complements for waveform
  const colorComplements = {
    blueOrange: {
      primary: '#10B981', // Green (complement of blue/orange)
      secondary: '#059669',
      light: '#34D399',
    },
    pink: {
      primary: '#10B981',
      secondary: '#059669',
      light: '#34D399',
    },
    purple: {
      primary: '#F59E0B',
      secondary: '#D97706',
      light: '#FBBF24',
    },
    blue: {
      primary: '#F97316',
      secondary: '#EA580C',
      light: '#FB923C',
    },
    green: {
      primary: '#EC4899',
      secondary: '#DB2777',
      light: '#F472B6',
    },
  };

  const currentComplement = colorComplements[profileSettings.colorScheme] || colorComplements.blueOrange;

  // Autoplay audio when prompt changes
  useEffect(() => {
    if (TEST_PROMPTS[currentPrompt] && accent && !showResults) {
      setHasPlayedOnce(false);
      const timer = setTimeout(() => {
        playPrompt();
      }, 300);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPrompt, showResults]);

  // Animate waveform when recording - reactive to mic input
  useEffect(() => {
    if (isRecording && audioCapture && audioCapture.analyser) {
      const analyser = audioCapture.analyser;
      const dataArray = new Uint8Array(analyser.fftSize);
      
      const animate = () => {
        analyser.getByteTimeDomainData(dataArray);
        
        let hasAudio = false;
        for (let i = 0; i < dataArray.length; i++) {
          if (Math.abs(dataArray[i] - 128) > 0.5) {
            hasAudio = true;
            break;
          }
        }
        
        if (hasAudio) {
          setAudioDataArray([...dataArray]);
        } else {
          setAudioDataArray(null);
        }
        
        waveformAnimationRef.current = requestAnimationFrame(animate);
      };
      waveformAnimationRef.current = requestAnimationFrame(animate);
      return () => {
        if (waveformAnimationRef.current) {
          cancelAnimationFrame(waveformAnimationRef.current);
          waveformAnimationRef.current = null;
        }
      };
    } else {
      setAudioDataArray(null);
      if (waveformAnimationRef.current) {
        cancelAnimationFrame(waveformAnimationRef.current);
        waveformAnimationRef.current = null;
      }
    }
  }, [isRecording, audioCapture]);

  const playPrompt = async () => {
    if (!accent) return;
    
    setIsPlaying(true);
    setHasPlayedOnce(true);
    try {
      // Use ElevenLabs TTS via backend
      // Extract accent name (e.g., "American English" -> "american")
      const accentName = accent.name.toLowerCase().replace(' english', '').replace('english', '').trim();
      console.log('🎵 Calling ElevenLabs TTS for initial test:', {
        prompt: TEST_PROMPTS[currentPrompt],
        accentName,
        accentFull: accent.name
      });
      
      // Ensure we're using ElevenLabs - no fallback
      const audioBlob = await ttsService.generateSpeech(
        TEST_PROMPTS[currentPrompt],
        null, // voice_id - will use accent-based selection from backend
        accentName, // accent name for voice selection (MUST be provided)
        false // robotic = false for test prompts (natural voice)
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
      console.error('❌ Error generating/playing TTS with ElevenLabs:', error);
      setIsPlaying(false);
      
      // Show user-friendly error message
      const errorMessage = error.message || 'Failed to generate audio with ElevenLabs';
      alert(`Unable to play audio: ${errorMessage}\n\nPlease ensure:\n- Backend server is running\n- ElevenLabs API key is configured\n- Check browser console for details`);
      
      // DO NOT use Web Speech API fallback - ElevenLabs is required
      throw error; // Re-throw to prevent any fallback
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

      // Move to next prompt immediately (no feedback display)
      if (currentPrompt < TEST_PROMPTS.length - 1) {
        setCurrentPrompt(currentPrompt + 1);
        setHasPlayedOnce(false);
      } else {
        // Test complete - show results
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
    setShowResults(true);
    setIsProcessing(false);
  };

  const handleContinueToDashboard = () => {
    // Calculate average score
    const avgScore = testResults.length > 0
      ? testResults.reduce((sum, r) => sum + (r.result.accent_score || 0), 0) / testResults.length
      : 0;

    // Calculate skill level from average score
    const skillRank = getSkillLevel(avgScore);

    // Mark that user has completed initial test and has a profile
    localStorage.setItem('hasCompletedInitialTest', 'true');
    localStorage.setItem('hasVisitedDashboard', 'true');

    // Navigate to practice transition screen
    navigate('/practice-transition', {
      state: {
        profile: {
        language: language,
          accent: accent,
          overallScore: avgScore,
          skillLevel: skillRank,
        },
        accent: accent,
        fromInitialTest: true,
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

  // Calculate skill rank for results screen
  const calculateSkillRank = () => {
    if (testResults.length === 0) return null;
    const avgScore = testResults.reduce((sum, r) => sum + (r.result.accent_score || 0), 0) / testResults.length;
    return getSkillLevel(avgScore);
  };

  const skillRank = showResults ? calculateSkillRank() : null;
  const avgScore = showResults && testResults.length > 0
    ? testResults.reduce((sum, r) => sum + (r.result.accent_score || 0), 0) / testResults.length
    : 0;

  // Results Screen
  if (showResults) {
    return (
      <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.backgroundGradient} flex flex-col opacity-90`}>
        <div className="flex-1 flex items-center justify-center px-4 pb-4">
          <div 
            className={`bg-white rounded-3xl shadow-2xl p-8 w-full max-w-4xl flex flex-col transition-all duration-700 ${
              isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
            style={{ minHeight: 'calc(100vh - 200px)', height: 'auto' }}
          >
            <div className="flex-1 flex flex-col items-center justify-center text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Assessment Complete!
              </h1>
              
              {skillRank && (
                <div className="mb-8">
                  <div className="inline-block px-6 py-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-full mb-4">
                    <p className="text-sm text-gray-600 mb-1">Your Skill Rank</p>
                    <p 
                      className="text-3xl font-bold"
                      style={{ 
                        color: skillRank.color === 'red' ? '#DC2626' :
                               skillRank.color === 'orange' ? '#EA580C' :
                               skillRank.color === 'yellow' ? '#CA8A04' :
                               skillRank.color === 'green' ? '#16A34A' :
                               skillRank.color === 'blue' ? '#2563EB' : '#6B7280'
                      }}
                    >
                      {skillRank.name}
                    </p>
                  </div>
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-700">Overall Score</span>
                      <span className="text-2xl font-bold text-accenta-primary">
                        {avgScore.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="h-3 rounded-full transition-all duration-500"
                        style={{ 
                          width: `${avgScore}%`,
                          backgroundColor: skillRank.color === 'red' ? '#DC2626' :
                                           skillRank.color === 'orange' ? '#EA580C' :
                                           skillRank.color === 'yellow' ? '#CA8A04' :
                                           skillRank.color === 'green' ? '#16A34A' :
                                           skillRank.color === 'blue' ? '#2563EB' : '#6B7280'
                        }}
                      />
                    </div>
                  </div>
                </div>
              )}

              <p className="text-lg text-gray-600 mb-8 max-w-2xl">
                You've completed all {TEST_PROMPTS.length} questions. Your skill rank has been calculated based on your pronunciation accuracy.
              </p>

              <button
                onClick={handleContinueToDashboard}
                className="px-8 py-4 bg-accenta-primary text-white rounded-lg font-semibold text-lg hover:bg-accenta-secondary transition-colors duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Start Practice Session
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
    <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.backgroundGradient} flex flex-col opacity-90`}>
      {/* Progress Bar at Top */}
      <div className={`w-full px-4 pt-4 pb-2 transition-all duration-700 ${
        isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
      }`}>
        <div className="max-w-7xl mx-auto">
          {/* Question Number */}
          <div className="flex justify-between items-center mb-2">
        <button
          onClick={handleBack}
          disabled={isRecording || isProcessing}
              className="text-white hover:text-gray-200 flex items-center drop-shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
              Back
        </button>
            <span className="text-white text-xl font-semibold drop-shadow-lg">
              {currentPrompt + 1} / {TEST_PROMPTS.length}
            </span>
          </div>
          {/* Progress Bar */}
          <div className="bg-white/30 rounded-full h-3 shadow-lg">
            <div
              className="bg-white h-3 rounded-full transition-all duration-300 shadow-md"
              style={{ width: `${progress}%` }}
            />
          </div>
          </div>
        </div>

      {/* Main Practice Card - Full Screen */}
      <div className="flex-1 flex items-center justify-center px-4 pb-4">
        <div 
          className={`bg-white rounded-3xl shadow-2xl p-8 w-full max-w-4xl flex flex-col transition-all duration-700 ${
            isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
          style={{ minHeight: 'calc(100vh - 200px)', height: 'auto' }}
        >
          {/* Static Content Section - Centered */}
          <div className="flex-shrink-0 flex flex-col items-center justify-center relative" style={{ minHeight: '400px', paddingTop: '80px' }}>
            {/* Phrase - Centered in available space */}
            <div className={`text-center transition-all duration-700 delay-200 flex items-center justify-center ${
              isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`} style={{ width: '100%', justifyContent: 'center', alignItems: 'center' }}>
              <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight text-gray-900 text-center px-4">
              {TEST_PROMPTS[currentPrompt]}
            </h2>
          </div>

            {/* Replay Button - Below phrase */}
            <div className={`flex justify-center mt-6 transition-opacity duration-300 ${hasPlayedOnce && !isPlaying ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
              <button
                onClick={playPrompt}
                disabled={isRecording || isPlaying || !hasPlayedOnce}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" />
                </svg>
                Replay
              </button>
            </div>

            {/* Recording Button with Waveform Animation - Below replay */}
            <div className="flex flex-col items-center justify-center relative mt-6" style={{ minHeight: '200px', width: '400px' }}>
              {/* Waveform Background - Always visible when recording */}
              {isRecording && (
                <div 
                  className="absolute flex items-center justify-center"
                  style={{ 
                    width: '400px', 
                    height: '200px',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -60%)',
                    zIndex: 0,
                    animation: 'fadeIn 0.3s ease-in forwards',
                    opacity: 1
                  }}
                >
                  <svg 
                    width="400" 
                    height="200" 
                    style={{ 
                      background: 'transparent'
                    }}
                  >
                    <defs>
                      <linearGradient id={`waveGradient-test-${currentPrompt}`} x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor={currentComplement.light} stopOpacity="0.3" />
                        <stop offset="50%" stopColor={currentComplement.primary} stopOpacity="1" />
                        <stop offset="100%" stopColor={currentComplement.light} stopOpacity="0.3" />
                      </linearGradient>
                    </defs>
                    {/* Three wavy lines - flat normally, reactive to audio */}
                    {[0, 1, 2].map((lineIndex) => {
                      const centerY = 100;
                      const offset = 0;
                      const points = [];
                      const numPoints = 200;
                      
                      if (audioDataArray && audioDataArray.length > 0) {
                        const dataLength = audioDataArray.length;
                        const samplesPerPoint = Math.max(1, Math.floor(dataLength / numPoints));
                        
                        for (let i = 0; i <= numPoints; i++) {
                          const x = (i / numPoints) * 400;
                          const dataIndex = Math.min(Math.floor((i / numPoints) * dataLength), dataLength - 1);
                          
                          let sum = 0;
                          let count = 0;
                          for (let j = 0; j < samplesPerPoint && (dataIndex + j) < dataLength; j++) {
                            sum += audioDataArray[dataIndex + j];
                            count++;
                          }
                          const avgValue = count > 0 ? sum / count : 128;
                          
                          const centerDistance = Math.abs(x - 200) / 200;
                          const baseAmplitude = (1 - centerDistance) * 25 + 5;
                          const normalizedAudio = (avgValue - 128) / 128;
                          const amplifiedAudio = normalizedAudio * 2.5;
                          const audioAmplitude = amplifiedAudio * baseAmplitude;
                          const phase = lineIndex * Math.PI / 4;
                          const y = centerY + offset + audioAmplitude + Math.sin((x * 0.01) + phase) * 2;
                          points.push(`${x},${y}`);
                        }
                      } else {
                        for (let i = 0; i <= numPoints; i++) {
                          const x = (i / numPoints) * 400;
                          const y = centerY + offset;
                          points.push(`${x},${y}`);
                        }
                      }
                      
                      return (
                        <polyline
                          key={lineIndex}
                          points={points.join(' ')}
                          fill="none"
                          stroke={`url(#waveGradient-test-${currentPrompt})`}
                          strokeWidth="2"
                          style={{
                            transition: 'opacity 0.1s ease',
                            opacity: 1
                          }}
                        />
                      );
                    })}
                  </svg>
                </div>
              )}
              
              {/* Record Button - Centered in waveform area */}
              <div className="relative z-10 flex flex-col items-center justify-center">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    disabled={isPlaying || isProcessing || !audioCapture}
                    className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95"
                  >
                    <svg className="w-8 h-8 text-gray-900" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                    </svg>
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="w-20 h-20 bg-black rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all transform hover:scale-105 active:scale-95"
                  >
                    <div className="w-6 h-6 bg-white rounded-sm"></div>
                  </button>
                )}
                {/* Label below button */}
                <div className="mt-3">
                  <div className="bg-gray-800 text-white px-4 py-2 rounded-lg text-sm font-medium shadow-md">
                    <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-800"></div>
                    {isRecording ? 'Recording...' : 'Tap to speak'}
                </div>
                </div>
              </div>
            </div>

            {/* Processing Indicator */}
            {isProcessing && (
              <div className="text-center text-gray-600 mt-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accenta-primary"></div>
                <p className="mt-2">Analyzing your pronunciation...</p>
            </div>
          )}

        {/* Skip Button (for testing) */}
            <div className="mt-8 text-center">
          <button
                onClick={() => {
                  if (currentPrompt < TEST_PROMPTS.length - 1) {
                    setCurrentPrompt(currentPrompt + 1);
                    setHasPlayedOnce(false);
                  } else {
                    finishTest();
                  }
                }}
                className="text-gray-500 hover:text-gray-700 text-sm underline"
          >
            Skip (for testing)
          </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InitialTest;

