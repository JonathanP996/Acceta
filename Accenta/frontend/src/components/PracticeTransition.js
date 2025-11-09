import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { profileManager } from '../utils/profileManager';

const PracticeTransition = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, accent } = location.state || {};
  const [resolvedProfile, setResolvedProfile] = useState(profile || profileManager.getCurrentProfile());
  const [isRevving, setIsRevving] = useState(true);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (!profile && resolvedProfile) {
      profileManager.setCurrentProfile(resolvedProfile);
    }
  }, [profile, resolvedProfile]);

  useEffect(() => {
    if (!resolvedProfile) {
      navigate('/dashboard');
    }
  }, [resolvedProfile, navigate]);

  useEffect(() => {
    // Rev up for 5 seconds
    const revTimer = setTimeout(() => {
      setIsRevving(false);
      setIsAnimating(true);
    }, 5000); // 5 seconds of revving

    // Navigate to practice after rev-up (5s) + take-off animation (2s) = 7 seconds total
    const navigateTimer = setTimeout(() => {
      if (resolvedProfile) {
        navigate('/practice', {
          state: {
            profile: resolvedProfile,
            accent: accent || resolvedProfile.accent,
          },
        });
      }
    }, 7000); // 7 seconds total

    return () => {
      clearTimeout(revTimer);
      clearTimeout(navigateTimer);
    };
  }, [navigate, resolvedProfile, accent]);

  const accentName = resolvedProfile?.accent
    ? (typeof resolvedProfile.accent === 'object' ? resolvedProfile.accent.name : resolvedProfile.accent)
    : (accent ? (typeof accent === 'object' ? accent.name : accent) : 'English');

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

      <div className="relative z-20 w-full max-w-xl">
        <div className="relative w-full flex justify-center">
          <div
            className="absolute bottom-full mb-6 pointer-events-none h-24 w-full flex justify-center"
            role="img"
            aria-label="F1 racecar"
            style={{ fontSize: '168px', filter: 'drop-shadow(0 32px 80px rgba(0,0,0,0.32))' }}
          >
            🏎️
          </div>

          <div
            className="w-full bg-white/15 backdrop-blur-2xl border border-white/25 rounded-[28px] px-7 md:px-10 py-9 text-center text-white shadow-[0_48px_110px_rgba(9,17,48,0.45)]"
            style={{ boxShadow: '0 28px 70px rgba(6,22,55,0.45)' }}
          >
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Warming up your session…</h1>
            <p className="text-lg text-white/85 mb-10">
              We&rsquo;re getting everything ready for your {accentName} practice.
            </p>

            <div className="space-y-4 text-left max-w-xl mx-auto">
              <div className="flex items-start gap-3">
                <div className="text-2xl leading-none mt-0.5">⚙️</div>
                <div>
                  <p className="text-base font-semibold text-white">Loading personalized prompts</p>
                  <p className="text-sm text-white/80">We&rsquo;re selecting phrases that match your skill level.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl leading-none mt-0.5">🤖</div>
                <div>
                  <p className="text-base font-semibold text-white">Wally is tuning in</p>
                  <p className="text-sm text-white/80">Your chat buddy is preparing to listen and coach you.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl leading-none mt-0.5">📡</div>
                <div>
                  <p className="text-base font-semibold text-white">Optimizing feedback engine</p>
                  <p className="text-sm text-white/80">We&rsquo;ll provide phoneme-level insights in real time.</p>
                </div>
              </div>
            </div>

            <div className="mt-10 flex items-center justify-center gap-2">
              <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
              <div className="w-3 h-3 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
              <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PracticeTransition;

