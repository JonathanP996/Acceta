import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/api';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div 
            className="text-2xl font-bold gradient-text cursor-pointer"
            onClick={() => navigate(authService.isAuthenticated() ? '/dashboard' : '/')}
          >
            accenta
          </div>
          
          <nav className="hidden md:flex items-center gap-6">
            <button
              onClick={() => navigate('/dashboard')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                location.pathname === '/dashboard' 
                  ? 'bg-purple-100 text-purple-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/practice-language-selection')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                location.pathname === '/practice-language-selection' 
                  ? 'bg-purple-100 text-purple-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Practice
            </button>
            <button
              onClick={() => navigate('/live-chat')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                location.pathname === '/live-chat' 
                  ? 'bg-purple-100 text-purple-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Live Chat
            </button>
            <button
              onClick={() => navigate('/profile')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                location.pathname === '/profile' 
                  ? 'bg-purple-100 text-purple-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Profile
            </button>
          </nav>

          <div className="flex items-center gap-4">
            {user && (
              <span className="text-gray-600 hidden sm:inline">
                {user.username || user.email}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

