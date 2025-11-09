import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LANGUAGES, searchLanguages } from '../data/languages';
import { authService, profileService } from '../services/api';

const LanguageSelection = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [hasProfile, setHasProfile] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user has a profile by checking email-specific localStorage
    const user = authService.getCurrentUser();
    if (user?.email) {
      const profiles = profileService.loadProfiles(user.email);
      setHasProfile(Array.isArray(profiles) && profiles.length > 0);
    } else {
      setHasProfile(false);
    }
  }, []);

  // Get progress for each language (email-specific)
  const getLanguageProgress = (languageId) => {
    const user = authService.getCurrentUser();
    if (!user?.email) return 0;
    
    const profiles = profileService.loadProfiles(user.email);
    if (!profiles.length) return 0;

    const matching = profiles.filter((profile) => {
      const profileLanguageId = profile.language?.id;
      return profileLanguageId === languageId;
    });

    if (!matching.length) return 0;

    const averageScore = matching.reduce((sum, profile) => sum + (profile.overallScore || 0), 0) / matching.length;
    return Math.round(averageScore);
  };

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
            {hasProfile ? (
              <button
                onClick={handleGoHome}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg font-semibold"
              >
                Dashboard
              </button>
            ) : (
              <button
                onClick={() => navigate('/login')}
                className="text-white/90 hover:text-white font-medium transition-colors px-4 py-2"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-20 px-6 py-12">
        <div className="max-w-7xl mx-auto">
          {/* Title */}
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 drop-shadow-lg">
              Select a language
            </h1>
          </div>

          {/* Search Bar */}
          <div className="mb-8 max-w-2xl mx-auto">
            <div className="relative">
              <input
                type="text"
                placeholder="Search languages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 pl-12 rounded-xl border-0 shadow-xl bg-white/95 backdrop-blur-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredLanguages.map((language) => {
              const progress = getLanguageProgress(language.id);
              return (
                <button
                  key={language.id}
                  onClick={() => handleLanguageSelect(language)}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 hover:scale-105 text-center group"
                >
                  <div className="text-6xl mb-4">{language.flag}</div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">{language.name}</h3>
                  {progress > 0 && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-500">Progress</span>
                        <span className="text-sm font-semibold text-gray-900">{progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-orange-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {filteredLanguages.length === 0 && (
            <div className="text-center py-12">
              <p className="text-white text-lg">No languages found matching "{searchQuery}"</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default LanguageSelection;

