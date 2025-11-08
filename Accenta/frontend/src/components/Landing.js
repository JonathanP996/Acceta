import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/api';

const Landing = () => {
  const navigate = useNavigate();
  const isAuthenticated = authService.isAuthenticated();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-cyan-800 to-orange-800 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10 z-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>

      {/* Header */}
      <header className="relative z-20 px-6 py-6 bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div 
            className="text-white text-3xl font-bold cursor-pointer hover:text-orange-300 transition-colors"
            onClick={() => navigate('/')}
          >
            accenta
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-white/90 hover:text-white font-medium transition-colors">Features</a>
            <a href="#how-it-works" className="text-white/90 hover:text-white font-medium transition-colors">How It Works</a>
            <a href="#pricing" className="text-white/90 hover:text-white font-medium transition-colors">Pricing</a>
          </nav>
          <div className="flex items-center gap-4">
            {!isAuthenticated ? (
              <>
                <button
                  onClick={() => navigate('/login')}
                  className="text-white/90 hover:text-white font-medium transition-colors px-4 py-2"
                >
                  Sign In
                </button>
                <button
                  onClick={() => navigate('/signup')}
                  className="px-6 py-2 bg-white text-purple-900 rounded-lg font-semibold hover:bg-pink-100 transition-colors shadow-lg"
                >
                  Get Started
                </button>
              </>
            ) : (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg font-semibold"
              >
                Go to Dashboard
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-20 px-6 py-20 md:py-32 text-center">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight drop-shadow-lg">
            Master your accent with{' '}
            <span className="bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent">
              AI-powered
            </span>{' '}
            pronunciation coaching
          </h1>
          <p className="text-xl md:text-2xl text-white/90 mb-10 max-w-3xl mx-auto leading-relaxed">
            Get real-time feedback and personalized practice to perfect your accent in any language.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate(isAuthenticated ? '/dashboard' : '/signup')}
              className="px-8 py-4 bg-blue-600 text-white rounded-xl font-semibold text-lg hover:bg-blue-700 transition-all shadow-xl hover:shadow-2xl hover:scale-105"
            >
              Start Learning
            </button>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section id="features" className="relative z-20 px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-white text-center mb-12">
            Why Choose Accenta?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 hover:bg-white/15 transition-all shadow-xl hover:shadow-2xl">
              <div className="text-5xl mb-6">🎯</div>
              <h3 className="text-2xl font-bold text-white mb-4">Real-Time Analysis</h3>
              <p className="text-white/90 text-lg leading-relaxed">
                Get instant feedback on your pronunciation with advanced AI analysis that identifies specific areas for improvement.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 hover:bg-white/15 transition-all shadow-xl hover:shadow-2xl">
              <div className="text-5xl mb-6">📊</div>
              <h3 className="text-2xl font-bold text-white mb-4">Progress Tracking</h3>
              <p className="text-white/90 text-lg leading-relaxed">
                Track your improvement with detailed metrics and personalized insights that show your journey to accent mastery.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 hover:bg-white/15 transition-all shadow-xl hover:shadow-2xl">
              <div className="text-5xl mb-6">🌍</div>
              <h3 className="text-2xl font-bold text-white mb-4">Multiple Languages</h3>
              <p className="text-white/90 text-lg leading-relaxed">
                Practice accents for English, Spanish, French, and many more languages with native-like pronunciation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-20 px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 text-center border border-white/20 shadow-xl">
              <div className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent">10+</div>
              <p className="text-white/90 text-lg font-medium">Languages</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 text-center border border-white/20 shadow-xl">
              <div className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent">50+</div>
              <p className="text-white/90 text-lg font-medium">Accents</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 text-center border border-white/20 shadow-xl">
              <div className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent">95%</div>
              <p className="text-white/90 text-lg font-medium">Accuracy</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 text-center border border-white/20 shadow-xl">
              <div className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-orange-400 bg-clip-text text-transparent">24/7</div>
              <p className="text-white/90 text-lg font-medium">Available</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-20 px-6 py-12 border-t border-white/20 mt-20">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-white/70 text-lg">
            © 2024 Accenta. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;

