/**
 * Language and Accent Data
 * Popular languages with their accents/dialects
 */

export const LANGUAGES = [
  {
    id: 'english',
    name: 'English',
    flag: '🇬🇧',
    popularity: 100,
    accents: [
      { id: 'american', name: 'American English', difficulty: 'beginner' },
      { id: 'british', name: 'British English', difficulty: 'intermediate' },
      { id: 'australian', name: 'Australian English', difficulty: 'intermediate' },
      { id: 'canadian', name: 'Canadian English', difficulty: 'beginner' },
      { id: 'irish', name: 'Irish English', difficulty: 'advanced' },
      { id: 'scottish', name: 'Scottish English', difficulty: 'advanced' },
    ],
  },
  {
    id: 'spanish',
    name: 'Spanish',
    flag: '🇪🇸',
    popularity: 95,
    accents: [
      { id: 'castilian', name: 'Castilian Spanish', difficulty: 'beginner' },
      { id: 'mexican', name: 'Mexican Spanish', difficulty: 'beginner' },
      { id: 'argentinian', name: 'Argentinian Spanish', difficulty: 'intermediate' },
      { id: 'colombian', name: 'Colombian Spanish', difficulty: 'intermediate' },
    ],
  },
  {
    id: 'french',
    name: 'French',
    flag: '🇫🇷',
    popularity: 90,
    accents: [
      { id: 'parisian', name: 'Parisian French', difficulty: 'beginner' },
      { id: 'quebecois', name: 'Québécois French', difficulty: 'intermediate' },
      { id: 'belgian', name: 'Belgian French', difficulty: 'intermediate' },
    ],
  },
  {
    id: 'german',
    name: 'German',
    flag: '🇩🇪',
    popularity: 85,
    accents: [
      { id: 'standard', name: 'Standard German', difficulty: 'beginner' },
      { id: 'austrian', name: 'Austrian German', difficulty: 'intermediate' },
      { id: 'swiss', name: 'Swiss German', difficulty: 'advanced' },
    ],
  },
  {
    id: 'italian',
    name: 'Italian',
    flag: '🇮🇹',
    popularity: 80,
    accents: [
      { id: 'tuscan', name: 'Tuscan Italian', difficulty: 'beginner' },
      { id: 'roman', name: 'Roman Italian', difficulty: 'intermediate' },
      { id: 'southern', name: 'Southern Italian', difficulty: 'intermediate' },
    ],
  },
  {
    id: 'portuguese',
    name: 'Portuguese',
    flag: '🇵🇹',
    popularity: 75,
    accents: [
      { id: 'european', name: 'European Portuguese', difficulty: 'beginner' },
      { id: 'brazilian', name: 'Brazilian Portuguese', difficulty: 'beginner' },
    ],
  },
  {
    id: 'mandarin',
    name: 'Mandarin Chinese',
    flag: '🇨🇳',
    popularity: 70,
    accents: [
      { id: 'beijing', name: 'Beijing Mandarin', difficulty: 'beginner' },
      { id: 'taiwanese', name: 'Taiwanese Mandarin', difficulty: 'intermediate' },
    ],
  },
  {
    id: 'japanese',
    name: 'Japanese',
    flag: '🇯🇵',
    popularity: 65,
    accents: [
      { id: 'tokyo', name: 'Tokyo Japanese', difficulty: 'beginner' },
      { id: 'osaka', name: 'Osaka Japanese', difficulty: 'intermediate' },
    ],
  },
];

export const getLanguageById = (id) => {
  return LANGUAGES.find(lang => lang.id === id);
};

export const getAccentById = (languageId, accentId) => {
  const language = getLanguageById(languageId);
  return language?.accents.find(accent => accent.id === accentId);
};

export const searchLanguages = (query) => {
  const lowerQuery = query.toLowerCase();
  return LANGUAGES.filter(lang => 
    lang.name.toLowerCase().includes(lowerQuery) ||
    lang.accents.some(accent => accent.name.toLowerCase().includes(lowerQuery))
  );
};

