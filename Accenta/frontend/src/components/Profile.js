import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/api';
import { getSkillLevel, getProgressPercentage, ENGLISH_SKILLS } from '../data/skills';

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [timelineRecordings, setTimelineRecordings] = useState([]);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);

    // Mock profile data
    const mockProfile = {
      language: 'English',
      accent: 'American',
      overallScore: 75,
      skillLevel: getSkillLevel(75),
      totalSessions: 12,
      practiceTime: 180,
      struggleAreas: ['r', 'th', 'v'],
      skills: ENGLISH_SKILLS.map(skill => ({
        ...skill,
        score: Math.floor(Math.random() * 40) + 60, // 60-100
      })),
    };
    setSelectedProfile(mockProfile);

    // Mock timeline recordings
    setTimelineRecordings([
      {
        id: 1,
        phrase: "The quick brown fox",
        date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        score: 45,
        skillLevel: 'Beginner',
      },
      {
        id: 2,
        phrase: "The quick brown fox",
        date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
        score: 62,
        skillLevel: 'Intermediate',
      },
      {
        id: 3,
        phrase: "The quick brown fox",
        date: new Date(),
        score: 75,
        skillLevel: 'Adept',
      },
    ]);
  }, []);

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-700 hover:text-accenta-primary flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Dashboard
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
            <div className="w-20" /> {/* Spacer */}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* User Info */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Account Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Username</p>
              <p className="text-lg font-semibold">{user.username}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="text-lg font-semibold">{user.email}</p>
            </div>
          </div>
        </div>

        {selectedProfile && (
          <>
            {/* Profile Stats */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedProfile.accent} ({selectedProfile.language})
                </h2>
                <span className={`px-4 py-2 rounded-full font-semibold bg-${selectedProfile.skillLevel.color}-100 text-${selectedProfile.skillLevel.color}-800`}>
                  {selectedProfile.skillLevel.name}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-accenta-primary">{selectedProfile.overallScore}%</p>
                  <p className="text-gray-600">Overall Score</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-accenta-primary">{selectedProfile.totalSessions}</p>
                  <p className="text-gray-600">Practice Sessions</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-accenta-primary">{selectedProfile.practiceTime}</p>
                  <p className="text-gray-600">Minutes Practiced</p>
                </div>
              </div>

              {/* Struggle Areas */}
              {selectedProfile.struggleAreas.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Struggle Areas</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedProfile.struggleAreas.map((area, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium"
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Skill Ratings */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Skill Ratings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {selectedProfile.skills.map((skill) => {
                  const level = getSkillLevel(skill.score);
                  const progress = getProgressPercentage(skill.score, level);
                  
                  return (
                    <div key={skill.id} className="border border-gray-200 rounded-lg p-4 hover:border-accenta-primary transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900">{skill.name}</h3>
                          <p className="text-sm text-gray-600">{skill.description}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-semibold bg-${level.color}-100 text-${level.color}-800`}>
                          {level.name}
                        </span>
                      </div>
                      <div className="mt-4">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">Score</span>
                          <span className="font-semibold">{skill.score}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`bg-${level.color}-500 h-2 rounded-full transition-all`}
                            style={{ width: `${skill.score}%` }}
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

            {/* Timeline */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Progress Timeline</h2>
              <div className="space-y-6">
                {timelineRecordings.map((recording, index) => (
                  <div key={recording.id} className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-accenta-primary/10 rounded-full flex items-center justify-center">
                        <span className="text-accenta-primary font-bold">{index + 1}</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold text-gray-900">{recording.phrase}</p>
                          <p className="text-sm text-gray-600">
                            {recording.date.toLocaleDateString()}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-accenta-primary">{recording.score}%</p>
                          <p className="text-xs text-gray-600">{recording.skillLevel}</p>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-accenta-primary h-2 rounded-full"
                          style={{ width: `${recording.score}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default Profile;

