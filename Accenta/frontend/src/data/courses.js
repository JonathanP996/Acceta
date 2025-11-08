/**
 * Course and Lesson Data
 * Organized by skill level and language
 */

export const COURSES = {
  english: {
    BEGINNER: [
      {
        id: 'mobile-phones',
        title: 'Chapter 1: Mobile phones',
        progress: 0,
        lessons: [
          {
            id: 'phone-plan',
            title: 'Getting a phone plan',
            description: 'Learn vocabulary to talk about phone plans',
            icon: '📱',
            unlocked: true,
            completed: false,
          },
          {
            id: 'regional-differences',
            title: 'Noticing regional differences',
            description: 'Learn the difference between "a cell" and "a mobile"',
            icon: '🌍',
            unlocked: false,
            completed: false,
          },
          {
            id: 'phone-features',
            title: 'Talking about phone plans',
            description: 'Learn vocabulary to talk about plan features',
            icon: '💬',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'daily-routines',
        title: 'Chapter 2: Daily routines',
        progress: 0,
        lessons: [
          {
            id: 'morning-routine',
            title: 'Describing your morning',
            description: 'Learn phrases for daily activities',
            icon: '☀️',
            unlocked: false,
            completed: false,
          },
          {
            id: 'evening-routine',
            title: 'Evening activities',
            description: 'Practice talking about evening routines',
            icon: '🌙',
            unlocked: false,
            completed: false,
          },
        ],
      },
    ],
    INTERMEDIATE: [
      {
        id: 'business-communication',
        title: 'Chapter 1: Business communication',
        progress: 0,
        lessons: [
          {
            id: 'meetings',
            title: 'Participating in meetings',
            description: 'Learn professional meeting vocabulary',
            icon: '🤝',
            unlocked: true,
            completed: false,
          },
          {
            id: 'presentations',
            title: 'Giving presentations',
            description: 'Practice presentation skills and phrases',
            icon: '📊',
            unlocked: false,
            completed: false,
          },
          {
            id: 'email-communication',
            title: 'Professional email writing',
            description: 'Master formal email etiquette and structure',
            icon: '✉️',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'social-interactions',
        title: 'Chapter 2: Social interactions',
        progress: 0,
        lessons: [
          {
            id: 'networking',
            title: 'Networking and small talk',
            description: 'Practice conversation starters and follow-ups',
            icon: '👥',
            unlocked: false,
            completed: false,
          },
          {
            id: 'expressing-opinions',
            title: 'Expressing opinions',
            description: 'Learn to articulate your thoughts clearly',
            icon: '💬',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'travel-and-culture',
        title: 'Chapter 3: Travel and culture',
        progress: 0,
        lessons: [
          {
            id: 'airport-travel',
            title: 'Navigating airports',
            description: 'Essential phrases for air travel',
            icon: '✈️',
            unlocked: false,
            completed: false,
          },
          {
            id: 'cultural-nuances',
            title: 'Understanding cultural nuances',
            description: 'Learn context-appropriate expressions',
            icon: '🌐',
            unlocked: false,
            completed: false,
          },
        ],
      },
    ],
    ADEPT: [
      {
        id: 'advanced-conversations',
        title: 'Chapter 1: Advanced conversations',
        progress: 0,
        lessons: [
          {
            id: 'debates',
            title: 'Engaging in debates',
            description: 'Practice argumentation and discussion',
            icon: '💭',
            unlocked: true,
            completed: false,
          },
          {
            id: 'persuasive-speaking',
            title: 'Persuasive speaking',
            description: 'Master techniques for convincing others',
            icon: '🎤',
            unlocked: false,
            completed: false,
          },
          {
            id: 'handling-disagreements',
            title: 'Handling disagreements',
            description: 'Navigate conflicts diplomatically',
            icon: '⚖️',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'academic-english',
        title: 'Chapter 2: Academic English',
        progress: 0,
        lessons: [
          {
            id: 'academic-writing',
            title: 'Academic writing style',
            description: 'Learn formal academic language structures',
            icon: '📝',
            unlocked: false,
            completed: false,
          },
          {
            id: 'research-presentations',
            title: 'Research presentations',
            description: 'Present complex ideas clearly',
            icon: '🔬',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'media-literacy',
        title: 'Chapter 3: Media and current events',
        progress: 0,
        lessons: [
          {
            id: 'news-discussion',
            title: 'Discussing news and current events',
            description: 'Engage in informed conversations about media',
            icon: '📰',
            unlocked: false,
            completed: false,
          },
          {
            id: 'critical-analysis',
            title: 'Critical analysis of media',
            description: 'Express nuanced views on complex topics',
            icon: '🔍',
            unlocked: false,
            completed: false,
          },
        ],
      },
    ],
    PRO: [
      {
        id: 'professional-fluency',
        title: 'Chapter 1: Professional fluency',
        progress: 0,
        lessons: [
          {
            id: 'negotiations',
            title: 'Business negotiations',
            description: 'Master negotiation language',
            icon: '📈',
            unlocked: true,
            completed: false,
          },
          {
            id: 'executive-communication',
            title: 'Executive-level communication',
            description: 'Communicate with C-suite professionals',
            icon: '💼',
            unlocked: false,
            completed: false,
          },
          {
            id: 'strategic-planning',
            title: 'Strategic planning discussions',
            description: 'Participate in high-level strategy sessions',
            icon: '🎯',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'legal-and-formal',
        title: 'Chapter 2: Legal and formal contexts',
        progress: 0,
        lessons: [
          {
            id: 'legal-terminology',
            title: 'Legal terminology',
            description: 'Navigate legal documents and discussions',
            icon: '⚖️',
            unlocked: false,
            completed: false,
          },
          {
            id: 'contract-discussions',
            title: 'Contract discussions',
            description: 'Understand and discuss contractual terms',
            icon: '📋',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'technical-communication',
        title: 'Chapter 3: Technical communication',
        progress: 0,
        lessons: [
          {
            id: 'engineering-concepts',
            title: 'Engineering and technical concepts',
            description: 'Explain complex technical ideas',
            icon: '🔧',
            unlocked: false,
            completed: false,
          },
          {
            id: 'scientific-presentations',
            title: 'Scientific presentations',
            description: 'Present research findings professionally',
            icon: '🧪',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'literary-analysis',
        title: 'Chapter 4: Literary and cultural analysis',
        progress: 0,
        lessons: [
          {
            id: 'literature-discussion',
            title: 'Discussing literature',
            description: 'Analyze and critique literary works',
            icon: '📚',
            unlocked: false,
            completed: false,
          },
          {
            id: 'cultural-criticism',
            title: 'Cultural criticism',
            description: 'Engage in sophisticated cultural discourse',
            icon: '🎭',
            unlocked: false,
            completed: false,
          },
        ],
      },
    ],
    MASTER: [
      {
        id: 'native-level',
        title: 'Chapter 1: Native-level proficiency',
        progress: 0,
        lessons: [
          {
            id: 'idioms',
            title: 'Advanced idioms and expressions',
            description: 'Learn native-level expressions',
            icon: '🎯',
            unlocked: true,
            completed: false,
          },
          {
            id: 'slang-and-colloquialisms',
            title: 'Slang and colloquialisms',
            description: 'Master informal and regional expressions',
            icon: '🗣️',
            unlocked: false,
            completed: false,
          },
          {
            id: 'humor-and-sarcasm',
            title: 'Understanding humor and sarcasm',
            description: 'Navigate subtle linguistic nuances',
            icon: '😄',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'philosophy-and-abstraction',
        title: 'Chapter 2: Philosophy and abstract concepts',
        progress: 0,
        lessons: [
          {
            id: 'philosophical-discourse',
            title: 'Philosophical discourse',
            description: 'Engage in deep philosophical discussions',
            icon: '🧠',
            unlocked: false,
            completed: false,
          },
          {
            id: 'abstract-thinking',
            title: 'Expressing abstract ideas',
            description: 'Articulate complex theoretical concepts',
            icon: '💫',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'creative-writing',
        title: 'Chapter 3: Creative writing and storytelling',
        progress: 0,
        lessons: [
          {
            id: 'narrative-techniques',
            title: 'Narrative techniques',
            description: 'Master storytelling and narrative structure',
            icon: '✍️',
            unlocked: false,
            completed: false,
          },
          {
            id: 'poetic-language',
            title: 'Poetic and figurative language',
            description: 'Use metaphors, similes, and imagery',
            icon: '📖',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'public-speaking',
        title: 'Chapter 4: Advanced public speaking',
        progress: 0,
        lessons: [
          {
            id: 'keynote-speaking',
            title: 'Keynote speaking',
            description: 'Deliver compelling keynote addresses',
            icon: '🎤',
            unlocked: false,
            completed: false,
          },
          {
            id: 'impromptu-speaking',
            title: 'Impromptu speaking',
            description: 'Speak eloquently without preparation',
            icon: '⚡',
            unlocked: false,
            completed: false,
          },
        ],
      },
      {
        id: 'cross-cultural-expertise',
        title: 'Chapter 5: Cross-cultural expertise',
        progress: 0,
        lessons: [
          {
            id: 'cultural-mediation',
            title: 'Cultural mediation',
            description: 'Bridge cultural communication gaps',
            icon: '🌉',
            unlocked: false,
            completed: false,
          },
          {
            id: 'diplomatic-language',
            title: 'Diplomatic language',
            description: 'Navigate sensitive topics with tact',
            icon: '🕊️',
            unlocked: false,
            completed: false,
          },
        ],
      },
    ],
  },
};

export const getCoursesForLevel = (languageId, skillLevel) => {
  const languageCourses = COURSES[languageId] || COURSES.english;
  const levelKey = skillLevel?.name?.toUpperCase() || 'BEGINNER';
  return languageCourses[levelKey] || languageCourses.BEGINNER || [];
};

