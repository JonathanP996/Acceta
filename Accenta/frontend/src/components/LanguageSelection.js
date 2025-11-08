import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LANGUAGES, searchLanguages } from '../data/languages';
import { authService } from '../services/api';

const LanguageSelection = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [hasProfile, setHasProfile] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user has a profile by checking:
    // 1. If they've completed initial test (stored in localStorage or state)
    // 2. If they have profile data in localStorage
    // 3. If they've visited dashboard before (indicates they have a profile)
    const user = authService.getCurrentUser();
    if (user) {
      // Check for profile indicators
      const hasCompletedTest = localStorage.getItem('hasCompletedInitialTest');
      const hasProfileData = localStorage.getItem('userProfile');
      const hasVisitedDashboard = localStorage.getItem('hasVisitedDashboard');
      
      // User has a profile if any of these are true
      setHasProfile(!!(hasCompletedTest || hasProfileData || hasVisitedDashboard));
    }
  }, []);

  const filteredLanguages = useMemo(() => {
    if (!searchQuery.trim()) {
      return LANGUAGES.sort((a, b) => b.popularity - a.popularity);
    }
    return searchLanguages(searchQuery);
  }, [searchQuery]);

  const handleLanguageSelect = (language) => {
    navigate(`/accent-selection/${language.id}`, { state: { language } });
  };

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header with Go Home button if user has profile */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            {hasProfile && (
              <button
                onClick={handleGoHome}
                className="flex items-center gap-2 text-white hover:text-white/90 transition-colors bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg backdrop-blur-sm"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                <span className="font-medium">Go to Home</span>
              </button>
            )}
            {!hasProfile && <div></div>} {/* Spacer when no button */}
            <div className="flex-1"></div>
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold text-white mb-2">Choose Your Language</h1>
            <p className="text-white/80">Select the language you want to learn</p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative">
            <input
              type="text"
              placeholder="Search languages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 pl-12 rounded-lg border-0 shadow-lg focus:ring-2 focus:ring-white"
            />
            <svg
              className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Language Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredLanguages.map((language) => (
            <button
              key={language.id}
              onClick={() => handleLanguageSelect(language)}
              className="bg-white rounded-xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 hover:scale-105 text-left"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-4xl">{language.flag}</span>
                <span className="text-sm text-gray-500">Popularity: {language.popularity}%</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{language.name}</h3>
              <p className="text-sm text-gray-600">
                {language.accents.length} accent{language.accents.length !== 1 ? 's' : ''} available
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {language.accents.slice(0, 3).map((accent) => (
                  <span
                    key={accent.id}
                    className="text-xs px-2 py-1 bg-accenta-primary/10 text-accenta-primary rounded-full"
                  >
                    {accent.name}
                  </span>
                ))}
                {language.accents.length > 3 && (
                  <span className="text-xs px-2 py-1 text-gray-500">
                    +{language.accents.length - 3} more
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>

        {filteredLanguages.length === 0 && (
          <div className="text-center py-12">
            <p className="text-white text-lg">No languages found matching "{searchQuery}"</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LanguageSelection;

