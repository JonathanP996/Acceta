import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const PracticeTransition = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, accent, fromInitialTest, fromSurvey } = location.state || {};
  const [hasStarted, setHasStarted] = useState(false);
  const [isRevving, setIsRevving] = useState(true);
  const [isDriving, setIsDriving] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (!hasStarted) return;

    // After start, car drives in place for a few seconds
    const driveTimer = setTimeout(() => {
      setIsRevving(false);
      setIsDriving(true);
    }, 3000); // 3 seconds of revving after start

    // Then car flies off
    const flyTimer = setTimeout(() => {
      setIsDriving(false);
      setIsAnimating(true);
    }, 5000); // 2 more seconds of driving = 5 seconds total after start

    // Navigate to practice after driving (5s) + take-off animation (1.5s) = 6.5 seconds total after start
    const navigateTimer = setTimeout(() => {
      navigate('/practice', {
        state: {
          profile: profile,
          accent: accent,
          fromInitialTest: fromInitialTest,
          fromSurvey: fromSurvey,
        },
      });
    }, 6500); // 6.5 seconds total after start

    return () => {
      clearTimeout(driveTimer);
      clearTimeout(flyTimer);
      clearTimeout(navigateTimer);
    };
  }, [hasStarted, navigate, profile, accent, fromInitialTest, fromSurvey]);

  const accentName = profile?.accent 
    ? (typeof profile.accent === 'object' ? profile.accent.name : profile.accent)
    : (accent ? (typeof accent === 'object' ? accent.name : accent) : 'English');

  // Pre-transition explanation screen
  if (!hasStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-cyan-800 to-orange-800 relative overflow-hidden flex flex-col items-center justify-center px-6">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10 z-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
            backgroundSize: '40px 40px'
          }}></div>
        </div>

        <div className="relative z-20 max-w-2xl w-full text-center">
          {/* Racing Car Emoji - Revving */}
          <div className="mb-8 relative inline-block">
            <div 
              className="text-9xl md:text-[12rem] inline-block animate-rev relative"
              style={{ 
                filter: 'drop-shadow(0 10px 25px rgba(0,0,0,0.3))',
              }}
            >
              🏎️
            </div>
          </div>

          {/* Explanation Text */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl shadow-2xl p-8 md:p-12 border border-white/20 mb-8">
            <h2 className="text-4xl font-bold text-white mb-4">Get Ready to Practice!</h2>
            <p className="text-xl text-white/90 mb-6">
              You're about to start your first {accentName} practice session
            </p>
            <div className="space-y-4 text-left text-white/90">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🎯</span>
                <div>
                  <p className="font-semibold">10 Practice Questions</p>
                  <p className="text-sm text-white/70">Listen, repeat, and get instant feedback</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-2xl">📊</span>
                <div>
                  <p className="font-semibold">Track Your Progress</p>
                  <p className="text-sm text-white/70">See your pronunciation improve with each session</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-2xl">🎧</span>
                <div>
                  <p className="font-semibold">Best Experience</p>
                  <p className="text-sm text-white/70">Use headphones for clearer audio feedback</p>
                </div>
              </div>
            </div>
          </div>

          {/* Start Button */}
          <button
            onClick={() => setHasStarted(true)}
            className="px-8 py-4 bg-blue-600 text-white rounded-xl font-semibold text-lg hover:bg-blue-700 transition-all shadow-xl hover:shadow-2xl hover:scale-105"
          >
            Start Practice
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 via-cyan-50 to-orange-50 flex flex-col items-center justify-center px-6">
      {/* Animated F1 Racecar */}
      <div className="mb-12 relative w-full max-w-md h-64 overflow-visible flex items-center justify-center">
        <div 
          className={`relative transition-all duration-1500 ease-out ${
            isAnimating 
              ? 'translate-x-[200%] scale-100 opacity-0' 
              : 'translate-x-0 scale-100 opacity-100'
          } ${isRevving ? 'animate-rev' : ''} ${isDriving ? 'animate-drive' : ''}`}
          style={{ 
            transformOrigin: 'center center',
            willChange: 'transform, opacity'
          }}
        >
          {/* Racing Car Emoji */}
          <div 
            className="text-9xl md:text-[12rem] transition-all duration-200 relative inline-block"
            style={{ 
              filter: 'drop-shadow(0 10px 25px rgba(0,0,0,0.3))',
            }}
          >
            🏎️
          </div>
          
          {/* Speed lines overlay when driving or animating */}
          {(isDriving || isAnimating) && (
            <div className="absolute inset-0 pointer-events-none">
              <svg width="100%" height="100%" className="overflow-visible">
                <line x1="0" y1="50%" x2="100%" y2="50%" stroke="#F97316" strokeWidth="4" strokeDasharray="8,6" opacity="0.7">
                  <animate attributeName="x1" from="0%" to="100%" dur="0.3s" repeatCount="indefinite" />
                  <animate attributeName="x2" from="10%" to="110%" dur="0.3s" repeatCount="indefinite" />
                </line>
                <line x1="0" y1="60%" x2="100%" y2="60%" stroke="#F97316" strokeWidth="3" strokeDasharray="6,4" opacity="0.6">
                  <animate attributeName="x1" from="0%" to="100%" dur="0.25s" repeatCount="indefinite" />
                  <animate attributeName="x2" from="10%" to="110%" dur="0.25s" repeatCount="indefinite" />
                </line>
                <line x1="0" y1="40%" x2="100%" y2="40%" stroke="#F97316" strokeWidth="3" strokeDasharray="6,4" opacity="0.5">
                  <animate attributeName="x1" from="0%" to="100%" dur="0.28s" repeatCount="indefinite" />
                  <animate attributeName="x2" from="10%" to="110%" dur="0.28s" repeatCount="indefinite" />
                </line>
              </svg>
            </div>
          )}
        </div>
      </div>

      {/* Text Content */}
      <div className="text-center max-w-lg">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
          {isDriving ? 'Loading your practice session...' : isAnimating ? 'Ready to go!' : 'Preparing your first ' + accentName + ' lesson...'}
        </h1>
        <p className="text-lg text-gray-600">
          {isAnimating ? 'Starting now!' : 'Tip: Turn up the volume and put on headphones for the best experience...'}
        </p>
      </div>

      {/* Loading indicator */}
      <div className="mt-8 flex gap-2">
        <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
        <div className="w-3 h-3 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
      </div>
    </div>
  );
};

export default PracticeTransition;

