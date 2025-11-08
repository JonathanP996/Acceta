import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Practice from './Practice';
import { getStruggleAreaPhrases, getPracticePhrases } from '../data/languagePrompts';

const CuratedPractice = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, struggleAreas } = location.state || {};

  // Generate curated phrases based on struggle areas and language
  const generateCuratedPhrases = (areas, languageId) => {
    const curatedPhrases = [];
    
    // Get language-specific phrases for each struggle area
    areas.forEach(area => {
      const phrases = getStruggleAreaPhrases(languageId || 'english', area);
      if (phrases && phrases.length > 0) {
        curatedPhrases.push(...phrases);
      }
    });

    // If no language-specific phrases found, fall back to default practice phrases
    return curatedPhrases.length > 0 ? curatedPhrases : getPracticePhrases(languageId || 'english');
  };

  // Get language ID from profile (could be stored as object with id, or just string name)
  let languageId = 'english'; // default fallback
  if (profile?.language) {
    if (typeof profile.language === 'object' && profile.language.id) {
      languageId = profile.language.id;
    } else if (typeof profile.language === 'string') {
      // Try to map language name to id
      const nameToId = {
        'english': 'english',
        'spanish': 'spanish',
        'french': 'french',
        'german': 'german',
        'italian': 'italian',
        'portuguese': 'portuguese',
        'mandarin': 'mandarin',
        'mandarin chinese': 'mandarin',
        'japanese': 'japanese',
      };
      languageId = nameToId[profile.language.toLowerCase()] || 'english';
    }
  }
  
  const [curatedPhrases] = useState(
    generateCuratedPhrases(struggleAreas || profile?.struggleAreas || [], languageId)
  );

  if (!profile) {
    navigate('/dashboard');
    return null;
  }

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          🎯 Curated Practice Track
        </h3>
        <p className="text-blue-700">
          This practice focuses on your struggle areas: {profile.struggleAreas?.join(', ') || 'general pronunciation'}
        </p>
      </div>
      <Practice 
        profile={profile}
        customPhrases={curatedPhrases}
        isCurated={true}
      />
    </div>
  );
};

export default CuratedPractice;

