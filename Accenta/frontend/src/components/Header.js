import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/api';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser();
  const [profileSettings, setProfileSettings] = useState({
    nickname: '',
    colorScheme: 'pink',
    profilePic: null,
  });

  // Load profile settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('profileSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setProfileSettings(parsed);
      } catch (error) {
        console.error('Error loading profile settings:', error);
      }
    }
  }, []);

  // Get user display name (nickname or username)
  const getDisplayName = () => {
    if (profileSettings.nickname) return profileSettings.nickname;
    return user?.username || 'User';
  };

  // Get user initials for profile picture
  const getUserInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Color scheme configurations
  const colorSchemes = {
    pink: { primary: 'from-pink-400 via-rose-400 to-fuchsia-400' },
    purple: { primary: 'from-purple-400 via-indigo-400 to-pink-400' },
    blue: { primary: 'from-blue-400 via-cyan-400 to-teal-400' },
    green: { primary: 'from-green-400 via-emerald-400 to-teal-400' },
  };

  const currentColorScheme = colorSchemes[profileSettings.colorScheme] || colorSchemes.pink;

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
              className={`px-2 py-2 rounded-lg transition-colors flex items-center gap-2 ${
                location.pathname === '/profile' 
                  ? 'bg-purple-100 text-purple-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {profileSettings.profilePic ? (
                <img
                  src={profileSettings.profilePic}
                  alt="Profile"
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${currentColorScheme.primary} flex items-center justify-center text-white text-xs font-bold`}>
                  {getUserInitials(getDisplayName())}
                </div>
              )}
              <span className="hidden sm:inline">Profile</span>
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

