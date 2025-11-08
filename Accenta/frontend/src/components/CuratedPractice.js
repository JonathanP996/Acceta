import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Practice from './Practice';

const CuratedPractice = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, struggleAreas } = location.state || {};

  // Generate curated phrases based on struggle areas
  const generateCuratedPhrases = (areas) => {
    const phraseMap = {
      'r': [
        "Red roses are really rare",
        "Round the rugged rock",
        "The rabbit ran rapidly",
        "Rory's roller skates",
        "Rare red roses",
      ],
      'th': [
        "Think about this thoroughly",
        "The thirty-three thieves",
        "Three thick thistles",
        "Through thick and thin",
        "Thank you for thinking",
      ],
      'v': [
        "Very valuable vases",
        "Violet velvet vest",
        "Vivian loves vegetables",
        "Vast valleys and views",
        "Victor's violin",
      ],
      'l': [
        "Lily likes lovely lilies",
        "Little Larry laughed",
        "Loyal lions lie",
        "Lazy lizards lounging",
        "Loud laughter",
      ],
    };

    const curatedPhrases = [];
    areas.forEach(area => {
      if (phraseMap[area.toLowerCase()]) {
        curatedPhrases.push(...phraseMap[area.toLowerCase()]);
      }
    });

    return curatedPhrases.length > 0 ? curatedPhrases : Practice.PRACTICE_PHRASES;
  };

  const [curatedPhrases] = useState(
    generateCuratedPhrases(struggleAreas || profile?.struggleAreas || [])
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

