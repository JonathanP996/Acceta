import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AudioCapture from '../utils/audioCapture';
import WaveformVisualization from './WaveformVisualization';
import { ttsService, accentDetectionService } from '../services/api';
import { getPracticePhrases } from '../data/languagePrompts';

// Default practice phrases (fallback) - Short single sentences
export const PRACTICE_PHRASES = [
  "Hello, how are you today?",
  "I would like a cup of coffee.",
  "The weather is beautiful today.",
  "Can you help me please?",
  "Thank you very much.",
  "I'm learning a new language.",
  "What time is it?",
  "I love practicing pronunciation.",
  "This is challenging but fun.",
  "I'm making great progress.",
  "Practice makes perfect.",
  "I can do this.",
  "Every day I improve.",
  "Pronunciation is important.",
  "I'm getting better at speaking.",
  "Keep practicing.",
  "You're doing great.",
  "Don't give up.",
  "Success takes time.",
  "I believe in myself.",
];

const Practice = ({ profile: propProfile, customPhrases: propCustomPhrases, isCurated }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile: locationProfile, fromInitialTest, fromSurvey, customPhrases: locationCustomPhrases } = location.state || {};
  const profile = propProfile || locationProfile;
  
  // Check if this is the first practice session (from initial test or survey)
  const isFirstPractice = fromInitialTest || fromSurvey;
  
  // Get custom phrases from props or location state
  const customPhrases = propCustomPhrases || locationCustomPhrases;
  
  // Get language-specific practice phrases if no custom phrases provided
  const defaultPhrases = profile?.language?.id 
    ? getPracticePhrases(profile.language.id) 
    : PRACTICE_PHRASES;
  
  // Use custom phrases if provided, otherwise use default
  // Limit to 5 questions only for first practice session (not for lesson-specific practice)
  const allPhrases = customPhrases || defaultPhrases;
  const phrases = (isFirstPractice && !customPhrases) ? allPhrases.slice(0, 5) : allPhrases;
  const [currentPhrase, setCurrentPhrase] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioCapture, setAudioCapture] = useState(null);
  const [audioData, setAudioData] = useState(null);
  const [showWaveform, setShowWaveform] = useState(false);
  const [timedMode, setTimedMode] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(30);
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const feedbackAudioRef = useRef(null); // For phoneme feedback TTS audio
  const feedbackAnalyserRef = useRef(null); // For audio analysis during TTS
  const feedbackAudioContextRef = useRef(null); // For Web Audio API context
  const feedbackFrequencyDataRef = useRef(null); // For frequency data
  const feedbackAnimationFrameRef = useRef(null); // For animation frame
  const [feedbackAudioLevels, setFeedbackAudioLevels] = useState([]); // For visualizer bars
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasPlayedOnce, setHasPlayedOnce] = useState(false);
  const resultsRef = useRef(null);
  const [waveformTime, setWaveformTime] = useState(0);
  const waveformAnimationRef = useRef(null);
  const [isMounted, setIsMounted] = useState(false);
  const [audioDataArray, setAudioDataArray] = useState(null);
  const [profileSettings, setProfileSettings] = useState({
    colorScheme: 'blueOrange',
  });
  const [useFileUpload, setUseFileUpload] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const fileInputRef = useRef(null);
  const [barWidth, setBarWidth] = useState(0);
  const [referenceAudioBlob, setReferenceAudioBlob] = useState(null); // Store reference TTS audio
  const [phonemeFeedback, setPhonemeFeedback] = useState(null); // Store phoneme-level feedback
  const [isLoadingPhonemeFeedback, setIsLoadingPhonemeFeedback] = useState(false);
  const [isPlayingFeedbackTTS, setIsPlayingFeedbackTTS] = useState(false);

  // Load profile settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('profileSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setProfileSettings(parsed);
      } catch (error) {
        console.error('Error loading profile settings:', error);
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
      primary: '#10B981', // Green (complement of pink)
      secondary: '#059669',
      light: '#34D399',
    },
    purple: {
      primary: '#F59E0B', // Yellow/Orange (complement of purple)
      secondary: '#D97706',
      light: '#FBBF24',
    },
    blue: {
      primary: '#F97316', // Orange (complement of blue)
      secondary: '#EA580C',
      light: '#FB923C',
    },
    green: {
      primary: '#EC4899', // Pink (complement of green)
      secondary: '#DB2777',
      light: '#F472B6',
    },
  };

  const currentComplement = colorComplements[profileSettings.colorScheme] || colorComplements.blueOrange;

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

  // Autoplay audio when phrase changes
  useEffect(() => {
    if (phrases[currentPhrase] && profile) {
      setHasPlayedOnce(false);
      // Small delay to ensure component is ready
      const timer = setTimeout(() => {
        // Handle autoplay errors gracefully - don't let them crash the app
        playPhrase().catch((error) => {
          console.warn('Autoplay failed (this is normal if browser blocks autoplay):', error);
          // Set hasPlayedOnce so user can still record
          setHasPlayedOnce(true);
        });
      }, 300);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPhrase]);

  // Scroll to results when they appear
  useEffect(() => {
    if (analysisResult && !isProcessing && resultsRef.current) {
      // Small delay to allow fade-in to start
      const scrollTimer = setTimeout(() => {
        const element = resultsRef.current;
        if (element) {
          const elementTop = element.getBoundingClientRect().top + window.pageYOffset;
          const offset = 100; // Offset from top of viewport
          window.scrollTo({
            top: elementTop - offset,
            behavior: 'smooth'
          });
        }
      }, 200);
      return () => clearTimeout(scrollTimer);
    }
  }, [analysisResult, isProcessing]);

  // Auto-play TTS when phoneme feedback is ready
  useEffect(() => {
    if (phonemeFeedback && !isLoadingPhonemeFeedback && !isPlayingFeedbackTTS) {
      // Small delay to ensure UI is ready
      const playTimer = setTimeout(() => {
        playPhonemeFeedbackTTS().catch((error) => {
          console.warn('Auto-play failed (this is normal if browser blocks autoplay):', error);
        });
      }, 500);
      return () => clearTimeout(playTimer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phonemeFeedback, isLoadingPhonemeFeedback]);

  // Cleanup: Stop TTS when component unmounts or page is left
  useEffect(() => {
    return () => {
      // Stop feedback TTS if playing
      if (feedbackAudioRef.current) {
        feedbackAudioRef.current.pause();
        feedbackAudioRef.current.currentTime = 0;
        feedbackAudioRef.current = null;
      }
    };
  }, []);

  // Animate waveform when recording - reactive to mic input
  useEffect(() => {
    if (isRecording && audioCapture && audioCapture.analyser) {
      console.log('🎙️ Starting reactive waveform animation');
      const analyser = audioCapture.analyser;
      // Use time domain data for actual waveform shape
      const dataArray = new Uint8Array(analyser.fftSize);
      
      const animate = () => {
        // Get time domain data (actual waveform shape)
        analyser.getByteTimeDomainData(dataArray);
        
        // Check if there's actual audio input (not just silence) - more sensitive
        let hasAudio = false;
        for (let i = 0; i < dataArray.length; i++) {
          // Check if values deviate from silence (128 is center, 0-255 range)
          // Lowered threshold from 2 to 0.5 for more sensitivity
          if (Math.abs(dataArray[i] - 128) > 0.5) {
            hasAudio = true;
            break;
          }
        }
        
        if (hasAudio) {
          setAudioDataArray([...dataArray]);
        } else {
          // Set to null to show flat line when no audio
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

  const playPhrase = async () => {
    console.log('🎵 Play Phrase clicked');
    setIsPlaying(true);
    try {
      // Use ElevenLabs TTS via backend
      // Extract accent name (e.g., "American English" -> "american")
      const accentString = typeof profile?.accent === 'object' 
        ? profile.accent?.name || profile.accent?.id
        : profile?.accent;
      const accentName = accentString 
        ? String(accentString).toLowerCase().replace(' english', '').replace('english', '').trim()
        : null;
      
      console.log('🎵 Calling ElevenLabs TTS service:', {
        phrase: phrases[currentPhrase],
        accentName,
        profileAccent: profile?.accent,
        languageId: profile?.language?.id
      });
      
      // Ensure we're using ElevenLabs - no fallback
      const audioBlob = await ttsService.generateSpeech(
        phrases[currentPhrase],
        null, // voice_id - will use accent-based selection from backend
        accentName, // accent name for voice selection (MUST be provided)
        false // robotic = false for practice phrases (natural voice)
      );
      
      console.log('🎵 Received audio blob:', {
        exists: !!audioBlob,
        size: audioBlob?.size,
        type: audioBlob?.type,
        constructor: audioBlob?.constructor?.name
      });
      
      // Validate audio blob
      if (!audioBlob || audioBlob.size === 0) {
        console.error('❌ Empty or invalid audio blob received');
        throw new Error('Received empty audio blob from TTS service');
      }
      
      // Store reference audio for phoneme comparison
      setReferenceAudioBlob(audioBlob);
      console.log('✅ Stored reference audio blob for phoneme analysis');
      
      // Create audio element and play immediately
      console.log('🎵 Creating audio element from blob');
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      // Set volume
      audio.volume = 1.0;
      
      // Set up event handlers
      audio.onended = () => {
        setIsPlaying(false);
        setHasPlayedOnce(true);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = (error) => {
        console.error('Error playing audio:', error);
        setIsPlaying(false);
        setHasPlayedOnce(true);
        URL.revokeObjectURL(audioUrl);
      };
      
      // Try to play immediately - don't wait for loading events
      // Blob URLs are typically ready immediately
      try {
        const playPromise = audio.play();
        
        // If play() returns a promise, handle it
        if (playPromise !== undefined) {
          await playPromise;
          console.log('✅ Audio playback started successfully');
        } else {
          console.log('✅ Audio playback started (no promise)');
        }
      } catch (playError) {
        console.error('Error playing audio:', playError);
        
        // If autoplay is blocked, wait briefly and try again
        if (playError.name === 'NotAllowedError' || playError.name === 'NotSupportedError') {
          console.log('⏳ Autoplay blocked, waiting for audio to load...');
          // Wait for canplay event (should be very quick for blob URLs)
          await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
              audio.removeEventListener('canplay', onCanPlay);
              audio.removeEventListener('error', onError);
              reject(new Error('Audio loading timeout'));
            }, 2000); // Shorter timeout - 2 seconds
            
            const onCanPlay = () => {
              clearTimeout(timeout);
              audio.removeEventListener('canplay', onCanPlay);
              audio.removeEventListener('error', onError);
              resolve();
            };
            
            const onError = (err) => {
              clearTimeout(timeout);
              audio.removeEventListener('canplay', onCanPlay);
              audio.removeEventListener('error', onError);
              reject(err);
            };
            
            if (audio.readyState >= 2) {
              clearTimeout(timeout);
              resolve();
            } else {
              audio.addEventListener('canplay', onCanPlay);
              audio.addEventListener('error', onError);
            }
          });
          
          // Try playing again after waiting
          try {
            await audio.play();
            console.log('✅ Audio playback started after waiting');
          } catch (retryError) {
            // Autoplay is still blocked - handle gracefully
            console.warn('⚠️ Audio playback still blocked after retry - user can click Replay button');
            setIsPlaying(false);
            setHasPlayedOnce(true); // Allow recording even if audio didn't play
            // Don't show alert - just log and allow user to continue
            return; // Exit gracefully without throwing
          }
        } else {
          throw playError;
        }
      }
    } catch (error) {
      console.error('❌ Error generating/playing TTS with ElevenLabs:', error);
      setIsPlaying(false);
      setHasPlayedOnce(true); // Allow recording even if audio failed
      
      // Show user-friendly error message
      const errorMessage = error.message || 'Failed to generate audio with ElevenLabs';
      
      // Only show alert for non-autoplay errors
      if (!errorMessage.includes('Audio playback blocked')) {
      alert(`Unable to play audio: ${errorMessage}\n\nPlease ensure:\n- Backend server is running\n- ElevenLabs API key is configured\n- Check browser console for details`);
      }
      
      // Don't re-throw - allow user to continue
      return;
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
      setAudioData(audioBlob);
      setShowWaveform(true);
      
      // Detect accent from the recording
      console.log('🎤 Detecting accent from recording...');
      const result = await accentDetectionService.detectAccent(audioBlob);
      console.log('✅ Accent detection result:', result);
      
      // Calculate accent evaluation score based on English confidence
      const targetAccent = typeof profile?.accent === 'object' 
        ? profile.accent?.name || profile.accent?.id 
        : profile?.accent;
      const targetAccentLower = String(targetAccent || '').toLowerCase();
      const targetLanguageId = profile?.language?.id || profile?.language;
      const languageIdLower = String(targetLanguageId || '').toLowerCase();
      
      // Check if target is English (by language ID or accent name)
      const isTargetEnglish = languageIdLower === 'english' || 
                              targetAccentLower.includes('english') || 
                              targetAccentLower === 'english';
      
      // Find English confidence from top predictions or predicted accent
      let englishConfidence = 0;
      
      // First check if the predicted accent itself is English
      if (result.predicted_accent && result.predicted_accent.toLowerCase().includes('english')) {
        englishConfidence = result.confidence || 0;
      } else if (result.top_predictions && Array.isArray(result.top_predictions)) {
        // Otherwise, find English in top predictions
        const englishPred = result.top_predictions.find(p => 
          p.accent && p.accent.toLowerCase().includes('english')
        );
        englishConfidence = englishPred?.confidence || 0;
      }
      
      // Calculate accent evaluation score
      // If target IS English: Higher English confidence = Higher score (better accent replication)
      // If target is NOT English: Lower English confidence = Higher score (better accent replication)
      let accentEvaluationScore;
      if (isTargetEnglish) {
        // For English accents: Higher English confidence = Better
        accentEvaluationScore = englishConfidence;
      } else {
        // For non-English accents: Lower English confidence = Better (100 - englishConfidence)
        accentEvaluationScore = Math.max(0, 100 - englishConfidence);
      }
      
      // Add evaluation score to result
      const resultWithEvaluation = {
        ...result,
        accent_evaluation_score: accentEvaluationScore,
        english_confidence: englishConfidence,
        target_accent: targetAccent,
        is_target_english: isTargetEnglish
      };
      
      setAnalysisResult(resultWithEvaluation);
      setIsProcessing(false);
      
      // Reset and animate bar width
      setBarWidth(0);
      setTimeout(() => {
        setBarWidth(Math.min(accentEvaluationScore || 0, 100));
      }, 300);
      
      // Get phoneme-level feedback if reference audio is available
      if (referenceAudioBlob && audioBlob) {
        setIsLoadingPhonemeFeedback(true);
        try {
          const languageCode = profile?.language?.id || profile?.language;
          console.log('🎯 Getting phoneme-level feedback...');
          const phonemeResult = await accentDetectionService.getPhonemeFeedback(
            referenceAudioBlob,
            audioBlob,
            phrases[currentPhrase],
            languageCode,
            accentEvaluationScore // Pass accent evaluation score
          );
          console.log('✅ Received phoneme feedback:', phonemeResult);
          setPhonemeFeedback(phonemeResult);
        } catch (error) {
          console.error('Error getting phoneme feedback:', error);
          // Don't show error to user - phoneme feedback is optional
          setPhonemeFeedback(null);
        } finally {
          setIsLoadingPhonemeFeedback(false);
        }
      }
      
    } catch (error) {
      console.error('Error detecting accent:', error);
      setIsProcessing(false);
      const errorMessage = error.response?.data?.detail || error.message || 'Error detecting accent. Please try again.';
      alert(errorMessage);
    }
  };

  const nextPhrase = () => {
    // Stop feedback TTS if playing
    if (feedbackAudioRef.current) {
      feedbackAudioRef.current.pause();
      feedbackAudioRef.current.currentTime = 0;
      feedbackAudioRef.current = null;
    }
    
    // Clean up audio visualization
    if (feedbackAnimationFrameRef.current) {
      cancelAnimationFrame(feedbackAnimationFrameRef.current);
      feedbackAnimationFrameRef.current = null;
    }
    if (feedbackAudioContextRef.current) {
      feedbackAudioContextRef.current.close().catch(() => {});
      feedbackAudioContextRef.current = null;
    }
    setFeedbackAudioLevels([]);
    feedbackAnalyserRef.current = null;
    
    if (currentPhrase < phrases.length - 1) {
      setCurrentPhrase(currentPhrase + 1);
      setShowWaveform(false);
      setAudioData(null);
      setAnalysisResult(null);
      setHasPlayedOnce(false);
      setBarWidth(0);
      setUploadedFile(null);
      setUseFileUpload(false);
      setReferenceAudioBlob(null);
      setPhonemeFeedback(null);
      setIsPlayingFeedbackTTS(false);
    } else {
      // Practice complete
      navigate('/dashboard', { state: { practiceComplete: true, isCurated } });
    }
  };

  // Play phoneme feedback using TTS
  const playPhonemeFeedbackTTS = async () => {
    if (!phonemeFeedback || isPlayingFeedbackTTS) return;
    
    try {
      setIsPlayingFeedbackTTS(true);
      
      // Combine feedback text into a natural script (exclude Practice Recommendations and Specific Areas)
      let feedbackText = phonemeFeedback.feedback || '';
      
      // Remove "Practice Recommendations" section
      feedbackText = feedbackText.replace(/\*\*Practice Recommendations\*\*\s*\n/g, '');
      feedbackText = feedbackText.replace(/Practice Recommendations\s*\n/g, '');
      feedbackText = feedbackText.replace(/-\s*Record yourself again[^\n]*/g, '');
      feedbackText = feedbackText.replace(/-\s*Listen to the reference[^\n]*/g, '');
      feedbackText = feedbackText.replace(/-\s*Practice saying[^\n]*/g, '');
      feedbackText = feedbackText.replace(/-\s*Focus on matching[^\n]*/g, '');
      feedbackText = feedbackText.replace(/-\s*Pay attention[^\n]*/g, '');
      
      // Remove markdown formatting for TTS
      feedbackText = feedbackText
        .replace(/\*\*/g, '') // Remove bold markers
        .replace(/\*/g, '') // Remove italic markers
        .replace(/##/g, '') // Remove headers
        .replace(/#/g, '') // Remove headers
        .replace(/\n\n+/g, '. ') // Replace multiple newlines with periods
        .replace(/\n/g, ' ') // Replace single newlines with spaces
        .trim();
      
      // Don't add specific improvements to TTS - user requested to exclude this
      
      // Get accent name for TTS (use profile accent or default to beijing)
      const accentName = profile?.accent?.name || profile?.accent || "beijing";
      
      console.log('🎤 Generating TTS for phoneme feedback:', feedbackText.substring(0, 100));
      
      // Generate speech using TTS service
      const audioBlob = await ttsService.generateSpeech(
        feedbackText,
        null, // voice_id - will use accent-based selection from backend
        accentName, // accent name for voice selection
        false // robotic = false (natural voice)
      );
      
      if (!audioBlob || audioBlob.size === 0) {
        throw new Error('Received empty audio blob from TTS service');
      }
      
      // Create audio element and play
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      feedbackAudioRef.current = audio; // Store reference for cleanup
      
      // Set up Web Audio API for visualization
      let analyser = null;
      let audioContext = null;
      
      try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Resume audio context if suspended (required by some browsers)
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
        
        const source = audioContext.createMediaElementSource(audio);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256; // For frequency analysis
        analyser.smoothingTimeConstant = 0.8; // Smooth the data
        source.connect(analyser);
        analyser.connect(audioContext.destination);
        
        feedbackAnalyserRef.current = analyser;
        feedbackAudioContextRef.current = audioContext;
        
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        feedbackFrequencyDataRef.current = dataArray;
        
        // Start visualization animation - use a function that checks the actual audio state
        const startAnimation = () => {
          const animate = () => {
            const currentAudio = feedbackAudioRef.current;
            const currentAnalyser = feedbackAnalyserRef.current;
            
            if (!currentAnalyser || !currentAudio || currentAudio.paused || currentAudio.ended) {
              setFeedbackAudioLevels([]);
              if (feedbackAnimationFrameRef.current) {
                cancelAnimationFrame(feedbackAnimationFrameRef.current);
                feedbackAnimationFrameRef.current = null;
              }
              return;
            }
            
            currentAnalyser.getByteFrequencyData(dataArray);
            
            // Create visualizer bars (20 bars for smooth animation)
            const barCount = 20;
            const levels = [];
            const step = Math.floor(bufferLength / barCount);
            
            for (let i = 0; i < barCount; i++) {
              const index = i * step;
              // Use average of nearby frequencies for smoother visualization
              let sum = 0;
              let count = 0;
              for (let j = Math.max(0, index - 2); j < Math.min(bufferLength, index + 3); j++) {
                sum += dataArray[j];
                count++;
              }
              const value = (sum / count) / 255; // Normalize to 0-1
              // Apply smoothing and boost for better visibility
              const smoothedValue = Math.min(1, value * 2.0);
              levels.push(smoothedValue);
            }
            
            setFeedbackAudioLevels(levels);
            feedbackAnimationFrameRef.current = requestAnimationFrame(animate);
          };
          
          animate();
        };
        
        // Start animation after audio starts playing
        audio.addEventListener('play', () => {
          console.log('🎵 Audio started playing, starting visualizer');
          startAnimation();
        }, { once: true });
        
        // Also try to start immediately in case play event already fired
        if (!audio.paused) {
          startAnimation();
        }
        
      } catch (error) {
        console.warn('Could not set up audio visualization:', error);
      }
      
      // Clean up URL when done
      audio.addEventListener('ended', () => {
        console.log('🎵 Audio ended, cleaning up visualizer');
        URL.revokeObjectURL(audioUrl);
        setIsPlayingFeedbackTTS(false);
        setFeedbackAudioLevels([]);
        feedbackAudioRef.current = null;
        
        // Clean up audio context
        if (feedbackAnimationFrameRef.current) {
          cancelAnimationFrame(feedbackAnimationFrameRef.current);
          feedbackAnimationFrameRef.current = null;
        }
        if (feedbackAudioContextRef.current) {
          feedbackAudioContextRef.current.close().catch(() => {});
          feedbackAudioContextRef.current = null;
        }
        feedbackAnalyserRef.current = null;
      });
      
      audio.addEventListener('error', (error) => {
        console.error('Error playing feedback audio:', error);
        URL.revokeObjectURL(audioUrl);
        setIsPlayingFeedbackTTS(false);
        setFeedbackAudioLevels([]);
        feedbackAudioRef.current = null;
        
        // Clean up audio context
        if (feedbackAnimationFrameRef.current) {
          cancelAnimationFrame(feedbackAnimationFrameRef.current);
          feedbackAnimationFrameRef.current = null;
        }
        if (feedbackAudioContextRef.current) {
          feedbackAudioContextRef.current.close().catch(() => {});
          feedbackAudioContextRef.current = null;
        }
        feedbackAnalyserRef.current = null;
      });
      
      audio.volume = 1.0;
      await audio.play();
      
      // Start animation immediately after play() resolves
      if (analyser && !audio.paused) {
        const animate = () => {
          const currentAudio = feedbackAudioRef.current;
          const currentAnalyser = feedbackAnalyserRef.current;
          
          if (!currentAnalyser || !currentAudio || currentAudio.paused || currentAudio.ended) {
            setFeedbackAudioLevels([]);
            if (feedbackAnimationFrameRef.current) {
              cancelAnimationFrame(feedbackAnimationFrameRef.current);
              feedbackAnimationFrameRef.current = null;
            }
            return;
          }
          
          currentAnalyser.getByteFrequencyData(feedbackFrequencyDataRef.current);
          
          const barCount = 20;
          const levels = [];
          const step = Math.floor(feedbackFrequencyDataRef.current.length / barCount);
          
          for (let i = 0; i < barCount; i++) {
            const index = i * step;
            let sum = 0;
            let count = 0;
            for (let j = Math.max(0, index - 2); j < Math.min(feedbackFrequencyDataRef.current.length, index + 3); j++) {
              sum += feedbackFrequencyDataRef.current[j];
              count++;
            }
            const value = (sum / count) / 255;
            const smoothedValue = Math.min(1, value * 2.0);
            levels.push(smoothedValue);
          }
          
          setFeedbackAudioLevels(levels);
          feedbackAnimationFrameRef.current = requestAnimationFrame(animate);
        };
        
        animate();
      }
      
    } catch (error) {
      console.error('Error playing phoneme feedback TTS:', error);
      setIsPlayingFeedbackTTS(false);
      alert('Failed to play feedback audio. Please try again.');
    }
  };

  const retry = () => {
    setShowWaveform(false);
    setAudioData(null);
    setAnalysisResult(null);
    setUploadedFile(null);
    setBarWidth(0);
    setPhonemeFeedback(null);
    setIsPlayingFeedbackTTS(false);
    // Stop feedback TTS if playing
    if (feedbackAudioRef.current) {
      feedbackAudioRef.current.pause();
      feedbackAudioRef.current.currentTime = 0;
      feedbackAudioRef.current = null;
    }
    
    // Clean up audio visualization
    if (feedbackAnimationFrameRef.current) {
      cancelAnimationFrame(feedbackAnimationFrameRef.current);
      feedbackAnimationFrameRef.current = null;
    }
    if (feedbackAudioContextRef.current) {
      feedbackAudioContextRef.current.close().catch(() => {});
      feedbackAudioContextRef.current = null;
    }
    setFeedbackAudioLevels([]);
    feedbackAnalyserRef.current = null;
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    
    setIsProcessing(true);
    setAnalysisResult(null);
    setUploadedFile(file);
    
    try {
      console.log('📁 Detecting accent from uploaded file:', file.name);
      
      // Detect accent from the uploaded file
      const result = await accentDetectionService.detectAccent(file);
      
      console.log('✅ Accent detection result:', result);
      
      // Calculate accent evaluation score based on English confidence
      const targetAccent = typeof profile?.accent === 'object' 
        ? profile.accent?.name || profile.accent?.id 
        : profile?.accent;
      const targetAccentLower = String(targetAccent || '').toLowerCase();
      const targetLanguageId = profile?.language?.id || profile?.language;
      const languageIdLower = String(targetLanguageId || '').toLowerCase();
      
      // Check if target is English (by language ID or accent name)
      const isTargetEnglish = languageIdLower === 'english' || 
                              targetAccentLower.includes('english') || 
                              targetAccentLower === 'english';
      
      // Find English confidence from top predictions or predicted accent
      let englishConfidence = 0;
      
      // First check if the predicted accent itself is English
      if (result.predicted_accent && result.predicted_accent.toLowerCase().includes('english')) {
        englishConfidence = result.confidence || 0;
      } else if (result.top_predictions && Array.isArray(result.top_predictions)) {
        // Otherwise, find English in top predictions
        const englishPred = result.top_predictions.find(p => 
          p.accent && p.accent.toLowerCase().includes('english')
        );
        englishConfidence = englishPred?.confidence || 0;
      }
      
      // Calculate accent evaluation score
      // If target IS English: Higher English confidence = Higher score (better accent replication)
      // If target is NOT English: Lower English confidence = Higher score (better accent replication)
      let accentEvaluationScore;
      if (isTargetEnglish) {
        // For English accents: Higher English confidence = Better
        accentEvaluationScore = englishConfidence;
      } else {
        // For non-English accents: Lower English confidence = Better (100 - englishConfidence)
        accentEvaluationScore = Math.max(0, 100 - englishConfidence);
      }
      
      // Add evaluation score to result
      const resultWithEvaluation = {
        ...result,
        accent_evaluation_score: accentEvaluationScore,
        english_confidence: englishConfidence,
        target_accent: targetAccent,
        is_target_english: isTargetEnglish
      };
      
      setAnalysisResult(resultWithEvaluation);
      
      // Reset and animate bar width
      setBarWidth(0);
      setTimeout(() => {
        setBarWidth(Math.min(accentEvaluationScore || 0, 100));
      }, 300);
      
      // Get phoneme-level feedback if reference audio is available
      if (referenceAudioBlob && file) {
        setIsLoadingPhonemeFeedback(true);
        try {
          const languageCode = profile?.language?.id || profile?.language;
          console.log('🎯 Getting phoneme-level feedback from file upload...');
          const phonemeResult = await accentDetectionService.getPhonemeFeedback(
            referenceAudioBlob,
            file,
            phrases[currentPhrase],
            languageCode,
            accentEvaluationScore // Pass accent evaluation score
          );
          console.log('✅ Received phoneme feedback:', phonemeResult);
          setPhonemeFeedback(phonemeResult);
        } catch (error) {
          console.error('Error getting phoneme feedback:', error);
          // Don't show error to user - phoneme feedback is optional
          setPhonemeFeedback(null);
        } finally {
          setIsLoadingPhonemeFeedback(false);
        }
      }
    } catch (error) {
      console.error('❌ Accent detection error:', error);
      setAnalysisResult({
        error: error.response?.data?.detail || error.message || 'Failed to detect accent. Please try again.',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <style>{`
        @keyframes scaleInBounce {
          0% {
            opacity: 0;
            transform: scale(0.8) translateY(20px);
          }
          50% {
            transform: scale(1.05) translateY(-5px);
          }
          100% {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        @keyframes waterFill {
          from {
            width: 0%;
          }
          to {
            width: 100%;
          }
        }
        
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(200%);
          }
        }
        
        @keyframes spillOverflow {
          0% {
            opacity: 0;
            transform: translateX(0) scaleY(1);
          }
          50% {
            opacity: 0.8;
            transform: translateX(4px) scaleY(1.2);
          }
          100% {
            opacity: 0.4;
            transform: translateX(8px) scaleY(0.8);
          }
        }
        
        @keyframes loadingBar {
          0%, 100% {
            transform: scaleY(0.3);
            opacity: 0.7;
          }
          50% {
            transform: scaleY(1);
            opacity: 1;
          }
        }
        
        @keyframes circleFill {
          0% {
            stroke-dashoffset: 314.16;
          }
          100% {
            stroke-dashoffset: var(--target-offset);
          }
        }
      `}</style>
    <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.backgroundGradient} flex flex-col opacity-90`}>
      {/* Progress Bar at Top */}
      <div className={`w-full px-4 pt-4 pb-2 transition-all duration-700 ${
        isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
      }`}>
        <div className="max-w-7xl mx-auto">
          {/* Question Number */}
          <div className="flex justify-between items-center mb-2">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-white hover:text-gray-200 flex items-center drop-shadow-lg"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <span className="text-white text-xl font-semibold drop-shadow-lg">
              {currentPhrase + 1} / {phrases.length}
            </span>
          </div>
          {/* Progress Bar */}
          <div className="bg-white/30 rounded-full h-3 shadow-lg">
            <div
              className="bg-white h-3 rounded-full transition-all duration-300 shadow-md"
              style={{ width: `${((currentPhrase + 1) / phrases.length) * 100}%` }}
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
          {/* Static Content Section - Centered (takes available space, results expand below) */}
          <div className="flex-shrink-0 flex flex-col items-center justify-center relative" style={{ minHeight: '400px', paddingTop: '80px' }}>
            {/* Timer - Absolute positioned at top */}
            {timedMode && isRecording && (
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 mb-6 text-center">
                <div className="inline-block bg-accenta-primary/20 rounded-full px-6 py-2">
                  <span className="text-accenta-primary text-2xl font-bold">{timeRemaining}s</span>
                </div>
              </div>
            )}
            
            {/* Phrase - Centered in available space */}
            <div className={`text-center transition-all duration-700 delay-200 flex items-center justify-center ${
              isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`} style={{ width: '100%', justifyContent: 'center', alignItems: 'center' }}>
              <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight text-gray-900 text-center px-4">
                {phrases[currentPhrase]}
              </h2>
            </div>

            {/* Replay Button - Below phrase */}
            <div className={`flex justify-center mt-6 transition-opacity duration-300 ${hasPlayedOnce && !isPlaying ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
              <button
                onClick={playPhrase}
                disabled={isRecording || isPlaying || !hasPlayedOnce}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" />
                </svg>
                Replay
              </button>
            </div>

            {/* Toggle between Microphone and File Upload */}
            <div className="flex justify-center gap-4 mt-4 mb-2">
              <button
                onClick={() => setUseFileUpload(false)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  !useFileUpload
                    ? 'bg-accenta-primary text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🎤 Microphone
              </button>
              <button
                onClick={() => {
                  setUseFileUpload(true);
                  fileInputRef.current?.click();
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  useFileUpload
                    ? 'bg-accenta-primary text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                📁 Upload File
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*,.mp3,.wav,.m4a,.flac,.webm,.ogg"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            {/* Show uploaded file name */}
            {uploadedFile && (
              <div className="text-center mt-2 mb-2">
                <span className="text-sm text-gray-600">
                  📄 {uploadedFile.name}
                </span>
              </div>
            )}

            {/* Recording Button with Waveform Animation - Below replay */}
            {!useFileUpload && (
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
                      <linearGradient id={`waveGradient-${currentPhrase}`} x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor={currentComplement.light} stopOpacity="0.3" />
                        <stop offset="50%" stopColor={currentComplement.primary} stopOpacity="1" />
                        <stop offset="100%" stopColor={currentComplement.light} stopOpacity="0.3" />
                      </linearGradient>
                    </defs>
                    {/* Three wavy lines - flat normally, reactive to audio */}
                    {[0, 1, 2].map((lineIndex) => {
                      const centerY = 100;
                      const offset = 0; // All lines overlap at the same position
                      const points = [];
                      const numPoints = 200;
                      
                      // Use real audio data if available, otherwise show flat line
                      if (audioDataArray && audioDataArray.length > 0) {
                        // Map time domain audio data to waveform
                        const dataLength = audioDataArray.length;
                        const samplesPerPoint = Math.max(1, Math.floor(dataLength / numPoints));
                        
                        for (let i = 0; i <= numPoints; i++) {
                          const x = (i / numPoints) * 400;
                          const dataIndex = Math.min(Math.floor((i / numPoints) * dataLength), dataLength - 1);
                          
                          // Get average of nearby samples for smoother waveform
                          let sum = 0;
                          let count = 0;
                          for (let j = 0; j < samplesPerPoint && (dataIndex + j) < dataLength; j++) {
                            sum += audioDataArray[dataIndex + j];
                            count++;
                          }
                          const avgValue = count > 0 ? sum / count : 128; // 128 is center (silence)
                          
                          // Convert audio data (0-255, where 128 is center) to y position
                          // Apply center-focused amplitude scaling
                          const centerDistance = Math.abs(x - 200) / 200; // 0 at center, 1 at edges
                          const baseAmplitude = (1 - centerDistance) * 25 + 5; // Max 30 at center, min 5 at edges
                          
                          // Normalize audio value: 0-255 -> -1 to 1 (128 is 0)
                          // Increase sensitivity by amplifying the signal
                          const normalizedAudio = (avgValue - 128) / 128;
                          const amplifiedAudio = normalizedAudio * 2.5; // Amplify by 2.5x for more sensitivity
                          const audioAmplitude = amplifiedAudio * baseAmplitude;
                          
                          // Add slight phase offset for each line
                          const phase = lineIndex * Math.PI / 4;
                          const y = centerY + offset + audioAmplitude + Math.sin((x * 0.01) + phase) * 2;
                          points.push(`${x},${y}`);
                        }
                      } else {
                        // Flat line when no audio input
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
                          stroke={`url(#waveGradient-${currentPhrase})`}
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
                    disabled={isPlaying || !audioCapture}
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
            )}

            {/* File Upload Area - Shown when useFileUpload is true */}
            {useFileUpload && (
              <div className="flex flex-col items-center justify-center relative mt-6" style={{ minHeight: '200px', width: '400px' }}>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-accenta-primary transition-colors cursor-pointer"
                     onClick={() => fileInputRef.current?.click()}>
                  <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-gray-600 font-medium">Click to upload audio file</p>
                  <p className="text-gray-400 text-sm mt-2">MP3, WAV, M4A, FLAC, WebM, OGG</p>
                  {uploadedFile && (
                    <p className="text-accenta-primary text-sm mt-2 font-semibold">
                      ✓ {uploadedFile.name}
                    </p>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,.mp3,.wav,.m4a,.flac,.webm,.ogg"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            )}

          </div>

          {/* Expandable Results Section */}
          <div className="flex-shrink-0" ref={resultsRef}>
            {/* Processing Indicator */}
            {isProcessing && (
              <div className="text-center text-gray-600 mt-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accenta-primary"></div>
                <p className="mt-2">Detecting accent...</p>
              </div>
            )}

            {/* Accent Detection Results */}
            {analysisResult && !isProcessing && (
              <div className="mt-8">
              {/* Accent Evaluation Score - Visual Circular Progress with Water Animation */}
              {analysisResult.accent_evaluation_score !== undefined && (
                <div 
                  className="mb-6 p-6 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 rounded-2xl border-2 border-purple-200 shadow-lg relative overflow-hidden"
                  style={{ 
                    animation: 'scaleInBounce 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
                    opacity: 0,
                    transform: 'scale(0.8)'
                  }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xl font-bold text-gray-800">Accent Evaluation Score</span>
                  </div>
                  
                  {/* Circular Progress Ring */}
                  <div className="flex items-center justify-center mb-4">
                    <div className="relative w-48 h-48">
                      <svg className="transform -rotate-90 w-48 h-48" viewBox="0 0 120 120">
                        {/* Background circle */}
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="none"
                          stroke="#E5E7EB"
                          strokeWidth="8"
                        />
                        {/* Progress circle with animation */}
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="none"
                          stroke={
                            analysisResult.accent_evaluation_score >= 80 ? '#10B981' :
                            analysisResult.accent_evaluation_score >= 60 ? '#F59E0B' :
                            '#EF4444'
                          }
                          strokeWidth="8"
                          strokeLinecap="round"
                          strokeDasharray={`${2 * Math.PI * 50}`}
                          strokeDashoffset={`${2 * Math.PI * 50}`}
                          style={{
                            filter: analysisResult.accent_evaluation_score >= 80 ? 'drop-shadow(0 0 8px rgba(16, 185, 129, 0.5))' :
                                    analysisResult.accent_evaluation_score >= 60 ? 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.5))' :
                                    'drop-shadow(0 0 8px rgba(239, 68, 68, 0.5))',
                            animation: 'circleFill 1.2s ease-out forwards',
                            animationDelay: '0.2s',
                            '--target-offset': `${2 * Math.PI * 50 * (1 - (analysisResult.accent_evaluation_score || 0) / 100)}`
                          }}
                        />
                      </svg>
                      {/* Center text */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className={`text-5xl font-bold ${
                          analysisResult.accent_evaluation_score >= 80 ? 'text-green-600' :
                          analysisResult.accent_evaluation_score >= 60 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {analysisResult.accent_evaluation_score.toFixed(0)}
                        </span>
                        <span className="text-lg text-gray-600 font-semibold">%</span>
                        <span className={`text-xs font-medium mt-1 ${
                          analysisResult.accent_evaluation_score >= 80 ? 'text-green-700' :
                          analysisResult.accent_evaluation_score >= 60 ? 'text-yellow-700' :
                          'text-red-700'
                        }`}>
                          {analysisResult.accent_evaluation_score >= 80 ? 'Excellent!' :
                           analysisResult.accent_evaluation_score >= 60 ? 'Good' :
                           'Keep Practicing'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Linear Progress Bar with Water Fill Animation */}
                  <div className="relative w-full bg-gray-200 rounded-full h-4 mb-3 overflow-hidden">
                    {/* Water fill effect */}
                    <div
                      className={`h-full rounded-full relative overflow-hidden ${
                        analysisResult.accent_evaluation_score >= 80 ? 'bg-gradient-to-r from-green-500 via-emerald-400 to-green-500' :
                        analysisResult.accent_evaluation_score >= 60 ? 'bg-gradient-to-r from-yellow-500 via-orange-400 to-yellow-500' :
                        'bg-gradient-to-r from-red-500 via-pink-400 to-red-500'
                      }`}
                      style={{ 
                        width: '0%',
                        animation: `waterFill 1.5s ease-out forwards`,
                        animationDelay: '0.3s',
                        '--target-width': `${Math.min(analysisResult.accent_evaluation_score || 0, 100)}%`
                      }}
                    >
                      {/* Water shimmer effect */}
                      <div 
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                        style={{
                          animation: 'shimmer 2s infinite',
                          transform: 'translateX(-100%)'
                        }}
                      />
                    </div>
                    
                    {/* Spill effect on the right side when score is high */}
                    {analysisResult.accent_evaluation_score >= 90 && (
                      <div 
                        className="absolute right-0 top-0 h-full w-2 opacity-0"
                        style={{
                          animation: 'spillOverflow 0.6s ease-out forwards',
                          animationDelay: '1.8s',
                          background: analysisResult.accent_evaluation_score >= 80 
                            ? 'linear-gradient(to right, rgba(16, 185, 129, 0.6), transparent)'
                            : 'linear-gradient(to right, rgba(245, 158, 11, 0.6), transparent)'
                        }}
                      />
                    )}
                  </div>
                  
                  {/* Score breakdown */}
                  <div className="grid grid-cols-2 gap-3 mt-4">
                    <div className="bg-white/70 rounded-lg p-3 border border-gray-200">
                      <p className="text-xs text-gray-600 mb-1">English Confidence</p>
                      <p className="text-lg font-bold text-gray-800">
                        {analysisResult.english_confidence?.toFixed(1) || 0}%
                      </p>
                    </div>
                    <div className="bg-white/70 rounded-lg p-3 border border-gray-200">
                      <p className="text-xs text-gray-600 mb-1">Target Accent</p>
                      <p className="text-lg font-bold text-gray-800 capitalize">
                        {analysisResult.target_accent || 'N/A'}
                      </p>
                </div>
                  </div>
                  
                  <p className="text-xs text-gray-600 mt-3 text-center">
                    {analysisResult.is_target_english
                      ? "Higher English confidence = Better accent replication"
                      : "Lower English confidence = Better accent replication"
                    }
                  </p>
                </div>
              )}
              
              {/* Phoneme-Level Feedback */}
              {phonemeFeedback && !isLoadingPhonemeFeedback && (
                <div className="mt-6 p-6 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl border-2 border-indigo-200 shadow-lg relative">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-800">🎯 Detailed Phoneme Analysis</h3>
                    <div className="flex items-center gap-3">
                      {/* Audio Visualizer - shows when TTS is playing */}
                      {isPlayingFeedbackTTS && (
                        <div className="flex items-end gap-0.5 h-10 px-3 bg-indigo-100 rounded-full">
                          {feedbackAudioLevels.length > 0 ? (
                            feedbackAudioLevels.map((level, i) => (
                              <div
                                key={i}
                                className="w-1.5 bg-gradient-to-t from-indigo-500 via-purple-500 to-pink-500 rounded-full"
                                style={{
                                  height: `${Math.max(8, level * 100)}%`,
                                  minHeight: '8px',
                                  transition: 'height 0.1s ease-out'
                                }}
                              />
                            ))
                          ) : (
                            // Show placeholder bars while initializing
                            Array.from({ length: 20 }).map((_, i) => (
                              <div
                                key={i}
                                className="w-1.5 bg-indigo-300 rounded-full"
                                style={{
                                  height: '8px'
                                }}
                              />
                            ))
                          )}
                        </div>
                      )}
                      <button
                        onClick={playPhonemeFeedbackTTS}
                        disabled={isPlayingFeedbackTTS}
                        className={`p-2 rounded-full transition-all duration-200 ${
                          isPlayingFeedbackTTS
                            ? 'bg-indigo-600 text-white cursor-not-allowed'
                            : 'bg-indigo-100 hover:bg-indigo-200 text-indigo-700 hover:text-indigo-800'
                        }`}
                        title="Listen to feedback"
                      >
                        {isPlayingFeedbackTTS ? (
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                          </svg>
                        )}
                      </button>
                </div>
              </div>

                  <div className="space-y-4">
                    {/* Transcriptions */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white/70 rounded-lg p-3 border border-gray-200">
                        <p className="text-xs text-gray-600 mb-1">Target Text</p>
                        <p className="text-sm font-semibold text-gray-800">{phonemeFeedback.target_text}</p>
                </div>
                      <div className="bg-white/70 rounded-lg p-3 border border-gray-200">
                        <p className="text-xs text-gray-600 mb-1">You Said</p>
                        <p className="text-sm font-semibold text-gray-800">{phonemeFeedback.user_text}</p>
                      </div>
                    </div>
                    
                    {/* Phoneme Sequences */}
                    <div className="bg-white/70 rounded-lg p-3 border border-gray-200">
                      <p className="text-xs text-gray-600 mb-2">Phoneme Comparison</p>
                      <div className="space-y-2 text-xs font-mono">
                        <div>
                          <span className="text-gray-500">Target:</span>
                          <span className="ml-2 text-gray-800">{phonemeFeedback.target_phonemes}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Your:</span>
                          <span className="ml-2 text-gray-800">{phonemeFeedback.user_phonemes}</span>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-300">
                          <span className="text-gray-500">Similarity:</span>
                          <span className={`ml-2 font-bold ${
                            phonemeFeedback.similarity_score >= 0.8 ? 'text-green-600' :
                            phonemeFeedback.similarity_score >= 0.6 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {(phonemeFeedback.similarity_score * 100).toFixed(1)}%
                      </span>
                </div>
                </div>
              </div>

                    {/* Gemini Feedback */}
                    <div className="bg-white/70 rounded-lg p-4 border border-gray-200">
                      <p className="text-sm font-semibold text-gray-800 mb-2">📝 Pronunciation Feedback</p>
                      <div className="text-sm text-gray-700 whitespace-pre-wrap">
                        {phonemeFeedback.feedback}
                </div>
                    </div>
                    
                  </div>
                </div>
              )}
              
              {/* Loading indicator for phoneme feedback */}
              {isLoadingPhonemeFeedback && (
                <div className="mt-6 p-6 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl border-2 border-indigo-200 shadow-lg">
                  <div className="flex items-center justify-center space-x-4">
                    {/* Animated loading bars */}
                    <div className="flex items-end space-x-1 h-12">
                      {[0, 1, 2, 3, 4].map((i) => (
                        <div
                          key={i}
                          className="w-2 bg-gradient-to-t from-indigo-500 to-purple-500 rounded-full"
                          style={{
                            animation: `loadingBar ${1.2}s ease-in-out infinite`,
                            animationDelay: `${i * 0.15}s`,
                            height: '100%'
                          }}
                        />
                      ))}
                    </div>
                    <div className="flex flex-col">
                      <p className="text-sm font-semibold text-indigo-700">Analyzing pronunciation...</p>
                      <p className="text-xs text-indigo-500 mt-1">Extracting phonemes and comparing</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4 mt-6">
                      <button
                        onClick={retry}
                        className="flex-1 bg-yellow-500 text-white rounded-lg py-3 font-semibold hover:bg-yellow-600 transition-colors"
                      >
                  Try Again
                      </button>
                <button
                  onClick={nextPhrase}
                  className="flex-1 bg-accenta-primary text-white rounded-lg py-3 font-semibold hover:bg-accenta-secondary transition-colors"
                >
                  Next Phrase
                </button>
              </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
    </>
  );
};

export default Practice;

