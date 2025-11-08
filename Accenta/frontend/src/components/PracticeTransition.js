import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const PracticeTransition = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, accent } = location.state || {};
  const [isRevving, setIsRevving] = useState(true);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    // Rev up for 5 seconds
    const revTimer = setTimeout(() => {
      setIsRevving(false);
      setIsAnimating(true);
    }, 5000); // 5 seconds of revving

    // Navigate to practice after rev-up (5s) + take-off animation (2s) = 7 seconds total
    const navigateTimer = setTimeout(() => {
      navigate('/practice', {
        state: {
          profile: profile,
          accent: accent,
        },
      });
    }, 7000); // 7 seconds total

    return () => {
      clearTimeout(revTimer);
      clearTimeout(navigateTimer);
    };
  }, [navigate, profile, accent]);

  const accentName = profile?.accent 
    ? (typeof profile.accent === 'object' ? profile.accent.name : profile.accent)
    : (accent ? (typeof accent === 'object' ? accent.name : accent) : 'English');

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 via-cyan-50 to-orange-50 flex flex-col items-center justify-center px-6">
      {/* Animated F1 Racecar */}
      <div className="mb-12 relative w-full max-w-md h-64 overflow-hidden">
        <div 
          className={`relative transition-all duration-2000 ease-in-out ${
            isAnimating 
              ? 'translate-x-[150%] -translate-y-20 scale-75 opacity-0' 
              : 'translate-x-0 translate-y-0 scale-100 opacity-100'
          } ${isRevving ? 'animate-rev' : ''}`}
          style={{ 
            transformOrigin: 'center center',
            willChange: 'transform, opacity'
          }}
        >
          {/* F1 Car Image */}
          <img
            src="/f1-car.png"
            alt="F1 Race Car"
            className="w-full h-auto max-w-xs mx-auto"
            style={{ 
              filter: 'drop-shadow(0 10px 25px rgba(0,0,0,0.3))',
              transform: isRevving ? 'scale(1.05)' : 'scale(1)',
              transition: 'transform 0.1s ease-in-out'
            }}
            onError={(e) => {
              // Fallback if image not found
              console.warn('F1 car image not found at /f1-car.png. Please add the image to the public folder.');
            }}
          />
          
          {/* Exhaust flames overlay when revving */}
          {isRevving && (
            <div className="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-8 pointer-events-none">
              <svg width="60" height="80" viewBox="0 0 60 80" className="overflow-visible">
                <ellipse cx="30" cy="30" rx="12" ry="20" fill="#F97316" opacity="0.9">
                  <animate attributeName="rx" values="12;18;12" dur="0.3s" repeatCount="indefinite" />
                  <animate attributeName="ry" values="20;28;20" dur="0.3s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;1;0.9" dur="0.3s" repeatCount="indefinite" />
                </ellipse>
                <ellipse cx="30" cy="40" rx="10" ry="18" fill="#FB923C" opacity="0.8">
                  <animate attributeName="rx" values="10;16;10" dur="0.25s" repeatCount="indefinite" />
                  <animate attributeName="ry" values="18;26;18" dur="0.25s" repeatCount="indefinite" />
                </ellipse>
                <ellipse cx="30" cy="50" rx="8" ry="14" fill="#FCD34D" opacity="0.7">
                  <animate attributeName="rx" values="8;14;8" dur="0.2s" repeatCount="indefinite" />
                  <animate attributeName="ry" values="14;20;14" dur="0.2s" repeatCount="indefinite" />
                </ellipse>
              </svg>
            </div>
          )}
          
          {/* Speed lines overlay when animating */}
          {isAnimating && (
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
          Preparing your first {accentName} lesson...
        </h1>
        <p className="text-lg text-gray-600">
          Tip: Turn up the volume and put on headphones for the best experience...
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

