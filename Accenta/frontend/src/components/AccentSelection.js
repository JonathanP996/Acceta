import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService, profileService } from '../services/api';

const AccentSelection = () => {
  const location = useLocation();
  const language = location.state?.language;
  const navigate = useNavigate();

  if (!language) {
    navigate('/language-selection');
    return null;
  }

  const handleAccentSelect = (accent) => {
    const user = authService.getCurrentUser();
    const email = user?.email;

    if (email) {
      const languageId = language?.id;
      const accentId = accent?.id || accent?.name;
      const existingProfile = profileService.findProfile(languageId, accentId, email);

      if (existingProfile) {
        profileService.setSelectedProfileId(existingProfile.profileId, email);
        navigate('/dashboard', {
          state: {
            selectedProfileId: existingProfile.profileId,
            accent: accent,
            language: language,
          },
        });
        return;
      }
    }

    navigate('/survey', {
      state: {
        language: language,
        accent: accent,
      },
    });
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      beginner: 'bg-green-100 text-green-800',
      intermediate: 'bg-yellow-100 text-yellow-800',
      advanced: 'bg-red-100 text-red-800',
    };
    return colors[difficulty] || colors.beginner;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-cyan-800 to-orange-800 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>

      {/* Header */}
      <header className="relative z-20 px-6 py-6 bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div 
            className="text-white text-3xl font-bold cursor-pointer hover:text-orange-300 transition-colors"
            onClick={() => navigate('/')}
          >
            accenta
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#languages" className="text-white/90 hover:text-white font-medium transition-colors">Languages</a>
          </nav>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/language-selection')}
              className="text-white/90 hover:text-white font-medium transition-colors px-4 py-2 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-20 px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="text-8xl mb-6">{language.flag}</div>
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 drop-shadow-lg">
              Choose Your Accent
            </h1>
            <p className="text-white/90 text-xl">Select an accent for {language.name}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {language.accents.map((accent) => (
              <button
                key={accent.id}
                onClick={() => handleAccentSelect(accent)}
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 hover:scale-105 text-left"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-bold text-gray-900">{accent.name}</h3>
                  <span
                    className={`text-xs px-3 py-1 rounded-full font-medium ${getDifficultyColor(
                      accent.difficulty
                    )}`}
                  >
                    {accent.difficulty}
                  </span>
                </div>
                <p className="text-gray-600">
                  Start learning {accent.name} pronunciation and rhythm patterns
                </p>
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default AccentSelection;

