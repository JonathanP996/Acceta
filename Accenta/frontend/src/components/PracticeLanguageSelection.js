import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { LANGUAGES, searchLanguages } from '../data/languages';
import Header from './Header';

const PracticeLanguageSelection = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const filteredLanguages = useMemo(() => {
    if (!searchQuery.trim()) {
      return LANGUAGES.sort((a, b) => b.popularity - a.popularity);
    }
    return searchLanguages(searchQuery);
  }, [searchQuery]);

  const handleLanguageSelect = (language) => {
    navigate(`/accent-selection/${language.id}`, { 
      state: { 
        language,
        fromPractice: true // Flag to indicate this is for practice, not initial setup
      } 
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose a Language to Practice
          </h1>
          <p className="text-lg text-gray-600">
            Select a language to start practicing your accent
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="max-w-md mx-auto">
            <div className="relative">
              <input
                type="text"
                placeholder="Search languages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 pl-12 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 transition-colors"
              />
              <svg
                className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Language Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredLanguages.map((language) => (
            <button
              key={language.id}
              onClick={() => handleLanguageSelect(language)}
              className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all transform hover:scale-105 border-2 border-gray-200 hover:border-purple-300 text-left"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="text-3xl">{language.flag}</div>
                <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  {language.popularity} learners
                </div>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">
                {language.name}
              </h3>
              <p className="text-sm text-gray-600">
                {language.nativeName}
              </p>
            </button>
          ))}
        </div>

        {filteredLanguages.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No languages found matching "{searchQuery}"</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default PracticeLanguageSelection;

