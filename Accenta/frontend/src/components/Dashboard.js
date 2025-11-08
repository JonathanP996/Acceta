import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/api';
import { getSkillLevel } from '../data/skills';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [profiles, setProfiles] = useState([]);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);

    // Load user profiles (mock data for now)
    // In production, fetch from backend
    const mockProfiles = [
      {
        language: 'English',
        accent: 'American',
        overallScore: 75,
        skillLevel: getSkillLevel(75),
        totalSessions: 12,
        practiceTime: 180, // minutes
      },
    ];
    setProfiles(mockProfiles);
  }, []);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleStartNew = () => {
    navigate('/language-selection');
  };

  const handleContinueLearning = (profile) => {
    navigate('/practice', { state: { profile } });
  };

  const handleViewProfile = () => {
    navigate('/profile');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Accenta</h1>
            <div className="flex items-center gap-4">
              <button
                onClick={handleViewProfile}
                className="text-gray-700 hover:text-accenta-primary"
              >
                Profile
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-700 hover:text-accenta-primary"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {user?.username || 'User'}!
          </h2>
          <p className="text-gray-600">Continue your accent learning journey</p>
        </div>

        {/* Test Complete Message */}
        {location.state?.testComplete && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800">
              ✓ Initial assessment complete! Your {location.state.accent.name} accent score: {location.state.initialScore?.toFixed(1)}%
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <button
            onClick={handleStartNew}
            className="bg-gradient-to-r from-accenta-primary to-accenta-secondary text-white rounded-xl p-6 hover:shadow-lg transition-all"
          >
            <div className="text-left">
              <h3 className="text-xl font-bold mb-2">Start Learning</h3>
              <p className="text-white/80">Choose a new language and accent</p>
            </div>
          </button>

          <button
            onClick={handleViewProfile}
            className="bg-white border-2 border-gray-200 rounded-xl p-6 hover:border-accenta-primary transition-all"
          >
            <div className="text-left">
              <h3 className="text-xl font-bold mb-2">View Profile</h3>
              <p className="text-gray-600">See your progress and statistics</p>
            </div>
          </button>
        </div>

        {/* Active Profiles */}
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Your Accents</h3>
          {profiles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {profiles.map((profile, index) => (
                <div
                  key={index}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="text-xl font-bold text-gray-900">{profile.accent}</h4>
                      <p className="text-gray-600">{profile.language}</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold bg-${profile.skillLevel.color}-100 text-${profile.skillLevel.color}-800`}
                    >
                      {profile.skillLevel.name}
                    </span>
                  </div>

                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Overall Score</span>
                      <span className="font-semibold">{profile.overallScore}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-accenta-primary h-2 rounded-full"
                        style={{ width: `${profile.overallScore}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <p className="text-gray-600">Sessions</p>
                      <p className="font-semibold">{profile.totalSessions}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Practice Time</p>
                      <p className="font-semibold">{profile.practiceTime} min</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <button
                      onClick={() => handleContinueLearning(profile)}
                      className="w-full bg-accenta-primary text-white rounded-lg py-2 hover:bg-accenta-secondary transition-colors"
                    >
                      Continue Learning
                    </button>
                    {profile.struggleAreas && profile.struggleAreas.length > 0 && (
                      <button
                        onClick={() => navigate('/curated-practice', { state: { profile, struggleAreas: profile.struggleAreas } })}
                        className="w-full bg-blue-500 text-white rounded-lg py-2 hover:bg-blue-600 transition-colors text-sm"
                      >
                        🎯 Curated Practice
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center">
              <p className="text-gray-600 mb-4">You haven't started learning any accents yet.</p>
              <button
                onClick={handleStartNew}
                className="bg-accenta-primary text-white px-6 py-3 rounded-lg hover:bg-accenta-secondary"
              >
                Get Started
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

