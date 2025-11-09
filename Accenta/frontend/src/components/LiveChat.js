import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService, getUserStorageKey, profileService } from '../services/api';
import AudioReactiveAvatar from './AudioReactiveAvatar';

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

const DEMO_CONVERSATION_TEMPLATE = [
  { id: 1, type: 'ai', buildText: (accentLabel) => `你好 (Nǐ hǎo)! 我是 Wally。准备好一起练习${accentLabel}口音了吗？` },
  { id: 2, type: 'user', buildText: () => 'Yeah, I would love to learn that accent. Can we start a conversation?' },
  { id: 3, type: 'ai', buildText: (accentLabel) => `太好了！我们先从常用问候开始。试试看：“你吃饭了吗儿？” 这是在${accentLabel}很常见的问候方式。` },
  { id: 4, type: 'user', buildText: () => '我吃了。' },
  { id: 5, type: 'ai', buildText: (accentLabel) => `很好！加上儿化音会更地道，比如“我吃了儿”。这样说听起来就很有${accentLabel}味儿。` },
];

const LiveChat = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile: stateProfile } = location.state || {};
  const [profileSettings, setProfileSettings] = useState({ colorScheme: 'blueOrange' });
  const [isRecording, setIsRecording] = useState(false);
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const user = authService.getCurrentUser();
  const email = user?.email;
  const storedProfiles = email ? profileService.loadProfiles(email) : [];
  const selectedProfileId = stateProfile?.profileId || (email ? profileService.getSelectedProfileId(email) : null);
  const resolvedProfile = stateProfile
    || (selectedProfileId ? storedProfiles.find((profile) => profile.profileId === selectedProfileId) : null)
    || storedProfiles[0]
    || null;
  const accentLabel = typeof resolvedProfile?.accent === 'object' ? resolvedProfile?.accent?.name : resolvedProfile?.accent || 'Beijing Mandarin';
  const demoConversation = DEMO_CONVERSATION_TEMPLATE.map((entry) => ({
    ...entry,
    text: entry.buildText ? entry.buildText(accentLabel) : entry.text,
  }));
  const aiMessages = demoConversation.filter(message => message.type === 'ai');
  const historyMessages = demoConversation;

  useEffect(() => {
    if (aiMessages.length > 0) {
      setCurrentStep(aiMessages.length - 1);
    }
  }, [accentLabel]);

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

  const currentColorScheme = colorSchemes[profileSettings.colorScheme] || colorSchemes.blueOrange;
  const currentAIMessage = aiMessages[currentStep]?.text || '';

  const toggleRecording = () => {
    setIsRecording(prev => !prev);
    if (!isAISpeaking) {
      setIsAISpeaking(true);
      setTimeout(() => setIsAISpeaking(false), 1200);
    }
  };

  const handleSimulateResponse = () => {
    setIsAISpeaking(true);
    setIsRecording(false);
    setCurrentStep(prev => (prev + 1) % aiMessages.length);
    setTimeout(() => setIsAISpeaking(false), 1500);
  };

  const handleBack = () => navigate('/dashboard');

  return (
    <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.backgroundGradient}`}>
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
            <h1 className="text-xl font-bold text-gray-900">Chat with Wally - {typeof resolvedProfile?.accent === 'object' ? resolvedProfile?.accent?.name : resolvedProfile?.accent || 'Beijing Mandarin'}</h1>
            <div className="w-32" />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className={`bg-gradient-to-br ${currentColorScheme.containerGradient} rounded-2xl shadow-xl min-h-[calc(100vh-250px)] flex flex-col items-center justify-center p-8`}>
          <div className="mb-8">
            <div
              onClick={toggleRecording}
              className="cursor-pointer transition-transform hover:scale-105 active:scale-95"
            >
              <AudioReactiveAvatar
                audioBlob={null}
                isSpeaking={isAISpeaking || isRecording}
                volumeLevel={isRecording ? 60 : 0}
                onAnimationComplete={() => setIsAISpeaking(false)}
              />
            </div>
            {isRecording && (
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-red-500/20 rounded-full">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                  <span className="text-sm text-red-700 font-medium">Recording look only • Tap Wally to stop</span>
                </div>
              </div>
            )}
          </div>

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
                  <button
                    onClick={handleSimulateResponse}
                    className={`flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full ${currentColorScheme.primaryLight} ${currentColorScheme.primaryText} transition-colors`}
                    title="Simulate next Wally response"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 10a8 8 0 1115.546 3.032 1 1 0 01-1.886-.667A6 6 0 1010 16h1.586a1 1 0 110 2H10a8 8 0 01-8-8z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="w-full max-w-2xl mb-6">
            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 max-h-48 overflow-y-auto">
              <div className="space-y-2">
                {historyMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`text-sm flex items-start gap-2 ${
                      message.type === 'user' ? `text-right ${currentColorScheme.primaryText} justify-end` : 'text-left text-gray-600'
                    }`}
                  >
                    <div className="flex-1">
                      {message.type === 'user' && <span className="font-medium">You: </span>}
                      {message.type === 'ai' && <span className="font-medium">Wally: </span>}
                      <span className="opacity-80">{message.text}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mb-6">
            <div className="bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 flex items-center gap-3">
              <div className={`rounded-full h-5 w-5 border-b-2 ${currentColorScheme.borderColor} animate-spin`} />
              <span className="text-sm text-gray-700 font-medium">Wally is currently offline. Visuals remain available for demo purposes.</span>
            </div>
          </div>

          <div className="w-full max-w-md mt-8">
            <p className="text-sm text-gray-600 text-center">
              点击 Wally 可以切换录音动画，或使用按钮轮播预设的北京口音提示。
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LiveChat;

