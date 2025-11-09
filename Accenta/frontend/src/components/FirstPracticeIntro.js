import React, { useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { profileManager } from '../utils/profileManager';

const FirstPracticeIntro = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile: profileFromState, accent: accentFromState, fromSurvey, fromInitialTest } =
    location.state || {};

  const resolvedProfile = useMemo(() => {
    if (profileFromState) {
      return profileFromState;
    }
    return profileManager.getCurrentProfile();
  }, [profileFromState]);

  useEffect(() => {
    if (!resolvedProfile) {
      navigate('/dashboard', { replace: true });
    } else {
      profileManager.setCurrentProfile(resolvedProfile);
    }
  }, [resolvedProfile, navigate]);

  if (!resolvedProfile) {
    return null;
  }

  const accentName =
    typeof (accentFromState || resolvedProfile.accent) === 'object'
      ? (accentFromState || resolvedProfile.accent).name
      : accentFromState || resolvedProfile.accent;

  const handleContinue = () => {
    navigate('/practice-transition', {
      state: {
        profile: resolvedProfile,
        accent: accentFromState || resolvedProfile.accent,
        fromSurvey: !!fromSurvey,
        fromInitialTest: !!fromInitialTest,
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

      <div className="relative z-20 w-full max-w-xl">
        <div className="relative w-full flex justify-center">
          <div
            className="absolute bottom-full mb-4 pointer-events-none text-[168px] drop-shadow-[0_32px_80px_rgba(0,0,0,0.32)]"
            role="img"
            aria-label="F1 racecar"
          >
            🏎️
          </div>

          <div
            className="w-full bg-white/15 backdrop-blur-2xl border border-white/25 rounded-[28px] px-7 md:px-10 py-9 text-center text-white shadow-[0_48px_110px_rgba(9,17,48,0.45)]"
            style={{
              boxShadow: '0 28px 70px rgba(6,22,55,0.45)',
            }}
          >
            <h1 className="text-4xl font-bold tracking-tight mb-4">Get Ready to Practice!</h1>
            <p className="text-lg text-white/85 mb-10">
              You&rsquo;re about to start your first {accentName} practice session.
            </p>

            <div className="space-y-5 text-left max-w-md mx-auto">
              <div className="flex items-start gap-4">
                <div className="text-3xl leading-none mt-0.5">🎯</div>
                <div>
                  <p className="text-base font-semibold text-white">10 Practice Questions</p>
                  <p className="text-sm text-white/75">Listen, repeat, and get instant feedback.</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="text-3xl leading-none mt-0.5">📊</div>
                <div>
                  <p className="text-base font-semibold text-white">Track Your Progress</p>
                  <p className="text-sm text-white/75">See your pronunciation improve with each session.</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="text-3xl leading-none mt-0.5">🎧</div>
                <div>
                  <p className="text-base font-semibold text-white">Best Experience</p>
                  <p className="text-sm text-white/75">Use headphones for clearer audio feedback.</p>
                </div>
              </div>
            </div>

            <div className="mt-12">
              <button
                onClick={handleContinue}
                className="inline-flex items-center justify-center px-10 py-3.5 rounded-2xl text-white font-semibold text-lg bg-gradient-to-r from-[#2A7CF7] to-[#1F64E8] shadow-[0_18px_40px_rgba(33,97,238,0.45)] hover:shadow-[0_20px_45px_rgba(33,97,238,0.55)] transition-all"
              >
                Start Practice
                <svg className="ml-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FirstPracticeIntro;

