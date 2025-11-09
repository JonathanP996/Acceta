import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AudioCapture from '../utils/audioCapture';
import { chatService, ttsService } from '../services/api';
import AudioReactiveAvatar from './AudioReactiveAvatar';

const LiveChat = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile: locationProfile } = location.state || {};
  
  // State for profile that can be updated dynamically
  const [profile, setProfile] = useState(locationProfile);
  
  // Load profile from localStorage if not provided via location
  useEffect(() => {
    if (!profile) {
      const storedProfile = localStorage.getItem('currentProfile');
      if (storedProfile) {
        try {
          const parsed = JSON.parse(storedProfile);
          setProfile(parsed);
        } catch (error) {
          console.error('Error parsing stored profile:', error);
        }
      }
    }
  }, []);
  
  // Listen for profile changes from dropdown
  useEffect(() => {
    const handleProfileChange = (event) => {
      const newProfile = event.detail;
      setProfile(newProfile);
      console.log('🔄 Profile updated in LiveChat component:', {
        language: typeof newProfile.language === 'object' ? newProfile.language?.name : newProfile.language,
        accent: typeof newProfile.accent === 'object' ? newProfile.accent?.name : newProfile.accent
      });
    };
    
    const handleStorageChange = (event) => {
      if (event.key === 'currentProfile') {
        try {
          const newProfile = JSON.parse(event.newValue);
          setProfile(newProfile);
        } catch (error) {
          console.error('Error parsing profile from storage event:', error);
        }
      }
    };
    
    window.addEventListener('profileChanged', handleProfileChange);
    window.addEventListener('storage', handleStorageChange);
    
    // Also check localStorage periodically (fallback for same-tab updates)
    const checkInterval = setInterval(() => {
      const storedProfile = localStorage.getItem('currentProfile');
      if (storedProfile) {
        try {
          const parsed = JSON.parse(storedProfile);
          const currentProfileId = profile?.id || `${profile?.language?.id || 'unknown'}_${(typeof profile?.accent === 'object' ? profile?.accent?.name : profile?.accent)?.toLowerCase().replace(/\s+/g, '_') || 'unknown'}`;
          const newProfileId = parsed.id || `${parsed.language?.id || 'unknown'}_${(typeof parsed.accent === 'object' ? parsed.accent?.name : parsed.accent)?.toLowerCase().replace(/\s+/g, '_') || 'unknown'}`;
          if (currentProfileId !== newProfileId) {
            setProfile(parsed);
          }
        } catch (error) {
          // Ignore parse errors
        }
      }
    }, 1000);
    
    return () => {
      window.removeEventListener('profileChanged', handleProfileChange);
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(checkInterval);
    };
  }, [profile]);
  
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioCapture, setAudioCapture] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isRestored, setIsRestored] = useState(false); // Track if conversation was restored
  const [micError, setMicError] = useState(null); // Track microphone initialization errors
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [currentAudioBlob, setCurrentAudioBlob] = useState(null);
  const [currentAIMessage, setCurrentAIMessage] = useState('');
  const [messageAudioMap, setMessageAudioMap] = useState(new Map()); // Store audio for each message
  const [pendingAudio, setPendingAudio] = useState(null); // Audio waiting for user interaction
  const [recordingVolume, setRecordingVolume] = useState(0); // Real-time volume during recording
  const messagesEndRef = useRef(null);
  const conversationHistory = useRef([]);
  const currentAudioRef = useRef(null); // Track current audio playback
  const isMountedRef = useRef(true); // Track if component is mounted - start as true, set to false on unmount
  const hasPlayedInitialGreeting = useRef(false); // Track if initial greeting was played
  const pendingAudioRef = useRef(null); // Ref to track pending audio element
  const allAudioRefs = useRef([]); // Track all audio instances to stop them
  const isPlayingRef = useRef(false); // Guard to prevent multiple simultaneous playbacks
  const initAudioRef = useRef(false); // Track if audio capture has been initialized
  const replayingMessageIdRef = useRef(null); // Track which message is currently being replayed
  const [profileSettings, setProfileSettings] = useState({
    colorScheme: 'blueOrange',
  });

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

  // Color scheme configurations (matching Dashboard)
  const colorSchemes = {
    blueOrange: {
      backgroundGradient: 'from-blue-900 via-cyan-800 to-orange-800',
      containerGradient: 'from-blue-50 via-cyan-50 to-orange-50',
      primary: 'bg-blue-600 hover:bg-blue-700',
      primaryLight: 'bg-blue-100 hover:bg-blue-200',
      primaryText: 'text-blue-600',
      borderColor: 'border-blue-600',
      accent: 'from-blue-500 to-orange-500',
      avatarGradient: 'from-blue-500 to-cyan-600',
    },
    pink: {
      backgroundGradient: 'from-pink-400 via-rose-400 to-fuchsia-400',
      containerGradient: 'from-pink-50 via-rose-50 to-fuchsia-50',
      primary: 'bg-pink-600 hover:bg-pink-700',
      primaryLight: 'bg-pink-100 hover:bg-pink-200',
      primaryText: 'text-pink-600',
      borderColor: 'border-pink-600',
      accent: 'from-pink-500 to-rose-500',
      avatarGradient: 'from-pink-500 to-rose-600',
    },
    purple: {
      backgroundGradient: 'from-purple-400 via-indigo-400 to-pink-400',
      containerGradient: 'from-purple-50 via-indigo-50 to-pink-50',
      primary: 'bg-purple-600 hover:bg-purple-700',
      primaryLight: 'bg-purple-100 hover:bg-purple-200',
      primaryText: 'text-purple-600',
      borderColor: 'border-purple-600',
      accent: 'from-purple-500 to-indigo-500',
      avatarGradient: 'from-purple-500 to-indigo-600',
    },
    blue: {
      backgroundGradient: 'from-blue-400 via-cyan-400 to-teal-400',
      containerGradient: 'from-blue-50 via-cyan-50 to-teal-50',
      primary: 'bg-blue-600 hover:bg-blue-700',
      primaryLight: 'bg-blue-100 hover:bg-blue-200',
      primaryText: 'text-blue-600',
      borderColor: 'border-blue-600',
      accent: 'from-blue-500 to-cyan-500',
      avatarGradient: 'from-blue-500 to-cyan-600',
    },
    green: {
      backgroundGradient: 'from-green-400 via-emerald-400 to-teal-400',
      containerGradient: 'from-green-50 via-emerald-50 to-teal-50',
      primary: 'bg-green-600 hover:bg-green-700',
      primaryLight: 'bg-green-100 hover:bg-green-200',
      primaryText: 'text-green-600',
      borderColor: 'border-green-600',
      accent: 'from-green-500 to-emerald-500',
      avatarGradient: 'from-green-500 to-emerald-600',
    },
  };

  const currentColorScheme = colorSchemes[profileSettings.colorScheme] || colorSchemes.blueOrange;

  // Get storage key for this conversation
  const getStorageKey = () => {
    if (!profile) return null;
    return `live_chat_${profile.language}_${profile.accent}`;
  };

  // Load saved conversation
  const loadSavedConversation = () => {
    const storageKey = getStorageKey();
    if (!storageKey) return null;
    
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const data = JSON.parse(saved);
        return {
          messages: data.messages || [],
          conversationHistory: data.conversationHistory || [],
        };
      }
    } catch (error) {
      console.error('Error loading saved conversation:', error);
    }
    return null;
  };

  // Stop all currently playing audio
  const stopAllAudio = () => {
    // Stop main audio ref
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
        if (currentAudioRef.current.src) {
          URL.revokeObjectURL(currentAudioRef.current.src);
        }
        currentAudioRef.current.src = '';
        currentAudioRef.current = null;
      } catch (e) {
        console.error('Error stopping currentAudioRef:', e);
      }
    }
    
    // Stop all audio instances
    allAudioRefs.current.forEach(audio => {
      try {
        audio.pause();
        audio.currentTime = 0;
        if (audio.src && audio.src.startsWith('blob:')) {
          URL.revokeObjectURL(audio.src);
        }
        audio.src = '';
      } catch (e) {
        console.error('Error stopping audio instance:', e);
      }
    });
    allAudioRefs.current = [];
    
    setIsAISpeaking(false);
    setCurrentAudioBlob(null);
    setPendingAudio(null);
    pendingAudioRef.current = null;
    isPlayingRef.current = false;
  };

  // Replay audio for a specific message
  const replayMessageAudio = async (messageId) => {
    // Guard: prevent multiple simultaneous replays of the same message
    if (replayingMessageIdRef.current === messageId) {
      console.log('Already replaying this message, skipping duplicate request');
      return;
    }
    
    // Guard: prevent replay if audio is already playing
    if (isPlayingRef.current) {
      console.log('Audio already playing, skipping replay request');
      return;
    }
    
    // Mark this message as being replayed
    replayingMessageIdRef.current = messageId;
    
    try {
      // Stop any currently playing audio first
      stopAllAudio();
      
      let audioBlob = messageAudioMap.get(messageId);
      
      // If audio not in map, regenerate it from the message text
      if (!audioBlob) {
        const message = messages.find(m => m.id === messageId);
        if (message && message.type === 'ai') {
          try {
            const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
            audioBlob = await ttsService.generateSpeech(message.text, null, accentName, true); // robotic=true for Wally
            
            // Store it for future replays
            if (audioBlob) {
              const newMap = new Map(messageAudioMap);
              newMap.set(messageId, audioBlob);
              setMessageAudioMap(newMap);
            }
          } catch (error) {
            console.error('Error generating replay audio:', error);
            replayingMessageIdRef.current = null; // Clear on error
            return;
          }
        }
      }
      
      if (audioBlob) {
        await playAIResponseAudio(audioBlob);
      }
    } catch (error) {
      console.error('Error replaying message audio:', error);
      replayingMessageIdRef.current = null; // Clear on error
    } finally {
      // Clear the replaying flag after a short delay to allow audio to start
      setTimeout(() => {
        replayingMessageIdRef.current = null;
      }, 100);
    }
  };

  // Save conversation to localStorage
  const saveConversation = (messagesToSave = messages) => {
    const storageKey = getStorageKey();
    if (!storageKey) return;
    
    try {
      // Convert Map to plain object for storage (we can't store audio blobs, but we can store message IDs)
      const audioMapObj = {};
      messageAudioMap.forEach((value, key) => {
        // Note: We can't store Blobs in localStorage, so we'll just store the message IDs
        // The audio will need to be regenerated if needed
        audioMapObj[key] = true; // Just mark that audio exists for this message
      });
      
      const data = {
        messages: messagesToSave,
        conversationHistory: conversationHistory.current,
        messageAudioMap: audioMapObj, // Store which messages have audio
        lastUpdated: new Date().toISOString(),
      };
      localStorage.setItem(storageKey, JSON.stringify(data));
    } catch (error) {
      console.error('Error saving conversation:', error);
    }
  };

  // Initialize audio capture function (defined outside useEffect so it can be called from retry button)
  const initAudio = async () => {
    // Prevent multiple initializations
    if (initAudioRef.current) {
      console.log('Audio capture already initialized, skipping...');
      return;
    }
    
    try {
      console.log('Initializing audio capture...');
      initAudioRef.current = true; // Mark as initializing
      
      // Check if getUserMedia is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia is not supported in this browser');
      }
      
      const capture = new AudioCapture();
      await capture.initialize();
      console.log('Audio capture initialized successfully');
      setAudioCapture(capture);
      setMicError(null); // Clear any previous errors
    } catch (error) {
      console.error('Error initializing audio capture:', error);
      initAudioRef.current = false; // Reset on error so user can retry
      let errorMessage = 'Microphone access required. ';
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage += 'Please allow microphone access in your browser settings.';
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        errorMessage += 'No microphone found. Please connect a microphone.';
      } else if (error.name === 'NotSupportedError' || error.name === 'ConstraintNotSatisfiedError') {
        errorMessage += 'Your browser does not support the required audio settings.';
      } else {
        errorMessage += `Error: ${error.message || 'Unknown error'}`;
      }
      
      setMicError(errorMessage);
    }
  };

  // Save conversation whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      saveConversation(messages);
    }
  }, [messages]);

  // Set mounted flag on mount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!profile) {
      navigate('/dashboard');
      return;
    }

    // Try to load saved conversation
    const saved = loadSavedConversation();
    if (saved && saved.messages.length > 0) {
      // Restore saved conversation - don't generate a new intro message
      setMessages(saved.messages);
      conversationHistory.current = saved.conversationHistory;
      setIsRestored(true);
      
      // Clear the restored flag after a few seconds
      setTimeout(() => setIsRestored(false), 3000);
      
      // Show the last AI message (could be intro or a regular message)
      const lastAIMessage = saved.messages.filter(m => m.type === 'ai').pop();
      if (lastAIMessage) {
        setCurrentAIMessage(lastAIMessage.text);
        
        // Regenerate audio for the last message (but don't auto-play - user can click replay)
        const regenerateMessageAudio = async () => {
          try {
            // Use TTS service to regenerate audio for the exact message text
            const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
            const audioBlob = await ttsService.generateSpeech(lastAIMessage.text, null, accentName, true); // robotic=true for Wally
            
            if (audioBlob) {
              const newMap = new Map(messageAudioMap);
              newMap.set(lastAIMessage.id, audioBlob);
              setMessageAudioMap(newMap);
              // Don't auto-play restored conversations - user can click replay if they want
            }
          } catch (error) {
            console.error('Error regenerating message audio:', error);
          }
        };
        regenerateMessageAudio();
      }
    } else {
      // Start new conversation - simple greeting that plays automatically
      const greetingText = "Is there anything you want to talk about right now?";
      const initialMessageId = Date.now();
      const initialMessage = {
        id: initialMessageId,
        type: 'ai',
        text: greetingText,
        timestamp: new Date(),
      };
      setMessages([initialMessage]);
      conversationHistory.current = [
        { role: 'assistant', content: greetingText }
      ];
      setCurrentAIMessage(greetingText);
      
      // Generate and play TTS immediately (same as practice mode) - but only once
      const playGreeting = async () => {
        // Guard: only play if we haven't played the initial greeting yet
        if (hasPlayedInitialGreeting.current) {
          console.log('Initial greeting already played, skipping...');
          return;
        }
        
        try {
          // Mark as played BEFORE async operations to prevent race conditions
          hasPlayedInitialGreeting.current = true;
          
          // Stop any existing audio first
          stopAllAudio();
          
          const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
          const audioBlob = await ttsService.generateSpeech(greetingText, null, accentName, true); // robotic=true for Wally
          
          if (audioBlob) {
            // Store audio for replay
            const newMap = new Map(messageAudioMap);
            newMap.set(initialMessageId, audioBlob);
            setMessageAudioMap(newMap);
            
            // Use centralized audio playback
            await playAIResponseAudio(audioBlob);
          }
        } catch (error) {
          console.error('Error generating/playing greeting TTS:', error);
          // Reset flag on error so user can try again
          hasPlayedInitialGreeting.current = false;
        }
      };
      
      playGreeting();
    }

    // Initialize audio capture on mount
    initAudio();

    return () => {
      // Save conversation before unmounting
      saveConversation();
      
      // Cleanup on unmount (isMountedRef is already handled by the dedicated useEffect)
      if (audioCapture) {
        audioCapture.cleanup();
      }
      // Stop any playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, [profile, navigate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleRecording = () => {
    if (isRecording) {
      stopListening();
    } else {
      startListening();
    }
  };

  const startListening = () => {
    if (!audioCapture) {
      console.error('Audio capture not initialized');
      alert('Microphone not initialized. Please refresh the page and try again.');
      return;
    }
    
    if (isRecording) {
      console.warn('Already recording, ignoring duplicate start request');
      return;
    }
    
    try {
      // Start recording with volume callback
      audioCapture.startRecording((volume) => {
        setRecordingVolume(volume);
      });
      setIsRecording(true);
      setIsListening(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
      
      let errorMessage = 'Error starting recording. ';
      if (error.message && error.message.includes('not initialized')) {
        errorMessage = 'Microphone not initialized. Please refresh the page and try again.';
      } else if (error.message) {
        errorMessage += error.message;
      } else {
        errorMessage += 'Please try again.';
      }
      
      alert(errorMessage);
      setIsRecording(false);
      setIsListening(false);
    }
  };

  const stopListening = async () => {
    if (!audioCapture || !isRecording) return;
    
    setIsRecording(false);
    setIsListening(false);
    setIsProcessing(true);
    setRecordingVolume(0); // Reset volume

    try {
      const audioBlob = await audioCapture.stopRecording();
      
      // Use new endpoint: Whisper transcription -> Gemini feedback & response
      const user = JSON.parse(localStorage.getItem('user'));
      
      // Prepare conversation history for API
      const historyForAPI = conversationHistory.current.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Add timeout to prevent hanging - 60 seconds max
      const requestStartTime = Date.now();
      console.log('🔄 [FRONTEND] Starting chat request...', {
        audioBlobSize: audioBlob.size,
        historyLength: historyForAPI.length,
        timestamp: new Date().toISOString()
      });
      
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
          const elapsed = (Date.now() - requestStartTime) / 1000;
          console.error(`❌ [FRONTEND] Request timeout after ${elapsed.toFixed(2)}s`);
          reject(new Error('Request timeout: The server took too long to respond. Please try again.'));
        }, 60000); // 60 second timeout
      });
      
      // Call the new endpoint that handles Whisper + Gemini with timeout
      const chatResponse = await Promise.race([
        (async () => {
          try {
            console.log('🔄 [FRONTEND] Calling sendMessageWithAudioUpload...');
            const response = await chatService.sendMessageWithAudioUpload(
              audioBlob,
              {
                user_id: user.user_id,
                language: profile.language,
                target_accent: profile.accent,
              },
              historyForAPI
            );
            const elapsed = (Date.now() - requestStartTime) / 1000;
            console.log(`✅ [FRONTEND] Request completed in ${elapsed.toFixed(2)}s`, {
              hasAudio: !!response.audio,
              audioSize: response.audio?.size || 0,
              messageLength: response.message?.length || 0
            });
            return response;
          } catch (error) {
            const elapsed = (Date.now() - requestStartTime) / 1000;
            console.error(`❌ [FRONTEND] Request failed after ${elapsed.toFixed(2)}s:`, error);
            throw error;
          }
        })(),
        timeoutPromise
      ]);
      
      // Get transcribed text
      const userText = chatResponse.transcribed_text || 'I said something...';
      
      // Add user message
      const userMessage = {
        id: Date.now(),
        type: 'user',
        text: userText,
        timestamp: new Date(),
        pronunciationScore: chatResponse.pronunciation_score || null,
      };
      setMessages(prev => [...prev, userMessage]);
      conversationHistory.current.push({ role: 'user', content: userText });

      // Add AI message and play audio
      const aiMessageId = Date.now() + 1;
      const aiMessage = {
        id: aiMessageId,
        type: 'ai',
        text: chatResponse.message,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
      conversationHistory.current.push({ role: 'assistant', content: chatResponse.message });
      setCurrentAIMessage(chatResponse.message);

      // Store audio for replay and play it
      let audioToPlay = chatResponse.audio;
      
      if (audioToPlay && audioToPlay.size > 0) {
        console.log('Playing AI response audio...', {
          blobSize: audioToPlay.size,
          blobType: audioToPlay.type
        });
        // Store audio for replay
        const newMap = new Map(messageAudioMap);
        newMap.set(aiMessageId, audioToPlay);
        setMessageAudioMap(newMap);
        
        // Stop any currently playing audio first and wait for cleanup
        stopAllAudio();
        await new Promise(resolve => setTimeout(resolve, 100)); // Ensure cleanup completes
        await playAIResponseAudio(audioToPlay);
      } else {
        console.warn('No valid audio received from backend, generating TTS fallback...');
        // Fallback: generate TTS
        try {
          const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
          audioToPlay = await ttsService.generateSpeech(chatResponse.message, null, accentName, true);
          if (audioToPlay && audioToPlay.size > 0) {
            const newMap = new Map(messageAudioMap);
            newMap.set(aiMessageId, audioToPlay);
            setMessageAudioMap(newMap);
            stopAllAudio();
            await playAIResponseAudio(audioToPlay);
          }
        } catch (ttsError) {
          console.error('Error generating TTS fallback:', ttsError);
        }
      }

    } catch (error) {
      console.error('Error processing audio:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        stack: error.stack
      });
      
      let errorMessage = 'Error processing your message. ';
      if (error.message && error.message.includes('timeout')) {
        // Timeout error
        errorMessage = 'Request timeout: The server took too long to respond. Please check your connection and try again.';
      } else if (error.response) {
        // Backend returned an error
        errorMessage += `Server error: ${error.response.status} - ${error.response.data?.detail || error.response.data?.message || 'Unknown error'}`;
      } else if (error.message) {
        // Network or other error
        errorMessage += error.message;
      } else {
        errorMessage += 'Please try again.';
      }
      
      alert(errorMessage);
    } finally {
      // Always clear processing state, even if there was an error or timeout
      setIsProcessing(false);
    }
  };

  const generateAIResponse = async (userText, analysisResult) => {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      
      // Prepare conversation history for API
      const historyForAPI = conversationHistory.current.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Call backend API to generate AI response with audio
      const chatResponse = await chatService.sendMessageWithAudio({
        user_id: user.user_id,
        session_id: `chat_${Date.now()}`,
        language: profile.language,
        target_accent: profile.accent,
        user_message: userText,
        pronunciation_score: analysisResult.accent_score,
        struggle_areas: analysisResult.struggle_areas || [],
        conversation_history: historyForAPI,
      });
      
      const aiMessageId = Date.now() + 1;
      const aiMessage = {
        id: aiMessageId,
        type: 'ai',
        text: chatResponse.message,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, aiMessage]);
      conversationHistory.current.push({ role: 'assistant', content: chatResponse.message });
      setCurrentAIMessage(chatResponse.message);

      // Store audio for replay and play it
      let audioToPlay = chatResponse.audio;
      
      // Validate audio blob if received
      if (audioToPlay && audioToPlay.size === 0) {
        console.warn('Received audio blob is empty, will generate TTS instead');
        audioToPlay = null;
      }
      
      // If no audio was provided or invalid, generate TTS for the message
      if (!audioToPlay) {
        console.log('No audio received, generating TTS for message...');
        try {
          // Use robotic voice for Wally
          const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
          audioToPlay = await ttsService.generateSpeech(chatResponse.message, null, accentName, true); // robotic=true
          if (audioToPlay && audioToPlay.size > 0) {
            console.log('TTS generated successfully', { blobSize: audioToPlay.size, blobType: audioToPlay.type });
            const newMap = new Map(messageAudioMap);
            newMap.set(aiMessageId, audioToPlay);
            setMessageAudioMap(newMap);
          } else {
            console.error('Generated TTS blob is invalid or empty');
            audioToPlay = null;
          }
        } catch (ttsError) {
          console.error('Error generating TTS for AI message:', ttsError);
          audioToPlay = null;
        }
      } else {
        // Store the audio we received
        console.log('Using audio from backend', { blobSize: audioToPlay.size, blobType: audioToPlay.type });
        const newMap = new Map(messageAudioMap);
        newMap.set(aiMessageId, audioToPlay);
        setMessageAudioMap(newMap);
      }

      // Play AI response audio using centralized function
      if (audioToPlay && audioToPlay.size > 0) {
        console.log('Playing AI response audio...', {
          blobSize: audioToPlay.size,
          blobType: audioToPlay.type
        });
        // Stop any currently playing audio first and wait for cleanup
        stopAllAudio();
        await new Promise(resolve => setTimeout(resolve, 100)); // Ensure cleanup completes
        await playAIResponseAudio(audioToPlay);
      } else {
        console.error('No valid audio to play for AI message');
      }

    } catch (error) {
      console.error('Error generating AI response:', error);
      // Fallback message
      const fallbackMessageId = Date.now() + 1;
      const fallbackMessage = {
        id: fallbackMessageId,
        type: 'ai',
        text: "That's really interesting! Tell me more about that. I'd love to hear more details! - Wally",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, fallbackMessage]);
      conversationHistory.current.push({ role: 'assistant', content: fallbackMessage.text });
      setCurrentAIMessage(fallbackMessage.text);
      
      // Generate and play TTS for fallback message - with robotic voice
      try {
        // Stop any currently playing audio first
        stopAllAudio();
        
        const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
        const audioBlob = await ttsService.generateSpeech(fallbackMessage.text, null, accentName, true); // robotic=true
        if (audioBlob) {
          const newMap = new Map(messageAudioMap);
          newMap.set(fallbackMessageId, audioBlob);
          setMessageAudioMap(newMap);
          
          // Use centralized audio playback
          await playAIResponseAudio(audioBlob);
        }
      } catch (ttsError) {
        console.error('Error generating TTS for fallback message:', ttsError);
      }
    }
  };

  const playAIResponseAudio = async (audioBlob) => {
    if (!isMountedRef.current) {
      console.warn('Component not mounted, skipping audio playback');
      return;
    }
    
    if (!audioBlob) {
      console.error('No audio blob provided to playAIResponseAudio');
      return;
    }
    
    if (audioBlob.size === 0) {
      console.error('Audio blob is empty (size: 0)');
      return;
    }
    
    // Guard against multiple simultaneous playbacks
    if (isPlayingRef.current) {
      console.warn('Audio already playing, skipping new playback request');
      return;
    }
    
    isPlayingRef.current = true;
    stopAllAudio();
    
    try {
      setCurrentAudioBlob(audioBlob);
      setIsAISpeaking(true);
      
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.volume = 1.0;
      
      audio.onloadeddata = () => {
        console.log('Audio data loaded, ready to play');
      };
      
      audio.oncanplay = () => {
        console.log('Audio can play');
      };
      
      audio.onended = () => {
        console.log('Audio playback ended');
        URL.revokeObjectURL(audioUrl);
        setIsAISpeaking(false);
        setCurrentAudioBlob(null);
        setPendingAudio(null);
        pendingAudioRef.current = null;
        isPlayingRef.current = false;
        replayingMessageIdRef.current = null;
        allAudioRefs.current = allAudioRefs.current.filter(a => a !== audio);
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      };
      
      audio.onerror = (error) => {
        console.error('Audio element error:', error, audio.error);
        URL.revokeObjectURL(audioUrl);
        setIsAISpeaking(false);
        setCurrentAudioBlob(null);
        isPlayingRef.current = false;
        replayingMessageIdRef.current = null;
        allAudioRefs.current = allAudioRefs.current.filter(a => a !== audio);
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      };
      
      audio.onpause = () => {
        if (!isMountedRef.current && currentAudioRef.current === audio) {
          URL.revokeObjectURL(audioUrl);
          setIsAISpeaking(false);
          setCurrentAudioBlob(null);
          currentAudioRef.current = null;
        }
      };
      
      if (allAudioRefs.current.includes(audio)) {
        console.warn('Audio instance already in tracking array - this should not happen');
      } else {
        allAudioRefs.current.push(audio);
      }
      
      currentAudioRef.current = audio;
      
      console.log('Audio element created, preparing to play...', {
        readyState: audio.readyState,
        networkState: audio.networkState
      });
      
      // Check again before playing (component might have unmounted)
      if (!isMountedRef.current) {
        URL.revokeObjectURL(audioUrl);
        return;
      }
      
      // Wait for audio to be ready (but don't block if it's already ready)
      if (audio.readyState < 2) {
        try {
          await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
              reject(new Error('Audio load timeout'));
            }, 5000);
            
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
            
            audio.addEventListener('canplay', onCanPlay);
            audio.addEventListener('error', onError);
            
            // Load the audio
            audio.load();
          });
          console.log('Audio is ready to play');
        } catch (loadError) {
          console.warn('Audio load timeout or error, attempting to play anyway:', loadError);
          // Continue anyway - sometimes audio can play even if readyState isn't 2
        }
      } else {
        console.log('Audio already ready, readyState:', audio.readyState);
      }
      
      // Handle autoplay restrictions - try to play, and if blocked, try again after user interaction
      try {
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          await playPromise;
        }
        console.log('✅ Audio playback started successfully');
        // Audio played successfully, clear any pending audio
        setPendingAudio(null);
        pendingAudioRef.current = null;
      } catch (playError) {
        console.warn('⚠️ Initial play attempt failed:', playError.name, playError.message);
        console.warn('Audio element state:', {
          readyState: audio.readyState,
          networkState: audio.networkState,
          src: audio.src.substring(0, 50) + '...',
          error: audio.error
        });
        // Clear playing flag on play error (unless it's autoplay restriction)
        if (playError.name !== 'NotAllowedError' && playError.name !== 'NotSupportedError') {
          isPlayingRef.current = false;
        }
        
        // If autoplay is blocked, set up interaction handler
        if (playError.name === 'NotAllowedError' || playError.name === 'NotSupportedError') {
          console.warn('Autoplay blocked by browser. Will attempt to play after user interaction.');
          
          // Create a more robust interaction handler
          const playOnInteraction = async (event) => {
            try {
              // Try to play again
              const playPromise = audio.play();
              if (playPromise !== undefined) {
                await playPromise;
              }
              console.log('Audio playback started after user interaction');
              
              // Clear pending audio on successful play
              setPendingAudio(null);
              pendingAudioRef.current = null;
              
              // Clean up listeners
              document.removeEventListener('click', playOnInteraction);
              document.removeEventListener('touchstart', playOnInteraction);
              document.removeEventListener('keydown', playOnInteraction);
            } catch (e) {
              console.error('Still unable to play audio after interaction:', e);
              setIsAISpeaking(false);
              setCurrentAudioBlob(null);
            }
          };
          
          // Add multiple event listeners for better compatibility
          // Also add to the main container for better UX
          const mainContainer = document.querySelector('.min-h-screen');
          if (mainContainer) {
            mainContainer.addEventListener('click', playOnInteraction, { once: true, capture: true });
            mainContainer.addEventListener('touchstart', playOnInteraction, { once: true, capture: true });
          }
          document.addEventListener('click', playOnInteraction, { once: true });
          document.addEventListener('touchstart', playOnInteraction, { once: true });
          document.addEventListener('keydown', playOnInteraction, { once: true });
          
          // Store pending audio for manual play button
          pendingAudioRef.current = audio;
          setPendingAudio(audio);
          
          // Don't set isAISpeaking to false - keep the UI state so user knows audio is available
          // Also keep currentAudioBlob set so avatar can react
        } else {
          throw playError;
        }
      }
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsAISpeaking(false);
      setCurrentAudioBlob(null);
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.src = '';
        currentAudioRef.current = null;
      }
      // Try to get more details about the error
      if (error.name === 'NotAllowedError') {
        console.error('Audio playback blocked by browser. User interaction may be required.');
      } else if (error.name === 'NotSupportedError') {
        console.error('Audio format not supported');
      } else {
        console.error('Unknown audio playback error:', error);
      }
    }
  };

  const handleClearConversation = () => {
    if (window.confirm('Are you sure you want to clear this conversation? This cannot be undone.')) {
      const storageKey = getStorageKey();
      if (storageKey) {
        localStorage.removeItem(storageKey);
      }
      setMessages([]);
      conversationHistory.current = [];
      setIsRestored(false);
      hasPlayedInitialGreeting.current = false; // Reset so we can play the new intro
      
      // Generate exactly ONE new intro greeting
      const generateInitialGreeting = async () => {
        try {
          const user = JSON.parse(localStorage.getItem('user'));
          const chatResponse = await chatService.sendMessageWithAudio({
            user_id: user.user_id,
            session_id: `chat_init_${Date.now()}`,
            language: profile.language,
            target_accent: profile.accent,
            user_message: "",
            conversation_history: [],
          });
          
          const initialMessageId = Date.now();
          const initialMessage = {
            id: initialMessageId,
            type: 'ai',
            text: chatResponse.message || `Hey! I'm Wally. What's up? What are you into these days?`,
            timestamp: new Date(),
          };
          setMessages([initialMessage]); // Only one message
          conversationHistory.current = [
            { role: 'assistant', content: initialMessage.text }
          ];
          setCurrentAIMessage(initialMessage.text);
          
          // Store and play audio
          let audioToPlay = chatResponse.audio;
          if (!audioToPlay) {
            // Generate TTS if no audio provided
            try {
              const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
              audioToPlay = await ttsService.generateSpeech(initialMessage.text, null, accentName, true); // robotic=true for Wally
            } catch (ttsError) {
              console.error('Error generating TTS for cleared conversation greeting:', ttsError);
            }
          }
          
          if (audioToPlay) {
            const newMap = new Map(messageAudioMap);
            newMap.set(initialMessageId, audioToPlay);
            setMessageAudioMap(newMap);
            if (isMountedRef.current && !hasPlayedInitialGreeting.current) {
              hasPlayedInitialGreeting.current = true;
              await playAIResponseAudio(audioToPlay);
            }
          }
        } catch (error) {
          console.error('Error generating initial greeting:', error);
        }
      };
      
      generateInitialGreeting();
    }
  };

  const handleBack = () => {
    // Save conversation before leaving
    saveConversation(messages);
    
    // Stop any playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    
    // Cleanup (isMountedRef is handled by useEffect cleanup)
    if (audioCapture) {
      audioCapture.cleanup();
    }
    navigate('/dashboard');
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.backgroundGradient}`}>
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 text-gray-700 hover:text-accenta-primary transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back to Dashboard</span>
            </button>
            <h1 className="text-xl font-bold text-gray-900">Chat with Wally - {profile?.accent} Accent</h1>
            <div className="w-32"></div> {/* Spacer */}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Restored Conversation Notice */}
        {isRestored && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-blue-800">Conversation restored - continuing where you left off</span>
            </div>
            <button
              onClick={handleClearConversation}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Start new
            </button>
          </div>
        )}
        
        {/* Main Container with Audio-Reactive Avatar */}
        <div className={`bg-gradient-to-br ${currentColorScheme.containerGradient} rounded-2xl shadow-xl min-h-[calc(100vh-250px)] flex flex-col items-center justify-center p-8`}>
          {/* Audio-Reactive Avatar - Clickable to start/stop recording */}
          <div className="mb-8">
            <div 
              onClick={toggleRecording}
              className="cursor-pointer transition-transform hover:scale-105 active:scale-95"
            >
              <AudioReactiveAvatar
                audioBlob={currentAudioBlob}
                isSpeaking={isAISpeaking || isRecording}
                volumeLevel={isRecording ? recordingVolume : 0}
                onAnimationComplete={() => {
                  setIsAISpeaking(false);
                  setCurrentAudioBlob(null);
                }}
              />
            </div>
            {isRecording && (
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-red-500/20 rounded-full">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-red-700 font-medium">Recording... Click Wally again to stop</span>
                </div>
              </div>
            )}
          </div>

          {/* Current AI Message Display */}
          {currentAIMessage && (
            <div className="max-w-2xl mb-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
                <div className="flex items-center gap-2 mb-3 justify-center">
                  <div className={`w-8 h-8 bg-gradient-to-br ${currentColorScheme.avatarGradient} rounded-full flex items-center justify-center`}>
                    <span className="text-white font-bold text-sm">W</span>
                  </div>
                  <span className="text-sm font-semibold text-gray-600">Wally</span>
                </div>
                <div className="flex items-center justify-center gap-3">
                  <p className="text-lg text-gray-800 text-center leading-relaxed flex-1">
                    {currentAIMessage}
                  </p>
                  {(() => {
                    const currentMessage = messages.filter(m => m.type === 'ai' && m.text === currentAIMessage).pop();
                    const hasAudio = currentMessage && messageAudioMap.has(currentMessage.id);
                    return hasAudio ? (
                      <button
                        onClick={() => replayMessageAudio(currentMessage.id)}
                        className={`flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full ${currentColorScheme.primaryLight} ${currentColorScheme.primaryText} transition-colors`}
                        title="Replay audio"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 14V6a1 1 0 00-1.555-.832L10 8.798V6a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z" />
                        </svg>
                      </button>
                    ) : null;
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* Play Audio Button (shown when autoplay is blocked) */}
          {pendingAudio && (
            <div className="mb-4">
              <button
                onClick={async () => {
                  try {
                    if (pendingAudioRef.current) {
                      const playPromise = pendingAudioRef.current.play();
                      if (playPromise !== undefined) {
                        await playPromise;
                      }
                      setPendingAudio(null);
                      pendingAudioRef.current = null;
                    }
                  } catch (error) {
                    console.error('Error playing pending audio:', error);
                  }
                }}
                className={`px-6 py-3 ${currentColorScheme.primary} text-white rounded-lg font-semibold transition-colors flex items-center gap-2`}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
                <span>Play Wally's Message</span>
              </button>
            </div>
          )}

            {/* Conversation History (Minimal) - Exclude current message */}
          {messages.length > 1 && (() => {
            // Filter out the current message from history
            const historyMessages = messages.filter(m => 
              m.type !== 'ai' || m.text !== currentAIMessage
            );
            
            return historyMessages.length > 0 ? (
              <div className="w-full max-w-2xl mb-6">
                <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 max-h-48 overflow-y-auto">
                  <div className="space-y-2">
                    {historyMessages.slice(-3).map((message) => (
                      <div
                        key={message.id}
                        className={`text-sm flex items-start gap-2 ${
                          message.type === 'user' ? `text-right ${currentColorScheme.primaryText} justify-end` : 'text-left text-gray-600'
                        }`}
                      >
                        <div className="flex-1">
                          {message.type === 'user' && (
                            <span className="font-medium">You: </span>
                          )}
                          {message.type === 'ai' && (
                            <span className="font-medium">Wally: </span>
                          )}
                          <span className="opacity-80">{message.text.substring(0, 100)}{message.text.length > 100 ? '...' : ''}</span>
                        </div>
                        {message.type === 'ai' && messageAudioMap.has(message.id) && (
                          <button
                            onClick={() => replayMessageAudio(message.id)}
                            className={`flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full ${currentColorScheme.primaryLight} ${currentColorScheme.primaryText} transition-colors`}
                            title="Replay audio"
                          >
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 14V6a1 1 0 00-1.555-.832L10 8.798V6a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z" />
                            </svg>
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null;
          })()}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="mb-6">
              <div className="bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 flex items-center gap-3">
                <div className={`animate-spin rounded-full h-5 w-5 border-b-2 ${currentColorScheme.borderColor}`}></div>
                <span className="text-sm text-gray-700 font-medium">Processing your message...</span>
              </div>
            </div>
          )}

          {/* Microphone Error Message */}
          {micError && (
            <div className="w-full max-w-md mt-4 mb-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-sm text-red-800 font-medium mb-2">{micError}</p>
                    <button
                      onClick={() => {
                        setMicError(null);
                        initAudioRef.current = false; // Reset flag to allow retry
                        initAudio();
                      }}
                      className="text-sm text-red-600 hover:text-red-800 underline"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="w-full max-w-md mt-8">
            <p className="text-sm text-gray-600 text-center">
              {micError
                ? '⚠️ Microphone access is required to chat with Wally'
                : isRecording
                ? '🎤 Speak naturally - Wally is listening! Click Wally again when done.'
                : isAISpeaking
                ? '👂 Listen to Wally\'s response...'
                : isProcessing
                ? '⏳ Processing your message...'
                : !audioCapture
                ? '🎤 Initializing microphone...'
                : '💬 Click Wally\'s face to start talking'}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LiveChat;

