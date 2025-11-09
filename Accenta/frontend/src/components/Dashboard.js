import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService, getUserStorageKey, profileService } from '../services/api';
import { getSkillLevel, getSkillsForAccent, ENGLISH_SKILLS, getProgressPercentage, SKILL_LEVELS } from '../data/skills';
import { getCoursesForLevel } from '../data/courses';
import { getLessonPhrases } from '../data/lessonPhrases';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [currentProfile, setCurrentProfile] = useState(null);
  const [profileSettings, setProfileSettings] = useState({
    nickname: '',
    colorScheme: 'blueOrange',
    profilePic: null,
  });
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [profilePicPreview, setProfilePicPreview] = useState(null);
  const fileInputRef = useRef(null);
  const [isImageEditorOpen, setIsImageEditorOpen] = useState(false);
  const [imageToEdit, setImageToEdit] = useState(null);
  const [imageScale, setImageScale] = useState(1);
  const [imageRotation, setImageRotation] = useState(0);
  const [imagePosition, setImagePosition] = useState({ x: 0, y: 0 });
  const imageEditorRef = useRef(null);
  const canvasRef = useRef(null);
  const [isAccentDropdownOpen, setIsAccentDropdownOpen] = useState(false);
  const accentDropdownRef = useRef(null);
  const [activeSection, setActiveSection] = useState('learn'); // 'learn' or 'practice'
  const [selectedSkillLevel, setSelectedSkillLevel] = useState(null);

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
          if (parsed.profilePic) {
            setProfilePicPreview(parsed.profilePic);
          }
        } catch (error) {
          console.error('Error loading profile settings:', error);
        }
      }
    }
  }, [user]);

  // Get user display name (nickname or username)
  const getDisplayName = () => {
    if (profileSettings.nickname) return profileSettings.nickname;
    return user?.username || 'User';
  };

  // Get user initials for profile picture
  const getUserInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Color scheme configurations
  const colorSchemes = {
    blueOrange: {
      name: 'Blue & Orange',
      gradient: 'from-blue-900 via-cyan-800 to-orange-800',
      primary: 'from-blue-900 via-cyan-800 to-orange-800',
      accent: 'from-blue-400 to-orange-400',
      button: 'bg-blue-600 hover:bg-blue-700',
      border: 'border-blue-200',
      cardGradient: 'from-blue-600 to-cyan-600',
      cardGradient2: 'from-blue-600 to-orange-600',
      cardGradient3: 'from-orange-600 to-blue-600',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      hoverBg: 'hover:bg-blue-100',
      backgroundGradient: 'from-blue-900 via-cyan-800 to-orange-800',
    },
    pink: {
      name: 'Pink',
      gradient: 'from-pink-50 via-rose-50 to-fuchsia-50',
      primary: 'from-pink-400 via-rose-400 to-fuchsia-400',
      accent: 'from-pink-600 to-rose-600',
      button: 'bg-pink-600 hover:bg-pink-700',
      border: 'border-pink-100',
      cardGradient: 'from-pink-500 to-rose-600',
      cardGradient2: 'from-pink-500 to-fuchsia-600',
      cardGradient3: 'from-rose-500 to-pink-600',
      textColor: 'text-pink-600',
      bgColor: 'bg-pink-50',
      hoverBg: 'hover:bg-pink-100',
    },
    purple: {
      name: 'Purple',
      gradient: 'from-purple-50 via-indigo-50 to-pink-50',
      primary: 'from-purple-400 via-indigo-400 to-pink-400',
      accent: 'from-purple-600 to-indigo-600',
      button: 'bg-purple-600 hover:bg-purple-700',
      border: 'border-purple-100',
      cardGradient: 'from-purple-500 to-indigo-600',
      cardGradient2: 'from-purple-500 to-pink-600',
      cardGradient3: 'from-indigo-500 to-purple-600',
      textColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      hoverBg: 'hover:bg-purple-100',
    },
    blue: {
      name: 'Blue',
      gradient: 'from-blue-50 via-cyan-50 to-teal-50',
      primary: 'from-blue-400 via-cyan-400 to-teal-400',
      accent: 'from-blue-600 to-cyan-600',
      button: 'bg-blue-600 hover:bg-blue-700',
      border: 'border-blue-100',
      cardGradient: 'from-blue-500 to-cyan-600',
      cardGradient2: 'from-blue-500 to-teal-600',
      cardGradient3: 'from-cyan-500 to-blue-600',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      hoverBg: 'hover:bg-blue-100',
    },
    green: {
      name: 'Green',
      gradient: 'from-green-50 via-emerald-50 to-teal-50',
      primary: 'from-green-400 via-emerald-400 to-teal-400',
      accent: 'from-green-600 to-emerald-600',
      button: 'bg-green-600 hover:bg-green-700',
      border: 'border-green-100',
      cardGradient: 'from-green-500 to-emerald-600',
      cardGradient2: 'from-green-500 to-teal-600',
      cardGradient3: 'from-emerald-500 to-green-600',
      textColor: 'text-green-600',
      bgColor: 'bg-green-50',
      hoverBg: 'hover:bg-green-100',
    },
  };

  const currentColorScheme = colorSchemes[profileSettings.colorScheme] || colorSchemes.blueOrange;

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // Handle profile picture upload
  const handleProfilePicChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        const imageUrl = reader.result;
        setImageToEdit(imageUrl);
        setIsImageEditorOpen(true);
        setImageScale(1);
        setImageRotation(0);
        setImagePosition({ x: 0, y: 0 });
      };
      reader.readAsDataURL(file);
    }
  };

  // Apply image adjustments and crop
  const applyImageEdit = () => {
    if (!imageToEdit) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const img = new Image();
    img.onload = () => {
      const size = 400; // Output size for profile picture
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      
      // Clear canvas
      ctx.clearRect(0, 0, size, size);
      
      // Calculate center position
      const centerX = size / 2;
      const centerY = size / 2;
      
      // Save context
      ctx.save();
      
      // Move to center
      ctx.translate(centerX, centerY);
      
      // Apply rotation
      ctx.rotate((imageRotation * Math.PI) / 180);
      
      // Apply scale
      const scaledWidth = img.width * imageScale;
      const scaledHeight = img.height * imageScale;
      
      // Draw image centered
      ctx.drawImage(
        img,
        -scaledWidth / 2 + imagePosition.x,
        -scaledHeight / 2 + imagePosition.y,
        scaledWidth,
        scaledHeight
      );
      
      // Restore context
      ctx.restore();
      
      // Convert to data URL
      const croppedImageUrl = canvas.toDataURL('image/png');
      setProfilePicPreview(croppedImageUrl);
      setProfileSettings((prev) => ({ ...prev, profilePic: croppedImageUrl }));
      setIsImageEditorOpen(false);
      setImageToEdit(null);
    };
    img.src = imageToEdit;
  };

  // Cancel image editing
  const cancelImageEdit = () => {
    setIsImageEditorOpen(false);
    setImageToEdit(null);
    setImageScale(1);
    setImageRotation(0);
    setImagePosition({ x: 0, y: 0 });
  };

  // Save profile settings (email-specific)
  const handleSaveProfile = () => {
    const currentUser = authService.getCurrentUser();
    if (currentUser?.email) {
      const settingsToSave = {
        ...profileSettings,
        profilePic: profilePicPreview,
      };
      const storageKey = getUserStorageKey('profileSettings', currentUser.email);
      localStorage.setItem(storageKey, JSON.stringify(settingsToSave));
      setIsEditModalOpen(false);
      window.location.reload();
    }
  };

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    localStorage.setItem('hasVisitedDashboard', 'true');

    if (!currentUser?.email) {
      setProfiles([]);
      setCurrentProfile(null);
      return;
    }

    const email = currentUser.email;
    const selectedFromState = location.state?.selectedProfileId;
    let storedProfiles = profileService.loadProfiles(email).map((profile) => {
      const generatedId = profile.profileId || profileService.generateProfileId(profile.language, profile.accent);
      let normalizedSkillLevel = profile.skillLevel;
      if (normalizedSkillLevel && typeof normalizedSkillLevel === 'string') {
        normalizedSkillLevel = Object.values(SKILL_LEVELS).find((level) => level.name === normalizedSkillLevel) || getSkillLevel(profile.overallScore || 0);
      } else if (!normalizedSkillLevel) {
        normalizedSkillLevel = getSkillLevel(profile.overallScore || 0);
      }

      const skills = profile.skills && profile.skills.length
        ? profile.skills
        : ENGLISH_SKILLS.map((skill) => ({
            ...skill,
            score: Math.max(0, Math.min(100, (profile.overallScore || 50) + (Math.random() * 20 - 10)))
          }));

      return {
        ...profile,
        profileId: generatedId,
        id: generatedId,
        skillLevel: normalizedSkillLevel,
        overallScore: profile.overallScore ?? 0,
        totalSessions: profile.totalSessions ?? 0,
        practiceTime: profile.practiceTime ?? 0,
        struggleAreas: profile.struggleAreas ?? [],
        skills,
        lastPracticed: profile.lastPracticed || Date.now(),
      };
    });

    storedProfiles.sort((a, b) => (b.lastPracticed || 0) - (a.lastPracticed || 0));
    setProfiles(storedProfiles);

    if (!storedProfiles.length) {
      setCurrentProfile(null);
      profileService.setSelectedProfileId(null, email);
      return;
    }

    let selectedId = selectedFromState || profileService.getSelectedProfileId(email);
    let activeProfile = selectedId ? storedProfiles.find((profile) => profile.profileId === selectedId) : null;

    if (!activeProfile) {
      activeProfile = storedProfiles[0];
      selectedId = activeProfile.profileId;
    }

    setCurrentProfile(activeProfile);
    profileService.setSelectedProfileId(selectedId, email);

    if (activeProfile?.skillLevel) {
      setSelectedSkillLevel(activeProfile.skillLevel);
    }

    if (selectedFromState) {
      navigate('/dashboard', { replace: true, state: {} });
    }
  }, [location.state, navigate]);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleStartNew = () => {
    navigate('/language-selection');
  };

  const handleViewProfile = () => {
    navigate('/profile');
  };

  // Toggle accent expansion (for accents list)
  const [expandedAccents, setExpandedAccents] = useState(new Set());
  const sectionRefs = useRef({});

  const toggleAccent = (accentId) => {
    setExpandedAccents((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(accentId)) {
        newSet.delete(accentId);
      } else {
        newSet.add(accentId);
      }
      return newSet;
    });
  };

  const handleSwitchAccent = (profile) => {
    if (!profile) return;
    setCurrentProfile(profile);
    const currentUser = authService.getCurrentUser();
    if (currentUser?.email && profile.profileId) {
      profileService.setSelectedProfileId(profile.profileId, currentUser.email);
    }
  };

  useEffect(() => {
    if (!currentProfile) return;

    let skillLevel = currentProfile.skillLevel;
    if (skillLevel && typeof skillLevel === 'string') {
      skillLevel = Object.values(SKILL_LEVELS).find((level) => level.name === skillLevel) || SKILL_LEVELS.INTERMEDIATE;
    }

    setSelectedSkillLevel(skillLevel || SKILL_LEVELS.INTERMEDIATE);
  }, [currentProfile]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (accentDropdownRef.current && !accentDropdownRef.current.contains(event.target)) {
        setIsAccentDropdownOpen(false);
      }
    };

    if (isAccentDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isAccentDropdownOpen]);

  return (
    <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.primary}`}>
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20 relative z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div 
              className="text-white text-3xl font-bold cursor-pointer hover:text-orange-300 transition-colors"
              onClick={() => navigate('/')}
            >
              accenta
            </div>
            <div className="flex items-center gap-4">
              {/* Accent Dropdown */}
              {profiles.length > 0 && (
                <div className="relative" ref={accentDropdownRef}>
                  <button
                    onClick={() => setIsAccentDropdownOpen(!isAccentDropdownOpen)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-white/20 bg-white/10 hover:bg-white/20 text-white/90 hover:text-white transition-colors font-medium"
                  >
                    <span>
                      {typeof currentProfile?.accent === 'object' 
                        ? currentProfile?.accent?.name 
                        : currentProfile?.accent || 'Select Accent'}
                    </span>
                    <svg 
                      className={`w-4 h-4 transition-transform ${isAccentDropdownOpen ? 'rotate-180' : ''}`}
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {isAccentDropdownOpen && (
                    <div className={`absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border-2 ${currentColorScheme.border} z-[100] max-h-96 overflow-y-auto`}>
                      <div className="p-2">
                        {profiles.map((profile) => {
                          const accentName = typeof profile.accent === 'object' ? profile.accent?.name : profile.accent;
                          const languageName = typeof profile.language === 'object' ? profile.language?.name : profile.language;
                          const isCurrent = currentProfile?.profileId === profile.profileId;
                          
                          return (
                            <button
                              key={profile.profileId || accentName}
                              onClick={() => {
                                handleSwitchAccent(profile);
                                setIsAccentDropdownOpen(false);
                              }}
                              className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                                isCurrent 
                                  ? `${currentColorScheme.bgColor} ${currentColorScheme.textColor} font-semibold` 
                                  : 'hover:bg-gray-100 text-gray-700'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="font-medium">{accentName}</p>
                                  <p className="text-sm text-gray-500">{languageName}</p>
                                </div>
                                {isCurrent && (
                                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                  </svg>
                                )}
                              </div>
                              <p className="text-xs text-gray-400 mt-1">Score: {profile.overallScore}%</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
              <button
                onClick={handleStartNew}
                className="text-white/90 hover:text-white font-medium transition-colors px-4 py-2 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Learn New Language</span>
              </button>
              <button
                onClick={handleLogout}
                className="text-white/90 hover:text-white font-medium transition-colors px-4 py-2"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Profile Header Bubble */}
        {user && (
          <div className="flex flex-wrap justify-center gap-6 mb-8">
            {/* Profile Picture Bubble */}
            <div className="relative">
              {profilePicPreview ? (
                <img
                  src={profilePicPreview}
                  alt="Profile"
                  className="w-32 h-32 rounded-full object-cover shadow-2xl ring-4 ring-white/50"
                />
              ) : (
                <div className={`w-32 h-32 rounded-full bg-gradient-to-br ${currentColorScheme.primary} flex items-center justify-center text-white text-4xl font-bold shadow-2xl ring-4 ring-white/50`}>
                  {getUserInitials(getDisplayName())}
                </div>
              )}
              <div className="absolute -bottom-2 -right-2 w-10 h-10 bg-green-400 rounded-full border-4 border-white shadow-lg"></div>
            </div>
            
            {/* Greeting Bubble */}
            <div className={`bg-white/90 backdrop-blur-sm rounded-full px-8 py-6 shadow-xl flex flex-col items-center justify-center min-w-[280px]`}>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                {getGreeting()}, {getDisplayName()}! 👋
              </h1>
              <p className="text-sm text-gray-600 mb-2">{user?.email}</p>
              {(() => {
                // Hardcoded to always show Intermediate
                const skillLevelName = 'Intermediate';
                
                return (
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-semibold text-gray-700">Skill Level:</span>
                    <span className="px-2 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-800">
                      {skillLevelName}
                    </span>
                  </div>
                );
              })()}
            </div>

            {/* Edit Profile Bubble */}
            <button
              onClick={() => setIsEditModalOpen(true)}
              className={`bg-white/90 backdrop-blur-sm rounded-full px-6 py-6 shadow-xl hover:shadow-2xl transition-all hover:scale-105 flex items-center gap-2 font-semibold`}
              style={{ color: `var(--${profileSettings.colorScheme}-600)` }}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Edit Profile</span>
            </button>
          </div>
        )}

        {/* Test Complete Message */}
        {location.state?.testComplete && (
          <div className="mb-6 flex justify-center">
            <div className="bg-green-100/90 backdrop-blur-sm border-2 border-green-300 rounded-full px-6 py-3 shadow-lg">
              <p className="text-green-800 font-semibold">
                ✓ Initial assessment complete! Your {typeof location.state.accent === 'object' ? location.state.accent?.name : location.state.accent} accent score: {location.state.initialScore?.toFixed(1)}%
              </p>
            </div>
          </div>
        )}

        {/* Section Tabs */}
        {currentProfile && (
          <div className="mb-8 flex justify-center gap-4 border-b-2 border-white/20 pb-4">
            <button
              onClick={() => setActiveSection('learn')}
              className={`px-8 py-3 text-lg font-semibold transition-all ${
                activeSection === 'learn'
                  ? 'text-white border-b-4 border-white'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              Learn
            </button>
            <button
              onClick={() => setActiveSection('practice')}
              className={`px-8 py-3 text-lg font-semibold transition-all ${
                activeSection === 'practice'
                  ? 'text-white border-b-4 border-white'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              Practice
            </button>
          </div>
        )}

        {/* Learn Section */}
        {currentProfile && activeSection === 'learn' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* Header with Title and Skill Level Selector */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-6">
                Complete {typeof currentProfile.language === 'object' ? currentProfile.language?.name : currentProfile.language || 'English'}
              </h1>
              
              {/* Skill Level Selector */}
              <div className="relative inline-block w-64">
                <select
                  value={selectedSkillLevel?.name || SKILL_LEVELS.INTERMEDIATE.name}
                  onChange={(e) => {
                    const level = Object.values(SKILL_LEVELS).find(l => l.name === e.target.value);
                    setSelectedSkillLevel(level || SKILL_LEVELS.INTERMEDIATE);
                  }}
                  className="w-full px-4 py-3 pl-12 border-2 border-gray-200 rounded-lg appearance-none bg-white text-gray-900 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer"
                >
                  {Object.values(SKILL_LEVELS).map((level) => (
                    <option key={level.name} value={level.name}>
                      {level.name}
                    </option>
                  ))}
                </select>
                <div className="absolute left-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Course Chapters */}
            {(() => {
              const languageId = typeof currentProfile.language === 'object' ? currentProfile.language?.id : 'english';
              const courses = getCoursesForLevel(languageId, selectedSkillLevel || currentProfile.skillLevel);
              
              return courses.length > 0 ? (
                courses.map((chapter) => (
                  <div key={chapter.id} className="mb-8 border-2 border-gray-200 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-2xl font-bold text-gray-900">{chapter.title}</h2>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-green-600">{chapter.progress}%</span>
                        <div className="w-32 h-2 bg-gray-200 rounded-full">
                          <div
                            className="h-2 bg-green-500 rounded-full transition-all duration-500"
                            style={{ width: `${chapter.progress}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    
                    {/* Lessons */}
                    <div className="space-y-3">
                      {chapter.lessons.map((lesson, index) => (
                        <div
                          key={lesson.id}
                          className={`flex items-center gap-4 p-4 rounded-lg border-2 transition-all ${
                            lesson.unlocked
                              ? 'bg-blue-50 border-blue-200 hover:bg-blue-100 cursor-pointer'
                              : 'bg-gray-50 border-gray-200 opacity-60'
                          }`}
                          onClick={() => {
                            if (lesson.unlocked) {
                              // Get lesson-specific phrases
                              const lessonPhrases = getLessonPhrases(lesson.id);
                              if (lessonPhrases.length > 0) {
                                // Navigate to practice with lesson-specific phrases (10 questions)
                                navigate('/practice', {
                                  state: {
                                    profile: currentProfile,
                                    customPhrases: lessonPhrases.slice(0, 10), // Ensure exactly 10 questions
                                    lessonId: lesson.id,
                                    lessonTitle: lesson.title,
                                  },
                                });
                              } else {
                                // Fallback to regular practice if no lesson phrases
                                navigate('/practice', {
                                  state: {
                                    profile: currentProfile,
                                  },
                                });
                              }
                            }
                          }}
                        >
                          {/* Lesson Icon/Avatar */}
                          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl ${
                            lesson.unlocked ? 'bg-yellow-400' : 'bg-gray-300 relative'
                          }`}>
                            {lesson.unlocked ? (
                              lesson.icon
                            ) : (
                              <>
                                <div className="absolute inset-0 bg-gray-400 rounded-full opacity-50"></div>
                                <svg className="w-8 h-8 text-white absolute z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                              </>
                            )}
                          </div>
                          
                          {/* Lesson Info */}
                          <div className="flex-1">
                            <h3 className={`text-lg font-bold mb-1 ${lesson.unlocked ? 'text-gray-900' : 'text-gray-400'}`}>
                              {lesson.title}
                            </h3>
                            <p className={`text-sm ${lesson.unlocked ? 'text-gray-600' : 'text-gray-400'}`}>
                              {lesson.description}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-600 text-lg">No courses available for this skill level yet.</p>
                </div>
              );
            })()}
          </div>
        )}

        {/* Practice Section */}
        {currentProfile && activeSection === 'practice' && (
          <div className="p-8">
            {/* Practice Types */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Wally */}
              <div
                onClick={() => navigate('/live-chat', { state: { profile: currentProfile } })}
                className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-blue-400 hover:shadow-lg transition-all cursor-pointer flex flex-col items-center text-center h-full"
              >
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Wally</h3>
                <p className="text-gray-600 mb-6 flex-1">Have a natural conversation with Wally, your friendly chat buddy</p>
                <button className={`w-full px-6 py-3 ${currentColorScheme.button} text-white rounded-lg font-semibold hover:shadow-lg transition-all`}>
                  Start
                </button>
              </div>

              {/* Call and Response */}
              <div
                onClick={() => navigate('/practice', { state: { profile: currentProfile } })}
                className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-blue-400 hover:shadow-lg transition-all cursor-pointer flex flex-col items-center text-center h-full"
              >
                <div className="text-6xl mb-4">🎤</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Call and Response</h3>
                <p className="text-gray-600 mb-6 flex-1">Practice phrases with instant feedback and detailed analysis</p>
                <button className={`w-full px-6 py-3 ${currentColorScheme.button} text-white rounded-lg font-semibold hover:shadow-lg transition-all`}>
                  Start
                </button>
              </div>

              {/* Timed Practice */}
              <div
                onClick={() => navigate('/practice', { state: { profile: currentProfile, timedMode: true, showDifficultySelection: true } })}
                className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-blue-400 hover:shadow-lg transition-all cursor-pointer flex flex-col items-center text-center h-full"
              >
                <div className="text-6xl mb-4">⏱️</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Timed Practice</h3>
                <p className="text-gray-600 mb-6 flex-1">Challenge yourself with time-limited sessions to build fluency</p>
                <button className={`w-full px-6 py-3 ${currentColorScheme.button} text-white rounded-lg font-semibold hover:shadow-lg transition-all`}>
                  Start
                </button>
              </div>
            </div>
          </div>
        )}

        {/* No Profile State */}
        {!currentProfile && (
          <div className="flex justify-center">
            <div className="bg-white/90 backdrop-blur-sm rounded-full shadow-xl p-12 text-center max-w-md">
              <div className="text-6xl mb-4">🎯</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Get Started with Accenta</h2>
              <p className="text-gray-600 mb-6">
                You haven't started learning any accents yet. Choose a language and accent to begin your journey!
              </p>
              <button
                onClick={handleStartNew}
                className={`${currentColorScheme.button} text-white px-8 py-3 rounded-full font-semibold hover:shadow-lg transition-all hover:scale-105`}
              >
                Start Learning
              </button>
            </div>
          </div>
        )}

      </main>

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Edit Profile</h2>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Profile Picture */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Profile Picture
                </label>
                <div className="flex items-center gap-6">
                  <div className="relative">
                    {profilePicPreview ? (
                      <img
                        src={profilePicPreview}
                        alt="Profile preview"
                        className="w-24 h-24 rounded-full object-cover shadow-md"
                      />
                    ) : (
                      <div className={`w-24 h-24 rounded-full bg-gradient-to-br ${currentColorScheme.primary} flex items-center justify-center text-white text-2xl font-bold shadow-md`}>
                        {getUserInitials(getDisplayName())}
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleProfilePicChange}
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 font-medium transition-colors"
                    >
                      Upload Photo
                    </button>
                    {profilePicPreview && (
                      <button
                        onClick={() => {
                          setProfilePicPreview(null);
                          setProfileSettings((prev) => ({ ...prev, profilePic: null }));
                        }}
                        className="ml-2 px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg text-red-700 font-medium transition-colors"
                      >
                        Remove
                      </button>
                    )}
                    <p className="text-xs text-gray-500 mt-2">JPG, PNG or GIF. Max size 5MB</p>
                  </div>
                </div>
              </div>

              {/* Nickname */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Nickname
                </label>
                <input
                  type="text"
                  value={profileSettings.nickname}
                  onChange={(e) => setProfileSettings((prev) => ({ ...prev, nickname: e.target.value }))}
                  placeholder={user?.username || 'Enter your nickname'}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent outline-none transition-all"
                />
                <p className="text-xs text-gray-500 mt-1">This will be displayed instead of your username</p>
              </div>

              {/* Color Scheme */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Color Scheme
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(colorSchemes).map(([key, scheme]) => (
                    <button
                      key={key}
                      onClick={() => setProfileSettings((prev) => ({ ...prev, colorScheme: key }))}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        profileSettings.colorScheme === key
                          ? 'border-pink-500 ring-2 ring-pink-200'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className={`h-12 rounded-lg bg-gradient-to-br ${scheme.gradient} mb-2`}></div>
                      <p className="text-sm font-medium text-gray-700">{scheme.name}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveProfile}
                className={`px-6 py-2 ${currentColorScheme.button} text-white rounded-lg font-semibold transition-colors shadow-md`}
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Editor Modal */}
      {isImageEditorOpen && imageToEdit && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Adjust Profile Picture</h2>
              <button
                onClick={cancelImageEdit}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Image Preview */}
              <div className="flex justify-center">
                <div className="relative w-80 h-80 rounded-full overflow-hidden border-4 border-gray-200 bg-gray-100">
                  <img
                    src={imageToEdit}
                    alt="Preview"
                    className="w-full h-full object-cover"
                    style={{
                      transform: `scale(${imageScale}) rotate(${imageRotation}deg) translate(${imagePosition.x}px, ${imagePosition.y}px)`,
                      transition: 'transform 0.1s ease-out',
                    }}
                  />
                </div>
              </div>

              {/* Hidden canvas for final image */}
              <canvas ref={canvasRef} className="hidden" />

              {/* Controls */}
              <div className="space-y-4">
                {/* Zoom Control */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Zoom: {Math.round(imageScale * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="3"
                    step="0.1"
                    value={imageScale}
                    onChange={(e) => setImageScale(parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>50%</span>
                    <span>300%</span>
                  </div>
                </div>

                {/* Rotation Control */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Rotation: {imageRotation}°
                  </label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    value={imageRotation}
                    onChange={(e) => setImageRotation(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>-180°</span>
                    <span>0°</span>
                    <span>180°</span>
                  </div>
                </div>

                {/* Position Controls */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Position
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => setImagePosition({ ...imagePosition, y: imagePosition.y - 10 })}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 font-medium transition-colors"
                    >
                      ↑ Up
                    </button>
                    <button
                      onClick={() => setImagePosition({ x: 0, y: 0 })}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 font-medium transition-colors"
                    >
                      Reset
                    </button>
                    <button
                      onClick={() => setImagePosition({ ...imagePosition, y: imagePosition.y + 10 })}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 font-medium transition-colors"
                    >
                      ↓ Down
                    </button>
                    <button
                      onClick={() => setImagePosition({ ...imagePosition, x: imagePosition.x - 10 })}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 font-medium transition-colors"
                    >
                      ← Left
                    </button>
                    <div className="px-4 py-2"></div>
                    <button
                      onClick={() => setImagePosition({ ...imagePosition, x: imagePosition.x + 10 })}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 font-medium transition-colors"
                    >
                      Right →
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={cancelImageEdit}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={applyImageEdit}
                className={`px-6 py-2 ${currentColorScheme.button} text-white rounded-lg font-semibold transition-colors shadow-md`}
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

