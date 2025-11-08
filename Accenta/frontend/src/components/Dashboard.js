import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/api';
import { getSkillLevel, getSkillsForAccent, ENGLISH_SKILLS, getProgressPercentage, SKILL_LEVELS } from '../data/skills';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [currentProfile, setCurrentProfile] = useState(null);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);

    // Mark that user has visited dashboard (indicates they have a profile)
    localStorage.setItem('hasVisitedDashboard', 'true');

    // Check if we have a new test result from InitialTest
    if (location.state?.testComplete && location.state?.initialScore !== undefined) {
      const initialScore = Math.round(location.state.initialScore);
      const language = location.state.language?.name || location.state.language || 'Unknown';
      const accent = location.state.accent?.name || location.state.accent || 'Unknown';
      
      // Initialize skills with scores based on overall score (can be refined later)
      const skills = ENGLISH_SKILLS.map(skill => ({
        ...skill,
        score: Math.max(0, Math.min(100, initialScore + (Math.random() * 20 - 10))), // Slight variation around overall score
      }));
      
      const newProfile = {
        language: language,
        accent: accent,
        overallScore: initialScore,
        skillLevel: getSkillLevel(initialScore),
        totalSessions: 1,
        practiceTime: 0, // minutes
        struggleAreas: location.state.results?.map(r => r.struggleAreas || []).flat().filter((v, i, a) => a.indexOf(v) === i) || [],
        skills: skills,
      };
      
      // Update profiles list (in production, this would be saved to backend)
      setProfiles([newProfile]);
      setCurrentProfile(newProfile);
      
      // Store in localStorage for persistence
      localStorage.setItem('currentProfile', JSON.stringify(newProfile));
      return;
    }

    // Load user profiles (mock data for now)
    // In production, fetch from backend
    const storedProfile = localStorage.getItem('currentProfile');
    if (storedProfile) {
      try {
        const parsed = JSON.parse(storedProfile);
        // Ensure skills are initialized if missing (for older profiles)
        if (!parsed.skills || parsed.skills.length === 0) {
          parsed.skills = ENGLISH_SKILLS.map(skill => ({
            ...skill,
            score: Math.max(0, Math.min(100, (parsed.overallScore || 50) + (Math.random() * 20 - 10))),
          }));
        }
        setProfiles([parsed]);
        setCurrentProfile(parsed);
        return;
      } catch (e) {
        console.error('Failed to parse stored profile:', e);
      }
    }

    // Initialize skills with mock scores
    const mockSkills = ENGLISH_SKILLS.map(skill => ({
      ...skill,
      score: Math.floor(Math.random() * 30) + 60, // 60-90 range
    }));
    
    const mockProfiles = [
      {
        language: 'English',
        accent: 'American',
        overallScore: 75,
        skillLevel: getSkillLevel(75),
        totalSessions: 12,
        practiceTime: 180, // minutes
        struggleAreas: ['r', 'th', 'v'],
        skills: mockSkills,
      },
    ];
    setProfiles(mockProfiles);
    
    // Set the first profile as current (or most recent)
    if (mockProfiles.length > 0) {
      setCurrentProfile(mockProfiles[0]);
    }
  }, [location.state]);

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

  const handleSwitchAccent = (profile) => {
    setCurrentProfile(profile);
    localStorage.setItem('currentProfile', JSON.stringify(profile));
  };

  // Get practice tracks: each skill + curated practice
  const getPracticeTracks = () => {
    if (!currentProfile || !currentProfile.skills) {
      return [];
    }

    const skillTracks = currentProfile.skills.map(skill => {
      const skillLevel = getSkillLevel(skill.score);
      const skillIcons = {
        pronunciation: '🔊',
        reduction: '📉',
        rhythm: '🎵',
        articulation: '💬',
      };
      
      const skillColors = {
        pronunciation: 'from-blue-500 to-blue-600',
        reduction: 'from-purple-500 to-purple-600',
        rhythm: 'from-green-500 to-green-600',
        articulation: 'from-orange-500 to-orange-600',
      };
      
      return {
        id: skill.id,
        title: skill.name,
        description: skill.description,
        icon: skillIcons[skill.id] || '🎯',
        color: skillColors[skill.id] || 'from-gray-500 to-gray-600',
        score: skill.score,
        skillLevel: skillLevel,
        onClick: () => navigate('/practice', { state: { profile: currentProfile, skill: skill.id } }),
      };
    });

    // Add Curated Practice track
    const curatedTrack = {
      id: 'curated-practice',
      title: 'Curated Practice',
      description: 'Focus on your struggle areas with targeted exercises',
      icon: '📚',
      color: 'from-pink-500 to-pink-600',
      onClick: () => navigate('/curated-practice', { state: { profile: currentProfile, struggleAreas: currentProfile?.struggleAreas || [] } }),
      disabled: !currentProfile?.struggleAreas || currentProfile.struggleAreas.length === 0,
    };

    return [...skillTracks, curatedTrack];
  };

  const practiceTracks = getPracticeTracks();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Accenta</h1>
            <div className="flex items-center gap-4">
              <button
                onClick={handleStartNew}
                className="text-gray-700 hover:text-accenta-primary flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Learn New Language</span>
              </button>
              <button
                onClick={handleViewProfile}
                className="text-gray-700 hover:text-accenta-primary flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>Profile</span>
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-700 hover:text-accenta-primary px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hello Message */}
        {user && (
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-900">
              Hello, {user.username || 'there'}! 👋
            </h2>
            <p className="text-gray-600 mt-1">
              {(() => {
                const hour = new Date().getHours();
                if (hour < 12) return 'Good morning! Ready to practice your accent?';
                if (hour < 18) return 'Good afternoon! Let\'s continue improving your pronunciation.';
                return 'Good evening! Time for some accent practice.';
              })()}
            </p>
          </div>
        )}

        {/* Test Complete Message */}
        {location.state?.testComplete && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800">
              ✓ Initial assessment complete! Your {location.state.accent.name} accent score: {location.state.initialScore?.toFixed(1)}%
            </p>
          </div>
        )}

        {/* Current Accent Focus Section */}
        {currentProfile ? (
          <>
            {/* Current Accent Header */}
            <div className="bg-gradient-to-r from-accenta-primary to-accenta-secondary rounded-2xl shadow-xl p-8 mb-8 text-white">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
                <div>
                  <h2 className="text-4xl font-bold mb-2">{currentProfile.accent} Accent</h2>
                  <p className="text-white/90 text-lg">{currentProfile.language}</p>
                </div>
                <div className="mt-4 md:mt-0 text-right">
                  <div className="inline-block bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 mb-2">
                    <p className="text-sm text-white/80">Overall Score</p>
                    <p className="text-3xl font-bold">{currentProfile.overallScore}%</p>
                  </div>
                  <span className="inline-block px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm font-semibold">
                    {currentProfile.skillLevel.name}
                  </span>
                </div>
              </div>

              {/* Progress Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-white/80 text-sm mb-1">Sessions</p>
                  <p className="text-2xl font-bold">{currentProfile.totalSessions}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-white/80 text-sm mb-1">Practice Time</p>
                  <p className="text-2xl font-bold">{currentProfile.practiceTime} min</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-white/80 text-sm mb-1">Level</p>
                  <p className="text-2xl font-bold">{currentProfile.skillLevel.name}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-white/80 text-sm mb-1">Progress</p>
                  <div className="w-full bg-white/20 rounded-full h-2 mt-2">
                    <div
                      className="bg-white h-2 rounded-full transition-all"
                      style={{ width: `${currentProfile.overallScore}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Practice Tracks */}
            <div className="mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Practice Tracks</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {practiceTracks.map((track) => {
                  const isSkill = track.score !== undefined;
                  const isMaxRank = isSkill && track.skillLevel.name === SKILL_LEVELS.MASTER.name;
                  
                  // Calculate progress to next rank
                  let progressToNextRank = 0;
                  if (isSkill && !isMaxRank) {
                    const currentLevel = track.skillLevel;
                    // Find next level
                    const nextLevel = Object.values(SKILL_LEVELS).find(
                      l => l.min > currentLevel.max
                    );
                    
                    if (nextLevel) {
                      // Progress from start of current level to start of next level
                      const range = nextLevel.min - currentLevel.min;
                      const progress = track.score - currentLevel.min;
                      progressToNextRank = Math.min(100, Math.max(0, (progress / range) * 100));
                    }
                  }
                  
                  return (
                    <button
                      key={track.id}
                      onClick={track.disabled ? undefined : track.onClick}
                      disabled={track.disabled}
                      className={`bg-gradient-to-br ${track.color} rounded-xl p-6 text-white text-left hover:shadow-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 relative overflow-hidden`}
                    >
                      {/* Skill Ranking Badge */}
                      {isSkill && (
                        <div className="absolute top-4 right-4 bg-white/20 backdrop-blur-sm rounded-lg px-3 py-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-white/80">Rank</span>
                            <span className="text-lg font-bold">{track.skillLevel.name}</span>
                          </div>
                          <div className="text-xs text-white/90 mt-0.5">{track.score}%</div>
                        </div>
                      )}
                      
                      <div className="text-4xl mb-3">{track.icon}</div>
                      <h4 className="text-xl font-bold mb-2">{track.title}</h4>
                      <p className="text-white/90 text-sm mb-3">{track.description}</p>
                      
                      {/* Progress Bar for Skills */}
                      {isSkill && (
                        <div className="mt-4">
                          <div className="w-full bg-white/20 rounded-full h-2 mb-1">
                            <div
                              className="bg-white h-2 rounded-full transition-all"
                              style={{ width: isMaxRank ? '100%' : `${progressToNextRank}%` }}
                            />
                          </div>
                          {isMaxRank ? (
                            <p className="text-xs text-white/90 font-semibold">Max rank achieved</p>
                          ) : (
                            <p className="text-xs text-white/70">
                              {progressToNextRank.toFixed(0)}% to next rank
                            </p>
                          )}
                        </div>
                      )}
                      
                      {track.disabled && (
                        <p className="text-white/70 text-xs mt-2 italic">Complete initial assessment to unlock</p>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Live Chat Mode */}
            {currentProfile && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-6">Live Chat Mode</h3>
                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-xl p-8 text-white">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="text-5xl">💬</div>
                        <div>
                          <h4 className="text-2xl font-bold mb-2">Chat with Wally</h4>
                          <p className="text-white/90 text-lg">
                            Have a natural conversation with Wally, your friendly AI coach who speaks in {currentProfile.accent} accent
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 space-y-2 text-white/80">
                        <div className="flex items-start gap-2">
                          <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Natural conversation about your personal life</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Real-time pronunciation feedback</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span>Friendly and supportive AI companion</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <button
                        onClick={() => navigate('/live-chat', { state: { profile: currentProfile } })}
                        className="px-8 py-4 bg-white text-indigo-600 rounded-lg font-semibold text-lg hover:bg-white/90 transition-colors duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center gap-2"
                      >
                        <span>Start Chat</span>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Other Accents Section (if user has multiple) */}
            {profiles.length > 1 && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Switch to Another Accent</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {profiles.filter(p => p !== currentProfile).map((profile, index) => (
                    <button
                      key={index}
                      onClick={() => handleSwitchAccent(profile)}
                      className="bg-white rounded-xl shadow-lg p-4 hover:shadow-xl transition-all text-left border-2 border-transparent hover:border-accenta-primary"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="text-lg font-bold text-gray-900">{profile.accent}</h4>
                          <p className="text-sm text-gray-600">{profile.language}</p>
                        </div>
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold">
                          {profile.overallScore}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">Click to switch</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          /* No Profile State */
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="text-6xl mb-4">🎯</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Get Started with Accenta</h2>
              <p className="text-gray-600 mb-6">
                You haven't started learning any accents yet. Choose a language and accent to begin your journey!
              </p>
              <button
                onClick={handleStartNew}
                className="bg-gradient-to-r from-accenta-primary to-accenta-secondary text-white px-8 py-3 rounded-lg font-semibold hover:shadow-lg transition-all"
              >
                Start Learning
              </button>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default Dashboard;

