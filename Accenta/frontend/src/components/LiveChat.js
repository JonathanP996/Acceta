import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AudioCapture from '../utils/audioCapture';
import { analysisService, chatService, ttsService } from '../services/api';
import AudioReactiveAvatar from './AudioReactiveAvatar';

const LiveChat = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile } = location.state || {};
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioCapture, setAudioCapture] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isRestored, setIsRestored] = useState(false); // Track if conversation was restored
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [currentAudioBlob, setCurrentAudioBlob] = useState(null);
  const [currentAIMessage, setCurrentAIMessage] = useState('');
  const [messageAudioMap, setMessageAudioMap] = useState(new Map()); // Store audio for each message
  const [pendingAudio, setPendingAudio] = useState(null); // Audio waiting for user interaction
  const messagesEndRef = useRef(null);
  const conversationHistory = useRef([]);
  const currentAudioRef = useRef(null); // Track current audio playback
  const isMountedRef = useRef(true); // Track if component is mounted
  const hasPlayedInitialGreeting = useRef(false); // Track if initial greeting was played
  const pendingAudioRef = useRef(null); // Ref to track pending audio element

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

  // Replay audio for a specific message
  const replayMessageAudio = async (messageId) => {
    let audioBlob = messageAudioMap.get(messageId);
    
    // If audio not in map, regenerate it from the message text
    if (!audioBlob) {
      const message = messages.find(m => m.id === messageId);
      if (message && message.type === 'ai') {
        try {
          const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
          audioBlob = await ttsService.generateSpeech(message.text, null, accentName);
          
          // Store it for future replays
          if (audioBlob) {
            const newMap = new Map(messageAudioMap);
            newMap.set(messageId, audioBlob);
            setMessageAudioMap(newMap);
          }
        } catch (error) {
          console.error('Error generating replay audio:', error);
          return;
        }
      }
    }
    
    if (audioBlob) {
      await playAIResponseAudio(audioBlob);
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

  // Save conversation whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      saveConversation(messages);
    }
  }, [messages]);

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
        
        // Regenerate and play audio for the last AI message when page loads
        if (!hasPlayedInitialGreeting.current) {
          hasPlayedInitialGreeting.current = true;
          // Regenerate audio for the last message using TTS directly
          const regenerateMessageAudio = async () => {
            try {
              // Use TTS service to regenerate audio for the exact message text
              const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
              const audioBlob = await ttsService.generateSpeech(lastAIMessage.text, null, accentName);
              
              if (audioBlob) {
                const newMap = new Map(messageAudioMap);
                newMap.set(lastAIMessage.id, audioBlob);
                setMessageAudioMap(newMap);
                if (isMountedRef.current) {
                  await playAIResponseAudio(audioBlob);
                }
              }
            } catch (error) {
              console.error('Error regenerating message audio:', error);
            }
          };
          regenerateMessageAudio();
        }
      }
    } else {
      // Start new conversation - generate exactly ONE intro message
      // Start new conversation with AI greeting (generated dynamically)
      const generateInitialGreeting = async () => {
        try {
          const user = JSON.parse(localStorage.getItem('user'));
          const chatResponse = await chatService.sendMessageWithAudio({
            user_id: user.user_id,
            session_id: `chat_init_${Date.now()}`,
            language: profile.language,
            target_accent: profile.accent,
            user_message: "", // Empty for initial greeting
            conversation_history: [],
          });
          
          const initialMessageId = Date.now();
          const initialMessage = {
            id: initialMessageId,
            type: 'ai',
            text: chatResponse.message || `Hi! I'm Wally. I'm here to help you practice your ${profile.accent} accent. What are you passionate about?`,
            timestamp: new Date(),
          };
          setMessages([initialMessage]);
          conversationHistory.current = [
            { role: 'assistant', content: initialMessage.text }
          ];
          setCurrentAIMessage(initialMessage.text);
          
          // Store audio for replay
          if (chatResponse.audio) {
            const newMap = new Map(messageAudioMap);
            newMap.set(initialMessageId, chatResponse.audio);
            setMessageAudioMap(newMap);
          }
          
          // Always ensure we have audio and play it
          let audioToPlay = chatResponse.audio;
          
          // If no audio was provided, generate TTS
          if (!audioToPlay) {
            console.warn('No audio received for initial greeting, generating TTS...');
            try {
              const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
              audioToPlay = await ttsService.generateSpeech(initialMessage.text, null, accentName);
              if (audioToPlay) {
                const newMap = new Map(messageAudioMap);
                newMap.set(initialMessageId, audioToPlay);
                setMessageAudioMap(newMap);
              }
            } catch (ttsError) {
              console.error('Error generating TTS for initial greeting:', ttsError);
            }
          }
          
          // Play greeting audio when page loads
          if (audioToPlay && isMountedRef.current && !hasPlayedInitialGreeting.current) {
            hasPlayedInitialGreeting.current = true;
            console.log('Playing initial greeting audio...', { blobSize: audioToPlay.size, blobType: audioToPlay.type });
            await playAIResponseAudio(audioToPlay);
          } else if (!audioToPlay) {
            console.error('Failed to get or generate audio for initial greeting');
          }
        } catch (error) {
          console.error('Error generating initial greeting:', error);
          // Fallback greeting
          const fallbackMessageId = Date.now();
          const initialMessage = {
            id: fallbackMessageId,
            type: 'ai',
            text: `Hi! I'm Wally. I'm here to help you practice your ${profile.accent} accent. What are you passionate about?`,
            timestamp: new Date(),
          };
          setMessages([initialMessage]);
          conversationHistory.current = [
            { role: 'assistant', content: initialMessage.text }
          ];
          setCurrentAIMessage(initialMessage.text);
          
          // Generate TTS for fallback greeting
          try {
            const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
            const audioBlob = await ttsService.generateSpeech(initialMessage.text, null, accentName);
            if (audioBlob) {
              const newMap = new Map(messageAudioMap);
              newMap.set(fallbackMessageId, audioBlob);
              setMessageAudioMap(newMap);
              if (isMountedRef.current && !hasPlayedInitialGreeting.current) {
                hasPlayedInitialGreeting.current = true;
                console.log('Playing fallback TTS audio...', audioBlob);
                await playAIResponseAudio(audioBlob);
              }
            }
          } catch (ttsError) {
            console.error('Error generating TTS for fallback greeting:', ttsError);
          }
        }
      };
      
      generateInitialGreeting();
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
      // Save conversation before unmounting
      saveConversation();
      
      // Cleanup on unmount
      isMountedRef.current = false;
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

  const startListening = () => {
    if (!audioCapture || isRecording) return;
    try {
      audioCapture.startRecording();
      setIsRecording(true);
      setIsListening(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Error starting recording. Please try again.');
    }
  };

  const stopListening = async () => {
    if (!audioCapture || !isRecording) return;
    
    setIsRecording(false);
    setIsListening(false);
    setIsProcessing(true);

    try {
      const audioBlob = await audioCapture.stopRecording();
      
      // Transcribe audio
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.wav');
      formData.append('user_id', JSON.parse(localStorage.getItem('user')).user_id);
      formData.append('session_id', `chat_${Date.now()}`);
      formData.append('language', profile.language);
      formData.append('target_accent', profile.accent);

      // Analyze pronunciation
      const analysisResult = await analysisService.analyzeAccent(formData);
      
      // Get transcription (check multiple possible field names)
      const userText = analysisResult.transcribed_text || 
                       analysisResult.transcription || 
                       analysisResult.text ||
                       'I said something...';
      
      // Add user message
      const userMessage = {
        id: Date.now(),
        type: 'user',
        text: userText,
        timestamp: new Date(),
        pronunciationScore: analysisResult.accent_score || analysisResult.score || null,
      };
      setMessages(prev => [...prev, userMessage]);
      conversationHistory.current.push({ role: 'user', content: userText });

      // Generate AI response with feedback using backend API
      await generateAIResponse(userText, {
        ...analysisResult,
        accent_score: analysisResult.accent_score || analysisResult.score || 70,
        struggle_areas: analysisResult.struggle_areas || analysisResult.struggleAreas || [],
      });

    } catch (error) {
      console.error('Error processing audio:', error);
      alert('Error processing your message. Please try again.');
    } finally {
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
          const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
          audioToPlay = await ttsService.generateSpeech(chatResponse.message, null, accentName);
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

      // Play AI response audio (will trigger reactive avatar)
      if (audioToPlay && audioToPlay.size > 0) {
        console.log('Attempting to play audio for AI message...');
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
      
      // Generate and play TTS for fallback message
      try {
        const accentName = profile.accent.toLowerCase().replace(' english', '').replace('english', '').trim();
        const audioBlob = await ttsService.generateSpeech(fallbackMessage.text, null, accentName);
        if (audioBlob) {
          const newMap = new Map(messageAudioMap);
          newMap.set(fallbackMessageId, audioBlob);
          setMessageAudioMap(newMap);
          await playAIResponseAudio(audioBlob);
        }
      } catch (ttsError) {
        console.error('Error generating TTS for fallback message:', ttsError);
      }
    }
  };

  const playAIResponseAudio = async (audioBlob) => {
    // Only play audio if component is still mounted
    if (!isMountedRef.current) {
      console.log('Component not mounted, skipping audio playback');
      return;
    }
    
    if (!audioBlob) {
      console.error('No audio blob provided to playAIResponseAudio');
      return;
    }
    
    // Validate blob
    if (audioBlob.size === 0) {
      console.error('Audio blob is empty (size: 0)');
      return;
    }
    
    try {
      console.log('Starting audio playback...', { 
        blobSize: audioBlob.size, 
        blobType: audioBlob.type,
        isValid: audioBlob instanceof Blob
      });
      
      // Stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.src = '';
        currentAudioRef.current = null;
      }
      
      // Set audio blob for reactive avatar FIRST so avatar can react
      setCurrentAudioBlob(audioBlob);
      setIsAISpeaking(true);
      
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      // Set volume to ensure it's audible
      audio.volume = 1.0;
      
      // Set up event handlers BEFORE trying to play
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
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      };
      
      audio.onerror = (error) => {
        console.error('Audio element error:', error, audio.error);
        URL.revokeObjectURL(audioUrl);
        setIsAISpeaking(false);
        setCurrentAudioBlob(null);
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      };
      
      // Pause handler - stop if component unmounts
      audio.onpause = () => {
        if (!isMountedRef.current && currentAudioRef.current === audio) {
          URL.revokeObjectURL(audioUrl);
          setIsAISpeaking(false);
          setCurrentAudioBlob(null);
          currentAudioRef.current = null;
        }
      };
      
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
        console.log('Audio playback started successfully');
        // Audio played successfully, clear any pending audio
        setPendingAudio(null);
        pendingAudioRef.current = null;
      } catch (playError) {
        console.warn('Initial play attempt failed:', playError.name, playError.message);
        
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
            text: chatResponse.message || `Hi! I'm Wally. I'm here to help you practice your ${profile.accent} accent. What are you passionate about?`,
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
              audioToPlay = await ttsService.generateSpeech(initialMessage.text, null, accentName);
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
    
    // Mark as unmounted
    isMountedRef.current = false;
    
    if (audioCapture) {
      audioCapture.cleanup();
    }
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
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
        <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-xl min-h-[calc(100vh-250px)] flex flex-col items-center justify-center p-8">
          {/* Audio-Reactive Avatar */}
          <div className="mb-8">
            <AudioReactiveAvatar
              audioBlob={currentAudioBlob}
              isSpeaking={isAISpeaking}
              onAnimationComplete={() => {
                setIsAISpeaking(false);
                setCurrentAudioBlob(null);
              }}
            />
          </div>

          {/* Current AI Message Display */}
          {currentAIMessage && (
            <div className="max-w-2xl mb-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
                <div className="flex items-center gap-2 mb-3 justify-center">
                  <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
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
                        className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-indigo-100 hover:bg-indigo-200 text-indigo-600 transition-colors"
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
                className="px-6 py-3 bg-indigo-500 text-white rounded-lg font-semibold hover:bg-indigo-600 transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
                <span>Play Wally's Message</span>
              </button>
            </div>
          )}

            {/* Conversation History (Minimal) */}
          {messages.length > 0 && (
            <div className="w-full max-w-2xl mb-6">
              <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 max-h-48 overflow-y-auto">
                <div className="space-y-2">
                  {messages.slice(-3).map((message) => (
                    <div
                      key={message.id}
                      className={`text-sm flex items-start gap-2 ${
                        message.type === 'user' ? 'text-right text-indigo-700 justify-end' : 'text-left text-gray-600'
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
                          className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-indigo-100 hover:bg-indigo-200 text-indigo-600 transition-colors"
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
          )}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="mb-6">
              <div className="bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600"></div>
                <span className="text-sm text-gray-700 font-medium">Processing your message...</span>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="w-full max-w-md mt-8">
            {!isRecording ? (
              <button
                onClick={startListening}
                disabled={isProcessing || !audioCapture || isAISpeaking}
                className="w-full px-8 py-6 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-2xl font-semibold text-lg hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
                <span>Tap to Speak</span>
              </button>
            ) : (
              <button
                onClick={stopListening}
                className="w-full px-8 py-6 bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-2xl font-semibold text-lg hover:from-red-600 hover:to-pink-700 flex items-center justify-center gap-3 shadow-lg animate-pulse"
              >
                <div className="w-4 h-4 bg-white rounded-full"></div>
                <span>Recording... Tap to Stop</span>
              </button>
            )}
            <p className="text-sm text-gray-600 text-center mt-4">
              {isRecording
                ? '🎤 Speak naturally - Wally is listening!'
                : isAISpeaking
                ? '👂 Listen to Wally\'s response...'
                : 'Click the button above to start speaking with Wally'}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LiveChat;

