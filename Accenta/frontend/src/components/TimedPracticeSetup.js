import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { profileManager } from '../utils/profileManager';

const DIFFICULTIES = [
  {
    id: 'easy',
    label: 'Easy',
    timeLimitSeconds: 30,
    description: '30 seconds per question',
    color: {
      border: 'border-emerald-300',
      bg: 'bg-emerald-50',
      text: 'text-emerald-700',
      chipBg: 'bg-emerald-200',
      chipText: 'text-emerald-800',
      hover: 'hover:border-emerald-400',
    },
  },
  {
    id: 'medium',
    label: 'Medium',
    timeLimitSeconds: 20,
    description: '20 seconds per question',
    color: {
      border: 'border-amber-300',
      bg: 'bg-amber-50',
      text: 'text-amber-700',
      chipBg: 'bg-amber-200',
      chipText: 'text-amber-800',
      hover: 'hover:border-amber-400',
    },
  },
  {
    id: 'hard',
    label: 'Hard',
    timeLimitSeconds: 15,
    description: '15 seconds per question',
    color: {
      border: 'border-orange-300',
      bg: 'bg-orange-50',
      text: 'text-orange-700',
      chipBg: 'bg-orange-200',
      chipText: 'text-orange-800',
      hover: 'hover:border-orange-400',
    },
  },
  {
    id: 'expert',
    label: 'Expert',
    timeLimitSeconds: 10,
    description: '10 seconds per question',
    color: {
      border: 'border-rose-300',
      bg: 'bg-rose-50',
      text: 'text-rose-700',
      chipBg: 'bg-rose-200',
      chipText: 'text-rose-800',
      hover: 'hover:border-rose-400',
    },
  },
];

const TimedPracticeSetup = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile: profileFromState } = location.state || {};

  const profile = useMemo(() => {
    if (profileFromState) return profileFromState;
    return profileManager.getCurrentProfile();
  }, [profileFromState]);

  if (!profile) {
    navigate('/dashboard', { replace: true });
    return null;
  }

  const handleSelectDifficulty = (difficulty) => {
    navigate('/practice', {
      state: {
        profile,
        timedMode: true,
        timedSettings: {
          difficultyId: difficulty.id,
          label: difficulty.label,
          timeLimitSeconds: difficulty.timeLimitSeconds,
          description: difficulty.description,
        },
      },
    });
  };

  return (
    <div className="min-h-screen bg-[#0D3082] bg-gradient-to-br from-[#0D3082] via-[#136A8A] to-[#C6423F] relative overflow-hidden flex items-center justify-center px-6 py-16">
      <div className="absolute inset-0 opacity-[0.08]">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.6) 1px, transparent 0)`,
            backgroundSize: '32px 32px',
          }}
        />
      </div>

      <div className="relative z-20 w-full max-w-5xl">
        <div className="bg-white rounded-[28px] px-8 md:px-14 py-12 text-gray-900 shadow-2xl">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-extrabold tracking-tight mb-3">Select Difficulty</h1>
            <p className="text-base text-gray-600">
              Choose your challenge level. Harder difficulties give you less time per question.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {DIFFICULTIES.map((difficulty) => (
              <button
                key={difficulty.id}
                onClick={() => handleSelectDifficulty(difficulty)}
                className={`rounded-3xl px-8 py-8 text-left transition-all duration-200 shadow-lg hover:shadow-xl focus:outline-none border ${difficulty.color.border} ${difficulty.color.hover} ${difficulty.color.bg}`}
              >
                <div className="flex flex-col items-start gap-3">
                  <p className={`text-2xl font-extrabold ${difficulty.color.text}`}>{difficulty.label}</p>
                  <p className="text-sm text-gray-600">{difficulty.description}</p>
                  <span className={`mt-2 inline-flex items-center justify-center px-4 py-2 rounded-full text-sm font-bold ${difficulty.color.chipBg} ${difficulty.color.chipText}`}>
                    {difficulty.timeLimitSeconds}s
                  </span>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-10 text-center">
            <button onClick={() => navigate('/dashboard')} className="text-gray-600 hover:text-gray-800 underline">
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimedPracticeSetup;

