import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { LANGUAGES, searchLanguages } from '../data/languages';

const LanguageSelection = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const filteredLanguages = useMemo(() => {
    if (!searchQuery.trim()) {
      return LANGUAGES.sort((a, b) => b.popularity - a.popularity);
    }
    return searchLanguages(searchQuery);
  }, [searchQuery]);

  const handleLanguageSelect = (language) => {
    navigate(`/accent-selection/${language.id}`, { state: { language } });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-accenta-primary to-accenta-secondary py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Choose Your Language</h1>
          <p className="text-white/80">Select the language you want to learn</p>
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

