import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/api';
import { SKILL_LEVELS, getSkillsForAccent } from '../data/skills';
import { profileManager } from '../utils/profileManager';

const Survey = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { language, accent } = location.state || {};
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedReason, setSelectedReason] = useState(null);
  const [knowsLevel, setKnowsLevel] = useState(null);
  const [selectedSkillLevel, setSelectedSkillLevel] = useState(null);
  const [user, setUser] = useState(null);
  const [profileSettings, setProfileSettings] = useState({
    nickname: '',
    colorScheme: 'blueOrange',
    profilePic: null,
  });

  useEffect(() => {
    if (!language || !accent) {
      navigate('/language-selection');
      return;
    }

    const currentUser = authService.getCurrentUser();
    setUser(currentUser);

    // Load profile settings
    const savedSettings = localStorage.getItem('profileSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setProfileSettings(parsed);
      } catch (error) {
        console.error('Error loading profile settings:', error);
      }
    }
  }, [language, accent, navigate]);

  const getDisplayName = () => {
    if (profileSettings.nickname) return profileSettings.nickname;
    return user?.username || 'there';
  };

  // Total steps depends on whether user knows their level or if we're already on step 3
  const totalSteps = (knowsLevel === 'know' || currentStep === 3) ? 3 : 2;
  const progress = (currentStep / totalSteps) * 100;

  const learningReasons = [
    { id: 'work', label: 'Work', icon: '🤝' },
    { id: 'school', label: 'School', icon: '📚' },
    { id: 'travel', label: 'Travel', icon: '✈️' },
    { id: 'culture', label: 'Culture', icon: '🎨' },
    { id: 'family', label: 'Family & community', icon: '👋' },
    { id: 'challenge', label: 'Challenge myself', icon: '💪' },
    { id: 'other', label: 'Other', icon: '💬' },
  ];

  const handleReasonSelect = (reasonId) => {
    setSelectedReason(reasonId);
    setTimeout(() => setCurrentStep(2), 300);
  };

  const handleLevelChoice = (choice) => {
    if (choice === 'need-help') {
      // Navigate to initial test
      navigate('/initial-test', {
        state: {
          language,
          accent,
          learningReason: selectedReason,
        },
      });
    } else if (choice === 'know' && currentStep === 2) {
      // Move to skill level selection step
      setKnowsLevel(choice);
      setTimeout(() => setCurrentStep(3), 300);
    }
  };

const handleSkillLevelSelect = (skillLevel) => {
  if (!skillLevel) return;
  setSelectedSkillLevel(skillLevel);
  const overallScore = (skillLevel.min + skillLevel.max) / 2;
  const languageId = typeof language === 'object' ? language.id : language;
  const accentId = typeof accent === 'object' ? accent.id : accent;
  const defaultSkills = getSkillsForAccent(languageId, accentId).map((skill) => ({
    ...skill,
    score: Math.round(overallScore),
  }));

  const createdProfile = profileManager.upsertProfile({
    language,
    accent,
    overallScore,
    skillLevel,
    learningReason: selectedReason,
    totalSessions: 0,
    practiceTime: 0,
    struggleAreas: [],
    skills: defaultSkills,
  });

  profileManager.setCurrentProfile(createdProfile);

  navigate('/first-practice-intro', {
    state: {
      profile: createdProfile,
      accent,
      fromSurvey: true,
      learningReason: selectedReason,
    },
  });
  };

  const skillLevels = [
    { id: 'BEGINNER', ...SKILL_LEVELS.BEGINNER, icon: '🌱', description: 'Just starting out' },
    { id: 'INTERMEDIATE', ...SKILL_LEVELS.INTERMEDIATE, icon: '📈', description: 'Getting comfortable' },
    { id: 'ADEPT', ...SKILL_LEVELS.ADEPT, icon: '⭐', description: 'Confident speaker' },
    { id: 'PRO', ...SKILL_LEVELS.PRO, icon: '🏆', description: 'Highly skilled' },
    { id: 'MASTER', ...SKILL_LEVELS.MASTER, icon: '👑', description: 'Native-like proficiency' },
  ];

  const getSkillLevelColor = (color) => {
    const colorMap = {
      red: 'from-red-400 to-red-600',
      orange: 'from-orange-400 to-orange-600',
      yellow: 'from-yellow-400 to-yellow-600',
      green: 'from-green-400 to-green-600',
      blue: 'from-blue-400 to-blue-600',
    };
    return colorMap[color] || 'from-gray-400 to-gray-600';
  };

  const accentName = typeof accent === 'object' ? accent.name : accent;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-cyan-800 to-orange-800 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10 z-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>

      {/* Progress Bar with Step Indicator */}
      <div className="relative z-20 pt-8 pb-4">
        <div className="max-w-2xl mx-auto px-6 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white/70 text-sm font-medium">Step {currentStep} of {totalSteps}</span>
            <span className="text-white/70 text-sm font-medium">{Math.round(progress)}%</span>
          </div>
          <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-orange-500 transition-all duration-500 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="relative z-20 max-w-3xl mx-auto px-6 py-8">
        {/* Step 1: Why are you learning? */}
        {currentStep === 1 && (
          <div className="animate-fadeIn">
            <div className="text-center mb-10">
              <div className="inline-block bg-white/10 backdrop-blur-md rounded-full px-6 py-2 mb-4">
                <span className="text-white/90 text-sm font-medium">Let's get to know you</span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 drop-shadow-lg">
                What's your motivation for learning{' '}
                <span className="bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent">
                  {accentName}
                </span>?
              </h1>
              <p className="text-white/80 text-center text-base max-w-xl mx-auto">
                Your answer helps us personalize your learning journey
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {learningReasons.map((reason) => (
                <button
                  key={reason.id}
                  onClick={() => handleReasonSelect(reason.id)}
                  className="bg-white/95 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-5 hover:border-blue-400 hover:shadow-2xl hover:scale-105 transition-all duration-300 text-center group relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-orange-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <div className="relative z-10">
                    <div className="text-5xl mb-3 transform group-hover:scale-110 transition-transform duration-300">
                      {reason.icon}
                    </div>
                    <div className="text-base font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                      {reason.label}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Do you know your level? */}
        {currentStep === 2 && (
          <div className="animate-fadeIn">
            <div className="text-center mb-10">
              <div className="inline-block bg-white/10 backdrop-blur-md rounded-full px-6 py-2 mb-4">
                <span className="text-white/90 text-sm font-medium">Almost there!</span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 drop-shadow-lg">
                How would you like to start?
              </h1>
              <p className="text-white/80 text-center text-base max-w-xl mx-auto">
                Choose the option that best fits your current situation
              </p>
            </div>

            <div className="space-y-3 mb-10">
              <button
                onClick={() => setKnowsLevel('know')}
                className={`w-full bg-white/95 backdrop-blur-sm border-2 rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 text-left group relative overflow-hidden ${
                  knowsLevel === 'know'
                    ? 'border-blue-500 shadow-xl scale-[1.02]'
                    : 'border-white/30 hover:border-blue-400 hover:scale-[1.01]'
                }`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br from-blue-50 to-transparent transition-opacity duration-300 ${
                  knowsLevel === 'know' ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                }`}></div>
                <div className="relative z-10 flex items-center gap-6">
                  <div className={`text-5xl transform transition-transform duration-300 ${
                    knowsLevel === 'know' ? 'scale-110' : 'group-hover:scale-110'
                  }`}>
                    👍
                  </div>
                  <div className="flex-1">
                    <div className="text-2xl font-bold text-gray-900 mb-2">
                      I know my level
                    </div>
                    <div className="text-sm text-gray-600">
                      I'm ready to start practicing right away
                    </div>
                  </div>
                  {knowsLevel === 'know' && (
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-orange-500 flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>
              </button>

              <button
                onClick={() => setKnowsLevel('need-help')}
                className={`w-full bg-white/95 backdrop-blur-sm border-2 rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 text-left group relative overflow-hidden ${
                  knowsLevel === 'need-help'
                    ? 'border-blue-500 shadow-xl scale-[1.02]'
                    : 'border-blue-300/50 hover:border-blue-400 hover:scale-[1.01]'
                }`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br from-blue-50 to-transparent transition-opacity duration-300 ${
                  knowsLevel === 'need-help' ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                }`}></div>
                <div className="relative z-10 flex items-center gap-6">
                  <div className={`text-5xl transform transition-transform duration-300 ${
                    knowsLevel === 'need-help' ? 'scale-110' : 'group-hover:scale-110'
                  }`}>
                    🔍
                  </div>
                  <div className="flex-1">
                    <div className="text-2xl font-bold text-gray-900 mb-2">
                      I need help finding my level
                    </div>
                    <div className="text-sm text-gray-600">
                      Take a quick assessment to discover where you stand
                    </div>
                  </div>
                  {knowsLevel === 'need-help' && (
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-orange-500 flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>
              </button>
            </div>

            <div className="flex justify-center">
              <button
                onClick={() => handleLevelChoice(knowsLevel)}
                disabled={!knowsLevel}
                className="px-10 py-4 bg-gradient-to-r from-blue-500 to-orange-500 text-white rounded-xl font-bold text-lg hover:shadow-2xl hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2"
              >
                <span>Continue</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Select your skill level */}
        {currentStep === 3 && (
          <div className="animate-fadeIn">
            <div className="text-center mb-10">
              <div className="inline-block bg-white/10 backdrop-blur-md rounded-full px-6 py-2 mb-4">
                <span className="text-white/90 text-sm font-medium">Final step!</span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 drop-shadow-lg">
                What's your current skill level?
              </h1>
              <p className="text-white/80 text-center text-base max-w-xl mx-auto">
                Select the level that best describes your proficiency with{' '}
                <span className="bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent font-semibold">
                  {accentName}
                </span>
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {skillLevels.map((level) => (
                <button
                  key={level.id}
                  onClick={() => setSelectedSkillLevel(level)}
                  className={`bg-white/95 backdrop-blur-sm border-2 rounded-2xl p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300 text-center group relative overflow-hidden ${
                    selectedSkillLevel?.id === level.id
                      ? 'border-blue-500 shadow-xl scale-[1.02]'
                      : 'border-white/30 hover:border-blue-400'
                  }`}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${getSkillLevelColor(level.color)} opacity-0 group-hover:opacity-10 transition-opacity duration-300 ${
                    selectedSkillLevel?.id === level.id ? 'opacity-20' : ''
                  }`}></div>
                  <div className="relative z-10">
                    <div className={`text-5xl mb-3 transform transition-transform duration-300 ${
                      selectedSkillLevel?.id === level.id ? 'scale-110' : 'group-hover:scale-110'
                    }`}>
                      {level.icon}
                    </div>
                    <div className={`text-xl font-bold mb-2 transition-colors ${
                      selectedSkillLevel?.id === level.id ? 'text-blue-600' : 'text-gray-900 group-hover:text-blue-600'
                    }`}>
                      {level.name}
                    </div>
                    <div className="text-sm text-gray-600 mb-3">
                      {level.description}
                    </div>
                    <div className="text-xs text-gray-500">
                      Score range: {level.min}-{level.max}%
                    </div>
                    {selectedSkillLevel?.id === level.id && (
                      <div className="mt-4 flex justify-center">
                        <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-orange-500 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-center">
              <button
                onClick={() => handleSkillLevelSelect(selectedSkillLevel)}
                disabled={!selectedSkillLevel}
                className="px-10 py-4 bg-gradient-to-r from-blue-500 to-orange-500 text-white rounded-xl font-bold text-lg hover:shadow-2xl hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2"
              >
                <span>Complete Setup</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Survey;

