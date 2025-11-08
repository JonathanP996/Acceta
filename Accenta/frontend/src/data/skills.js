/**
 * Skill Definitions for Accents
 */

export const SKILL_LEVELS = {
  BEGINNER: { name: 'Beginner', color: 'red', min: 0, max: 20 },
  INTERMEDIATE: { name: 'Intermediate', color: 'orange', min: 21, max: 40 },
  ADEPT: { name: 'Adept', color: 'yellow', min: 41, max: 60 },
  PRO: { name: 'Pro', color: 'green', min: 61, max: 80 },
  MASTER: { name: 'Master', color: 'blue', min: 81, max: 100 },
};

export const getSkillLevel = (score) => {
  if (score >= 81) return SKILL_LEVELS.MASTER;
  if (score >= 61) return SKILL_LEVELS.PRO;
  if (score >= 41) return SKILL_LEVELS.ADEPT;
  if (score >= 21) return SKILL_LEVELS.INTERMEDIATE;
  return SKILL_LEVELS.BEGINNER;
};

export const getProgressPercentage = (score, level) => {
  const currentLevel = getSkillLevel(score);
  const nextLevel = Object.values(SKILL_LEVELS).find(
    l => l.min > currentLevel.max
  ) || SKILL_LEVELS.MASTER;
  
  const range = nextLevel.max - currentLevel.max;
  const progress = score - currentLevel.max;
  return Math.min(100, Math.max(0, (progress / range) * 100));
};

// Skill definitions for different accents
export const ENGLISH_SKILLS = [
  {
    id: 'pronunciation',
    name: 'Pronunciation',
    description: 'Accuracy of individual sounds and phonemes',
    practiceTracks: ['phoneme-practice', 'minimal-pairs'],
  },
  {
    id: 'reduction',
    name: 'Reduction',
    description: 'Natural reduction of unstressed syllables',
    practiceTracks: ['reduction-practice', 'connected-speech'],
  },
  {
    id: 'rhythm',
    name: 'Rhythm',
    description: 'Stress patterns and sentence rhythm',
    practiceTracks: ['stress-patterns', 'intonation'],
  },
  {
    id: 'articulation',
    name: 'Articulation',
    description: 'Clarity and precision of speech',
    practiceTracks: ['articulation-drills', 'tongue-placement'],
  },
];

export const getSkillsForAccent = (languageId, accentId) => {
  // For now, return English skills for all accents
  // Can be extended for other languages
  return ENGLISH_SKILLS;
};

