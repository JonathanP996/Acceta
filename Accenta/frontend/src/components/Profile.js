import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService, getUserStorageKey, profileService } from '../services/api';
import { getSkillLevel, getProgressPercentage, ENGLISH_SKILLS, SKILL_LEVELS } from '../data/skills';

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [currentProfile, setCurrentProfile] = useState(null);
  const [expandedAccents, setExpandedAccents] = useState(new Set());
  const [visibleSections, setVisibleSections] = useState(new Set());
  const sectionRefs = useRef({});
  
  // Profile settings state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [profileSettings, setProfileSettings] = useState({
    nickname: '',
    colorScheme: 'pink',
    profilePic: null, // Will store image URL or file
  });
  const [profilePicPreview, setProfilePicPreview] = useState(null);
  const fileInputRef = useRef(null);

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // Get user display name (nickname or username)
  const getDisplayName = () => {
    if (profileSettings.nickname) return profileSettings.nickname;
    return user?.username || 'there';
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
    pink: {
      name: 'Pink',
      gradient: 'from-pink-50 via-rose-50 to-fuchsia-50',
      primary: 'from-pink-400 via-rose-400 to-fuchsia-400',
      accent: 'from-pink-600 to-rose-600',
      button: 'bg-pink-600 hover:bg-pink-700',
      border: 'border-pink-100',
    },
    purple: {
      name: 'Purple',
      gradient: 'from-purple-50 via-indigo-50 to-pink-50',
      primary: 'from-purple-400 via-indigo-400 to-pink-400',
      accent: 'from-purple-600 to-indigo-600',
      button: 'bg-purple-600 hover:bg-purple-700',
      border: 'border-purple-100',
    },
    blue: {
      name: 'Blue',
      gradient: 'from-blue-50 via-cyan-50 to-teal-50',
      primary: 'from-blue-400 via-cyan-400 to-teal-400',
      accent: 'from-blue-600 to-cyan-600',
      button: 'bg-blue-600 hover:bg-blue-700',
      border: 'border-blue-100',
    },
    green: {
      name: 'Green',
      gradient: 'from-green-50 via-emerald-50 to-teal-50',
      primary: 'from-green-400 via-emerald-400 to-teal-400',
      accent: 'from-green-600 to-emerald-600',
      button: 'bg-green-600 hover:bg-green-700',
      border: 'border-green-100',
    },
  };

  const currentColorScheme = colorSchemes[profileSettings.colorScheme] || colorSchemes.pink;

  // Scroll animation observer
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setVisibleSections((prev) => new Set([...prev, entry.target.id]));
        }
      });
    }, observerOptions);

    // Observe all section refs
    Object.values(sectionRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => {
      Object.values(sectionRefs.current).forEach((ref) => {
        if (ref) observer.unobserve(ref);
      });
    };
  }, [profiles]);

  // Toggle accent expansion
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
  }, []);

  // Handle profile picture upload
  const handleProfilePicChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        const imageUrl = reader.result;
        setProfilePicPreview(imageUrl);
        setProfileSettings((prev) => ({ ...prev, profilePic: imageUrl }));
      };
      reader.readAsDataURL(file);
    }
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
      // Force re-render to update UI
      window.location.reload();
    }
  };

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    if (!currentUser?.email) {
      setProfiles([]);
      setCurrentProfile(null);
      return;
    }

    const email = currentUser.email;
    const storedProfiles = profileService.loadProfiles(email).map((profile) => {
      const profileId = profile.profileId || profileService.generateProfileId(profile.language, profile.accent);
      let skillLevel = profile.skillLevel;
      if (skillLevel && typeof skillLevel === 'string') {
        skillLevel = Object.values(SKILL_LEVELS).find((level) => level.name === skillLevel) || getSkillLevel(profile.overallScore || 0);
      } else if (!skillLevel) {
        skillLevel = getSkillLevel(profile.overallScore || 0);
      }

      const skills = profile.skills && profile.skills.length
        ? profile.skills
        : ENGLISH_SKILLS.map((skill) => ({
            ...skill,
            score: Math.max(0, Math.min(100, (profile.overallScore || 50) + (Math.random() * 20 - 10)))
          }));

      return {
        ...profile,
        profileId,
        skillLevel,
        skills,
        overallScore: profile.overallScore ?? 0,
        totalSessions: profile.totalSessions ?? 0,
        practiceTime: profile.practiceTime ?? 0,
        struggleAreas: profile.struggleAreas ?? [],
        lastPracticed: profile.lastPracticed || Date.now(),
      };
    });

    storedProfiles.sort((a, b) => (b.lastPracticed || 0) - (a.lastPracticed || 0));
    setProfiles(storedProfiles);
    setCurrentProfile(storedProfiles[0] || null);
  }, []);

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br ${currentColorScheme.gradient}`}>
      {/* Header with Back Button */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-700 hover:text-pink-600 flex items-center transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Profile Header with Picture and Greeting */}
        <div 
          className={`bg-white/90 backdrop-blur-sm rounded-3xl shadow-xl p-8 mb-8 border ${currentColorScheme.border}`}
          style={{
            opacity: 1,
            transform: 'translateY(0)',
            transition: 'opacity 0.6s ease, transform 0.6s ease'
          }}
        >
          <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
            {/* Profile Picture */}
            <div className="relative">
              {profilePicPreview ? (
                <img
                  src={profilePicPreview}
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover shadow-lg ring-4 ring-pink-200"
                />
              ) : (
                <div className={`w-24 h-24 rounded-full bg-gradient-to-br ${currentColorScheme.primary} flex items-center justify-center text-white text-3xl font-bold shadow-lg ring-4 ring-pink-200`}>
                  {getUserInitials(getDisplayName())}
                </div>
              )}
              <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-green-400 rounded-full border-4 border-white shadow-md"></div>
            </div>
            
            {/* Username and Greeting */}
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                {getGreeting()}, {getDisplayName()}! 👋
              </h1>
              <p className="text-lg text-gray-600 mb-2">{user?.email}</p>
              {(() => {
                // Get skill level from current profile (most recent)
                const profile = currentProfile || (profiles.length > 0 ? profiles[0] : null);
                let skillLevelName = null;
                
                if (profile) {
                  // Try to get skill level from profile
                  if (profile.skillLevel) {
                    const skillLevel = profile.skillLevel;
                    if (typeof skillLevel === 'object' && skillLevel.name) {
                      skillLevelName = skillLevel.name;
                    } else if (typeof skillLevel === 'string') {
                      skillLevelName = skillLevel;
                    }
                  }
                  
                  // Fallback: Calculate skill level from overall score if skillLevel is missing
                  if (!skillLevelName && profile.overallScore !== undefined) {
                    const calculatedLevel = getSkillLevel(profile.overallScore);
                    skillLevelName = calculatedLevel.name;
                  }
                }
                
                // Always show skill level if we have a profile (even if we need to calculate it)
                if (profile && !skillLevelName && profile.overallScore === undefined) {
                  // If no score, default to Beginner
                  skillLevelName = 'Beginner';
                }
                
                return skillLevelName ? (
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm font-semibold text-gray-700">Skill Level:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                      skillLevelName === 'Beginner' ? 'bg-red-100 text-red-800' :
                      skillLevelName === 'Intermediate' ? 'bg-orange-100 text-orange-800' :
                      skillLevelName === 'Adept' ? 'bg-yellow-100 text-yellow-800' :
                      skillLevelName === 'Pro' ? 'bg-green-100 text-green-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {skillLevelName}
                    </span>
                  </div>
                ) : null;
              })()}
            </div>

            {/* Edit Profile Button */}
            <button
              onClick={() => setIsEditModalOpen(true)}
              className={`px-4 py-2 bg-white/80 hover:bg-white border ${currentColorScheme.border} rounded-lg font-semibold transition-all hover:shadow-md flex items-center gap-2`}
              style={{ color: `var(--${profileSettings.colorScheme}-600)` }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit Profile
            </button>
          </div>
        </div>

        {/* Accents List */}
        <div 
          id="accents-list"
          ref={(el) => (sectionRefs.current['accents-list'] = el)}
          className={`transition-all duration-700 ${
            visibleSections.has('accents-list') 
              ? 'opacity-100 translate-y-0' 
              : 'opacity-0 translate-y-8'
          }`}
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Your Accents</h2>
          
          {profiles.length === 0 ? (
            <div className={`bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-8 border ${currentColorScheme.border} text-center`}>
              <p className="text-gray-600 text-lg">No accents started yet. Start practicing to see your progress here!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {profiles.map((profile, index) => {
                const isExpanded = expandedAccents.has(profile.profileId);
                const languageName = typeof profile.language === 'object' ? profile.language.name : profile.language;
                const accentName = typeof profile.accent === 'object' ? profile.accent.name : profile.accent;
                
                // Format last practiced date
                const lastPracticedDate = new Date(profile.lastPracticed);
                const daysAgo = Math.floor((Date.now() - lastPracticedDate.getTime()) / (1000 * 60 * 60 * 24));
                const lastPracticedText = daysAgo === 0 
                  ? 'Today' 
                  : daysAgo === 1 
                  ? 'Yesterday' 
                  : `${daysAgo} days ago`;

                return (
                  <div
                    key={profile.profileId}
                    id={`accent-${profile.profileId}`}
                    ref={(el) => (sectionRefs.current[`accent-${profile.profileId}`] = el)}
                    className={`bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border ${currentColorScheme.border} overflow-hidden transition-all duration-300 ${
                      isExpanded ? 'shadow-xl' : 'hover:shadow-xl'
                    }`}
                  >
                    {/* Collapsed Header - Always Visible */}
                    <button
                      onClick={() => toggleAccent(profile.profileId)}
                      className={`w-full p-6 flex items-center justify-between transition-colors ${
                        profileSettings.colorScheme === 'pink' ? 'hover:bg-pink-50/50' :
                        profileSettings.colorScheme === 'purple' ? 'hover:bg-purple-50/50' :
                        profileSettings.colorScheme === 'blue' ? 'hover:bg-blue-50/50' :
                        'hover:bg-green-50/50'
                      }`}
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${currentColorScheme.primary} flex items-center justify-center text-white text-xl font-bold shadow-md`}>
                          {accentName.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 text-left">
                          <h3 className="text-xl font-bold text-gray-900">
                            {accentName} ({languageName})
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            Last practiced: {lastPracticedText}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className={`text-2xl font-bold bg-gradient-to-r ${currentColorScheme.accent} bg-clip-text text-transparent`}>
                            {profile.overallScore}%
                          </p>
                          <p className="text-xs text-gray-600">{profile.skillLevel.name}</p>
                        </div>
                        <svg
                          className={`w-6 h-6 transition-transform duration-300 ${
                            isExpanded ? 'rotate-180' : ''
                          }`}
                          style={{ color: `var(--${profileSettings.colorScheme}-600)` }}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </button>

                    {/* Expanded Content - Hidden by Default */}
                    {isExpanded && (
                      <div className="px-6 pb-6 pt-0 border-t border-pink-100 transition-all duration-300 ease-in-out">
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
                          <div className="text-center p-4 bg-gradient-to-br from-pink-50 to-rose-50 rounded-xl">
                            <p className="text-3xl font-bold bg-gradient-to-r from-pink-600 to-rose-600 bg-clip-text text-transparent">
                              {profile.overallScore}%
                            </p>
                            <p className="text-gray-600 mt-1 text-sm">Overall Score</p>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-br from-pink-50 to-rose-50 rounded-xl">
                            <p className="text-3xl font-bold bg-gradient-to-r from-pink-600 to-rose-600 bg-clip-text text-transparent">
                              {profile.totalSessions}
                            </p>
                            <p className="text-gray-600 mt-1 text-sm">Practice Sessions</p>
                          </div>
                          <div className="text-center p-4 bg-gradient-to-br from-pink-50 to-rose-50 rounded-xl">
                            <p className="text-3xl font-bold bg-gradient-to-r from-pink-600 to-rose-600 bg-clip-text text-transparent">
                              {profile.practiceTime}
                            </p>
                            <p className="text-gray-600 mt-1 text-sm">Minutes Practiced</p>
                          </div>
                        </div>

                        {/* Struggle Areas */}
                        {profile.struggleAreas && profile.struggleAreas.length > 0 && (
                          <div className="mb-6">
                            <h4 className="text-lg font-semibold text-gray-900 mb-3">Struggle Areas</h4>
                            <div className="flex flex-wrap gap-2">
                              {profile.struggleAreas.map((area, idx) => (
                                <span
                                  key={idx}
                                  className={`px-3 py-1 rounded-full text-sm font-medium border`}
                                  style={{ 
                                    background: `linear-gradient(to right, var(--${profileSettings.colorScheme}-100), var(--${profileSettings.colorScheme}-200))`,
                                    color: `var(--${profileSettings.colorScheme}-800)`,
                                    borderColor: `var(--${profileSettings.colorScheme}-200)`
                                  }}
                                >
                                  {area}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Skill Ratings */}
                        {profile.skills && profile.skills.length > 0 && (
                          <div>
                            <h4 className="text-lg font-semibold text-gray-900 mb-4">Skill Ratings</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {profile.skills.map((skill) => {
                                const level = getSkillLevel(skill.score);
                                const progress = getProgressPercentage(skill.score, level);
                                
                                return (
                                  <div
                                    key={skill.id}
                                    className={`border rounded-lg p-4 hover:shadow-md transition-all bg-gradient-to-br from-white`}
                                    style={{ 
                                      borderColor: `var(--${profileSettings.colorScheme}-200)`,
                                      background: `linear-gradient(to bottom right, white, var(--${profileSettings.colorScheme}-50))`
                                    }}
                                  >
                                    <div className="flex justify-between items-start mb-2">
                                      <div>
                                        <h5 className="font-semibold text-gray-900">{skill.name}</h5>
                                        <p className="text-sm text-gray-600">{skill.description}</p>
                                      </div>
                                      <span className={`px-2 py-1 rounded text-xs font-semibold bg-${level.color}-100 text-${level.color}-800`}>
                                        {level.name}
                                      </span>
                                    </div>
                                    <div className="mt-4">
                                      <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">Score</span>
                                        <span style={{ color: `var(--${profileSettings.colorScheme}-600)` }} className="font-semibold">{skill.score}%</span>
                                      </div>
                                      <div className={`w-full rounded-full h-2`} style={{ backgroundColor: `var(--${profileSettings.colorScheme}-100)` }}>
                                        <div
                                          className={`h-2 rounded-full transition-all`}
                                          style={{ 
                                            width: `${skill.score}%`,
                                            background: `linear-gradient(to right, var(--${profileSettings.colorScheme}-500), var(--${profileSettings.colorScheme}-600))`
                                          }}
                                        />
                                      </div>
                                      <p className="text-xs text-gray-500 mt-1">
                                        {progress.toFixed(0)}% to next level
                                      </p>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
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
    </div>
  );
};

export default Profile;

