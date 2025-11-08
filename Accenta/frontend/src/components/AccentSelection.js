import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const AccentSelection = () => {
  const location = useLocation();
  const language = location.state?.language;
  const navigate = useNavigate();

  if (!language) {
    navigate('/language-selection');
    return null;
  }

  const handleAccentSelect = (accent) => {
    navigate('/initial-test', {
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
    <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/language-selection')}
          className="mb-6 text-white hover:text-gray-200 flex items-center"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Languages
        </button>

        <div className="text-center mb-8">
          <div className="text-6xl mb-4">{language.flag}</div>
          <h1 className="text-4xl font-bold text-white mb-2">Choose Your Accent</h1>
          <p className="text-white/80">Select an accent for {language.name}</p>
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
    </div>
  );
};

export default AccentSelection;

