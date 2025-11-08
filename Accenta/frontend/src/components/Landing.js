import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/api';

const Landing = () => {
  const navigate = useNavigate();
  const isAuthenticated = authService.isAuthenticated();

  return (
    <div className="min-h-screen starry-bg">
      {/* Header */}
      <header className="relative z-10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div 
            className="text-white text-2xl font-bold cursor-pointer hover:text-pink-300 transition-colors"
            onClick={() => navigate('/')}
          >
            accenta
          </div>
          <nav className="hidden md:flex items-center gap-8 text-white">
            <a href="#features" className="hover:text-pink-300 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-pink-300 transition-colors">How It Works</a>
            <a href="#pricing" className="hover:text-pink-300 transition-colors">Pricing</a>
          </nav>
          <div className="flex items-center gap-4">
            {!isAuthenticated ? (
              <>
                <button
                  onClick={() => navigate('/login')}
                  className="text-white hover:text-pink-300 transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => navigate('/signup')}
                  className="px-4 py-2 border-2 border-white text-white rounded-lg hover:bg-white hover:text-purple-600 transition-colors"
                >
                  Get Started
                </button>
              </>
            ) : (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
              >
                Go to Dashboard
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Master your accent with AI-powered pronunciation coaching
          </h1>
          <p className="text-xl text-white/90 mb-8">
            Get real-time feedback and personalized practice to perfect your accent in any language.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate(isAuthenticated ? '/dashboard' : '/signup')}
              className="px-8 py-4 bg-pink-500 text-white rounded-lg font-semibold text-lg hover:bg-pink-600 transition-colors shadow-lg"
            >
              Start Learning
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="px-8 py-4 bg-transparent border-2 border-white text-white rounded-lg font-semibold text-lg hover:bg-white hover:text-purple-600 transition-colors"
            >
              Book a Demo
            </button>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="relative z-10 px-6 py-16">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="glass-card rounded-2xl p-6 text-white">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-bold mb-2">Real-Time Analysis</h3>
              <p className="text-white/80">
                Get instant feedback on your pronunciation with advanced AI analysis
              </p>
            </div>

            {/* Card 2 */}
            <div className="glass-card rounded-2xl p-6 text-white">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">Progress Tracking</h3>
              <p className="text-white/80">
                Track your improvement with detailed metrics and personalized insights
              </p>
            </div>

            {/* Card 3 */}
            <div className="glass-card rounded-2xl p-6 text-white">
              <div className="text-4xl mb-4">🌍</div>
              <h3 className="text-xl font-bold mb-2">Multiple Languages</h3>
              <p className="text-white/80">
                Practice accents for English, Spanish, French, and many more languages
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-10 px-6 py-16">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="glass-card rounded-2xl p-6 text-center text-white">
              <div className="text-3xl font-bold mb-2 gradient-text">10+</div>
              <p className="text-white/80">Languages</p>
            </div>
            <div className="glass-card rounded-2xl p-6 text-center text-white">
              <div className="text-3xl font-bold mb-2 gradient-text">50+</div>
              <p className="text-white/80">Accents</p>
            </div>
            <div className="glass-card rounded-2xl p-6 text-center text-white">
              <div className="text-3xl font-bold mb-2 gradient-text">95%</div>
              <p className="text-white/80">Accuracy</p>
            </div>
            <div className="glass-card rounded-2xl p-6 text-center text-white">
              <div className="text-3xl font-bold mb-2 gradient-text">24/7</div>
              <p className="text-white/80">Available</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Landing;

