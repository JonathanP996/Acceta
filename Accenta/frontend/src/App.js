import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { authService } from './services/api';

// Auth Components
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';

// Main Components
import LanguageSelection from './components/LanguageSelection';
import AccentSelection from './components/AccentSelection';
import InitialTest from './components/InitialTest';
import Dashboard from './components/Dashboard';
import Profile from './components/Profile';
import Practice from './components/Practice';
import CuratedPractice from './components/CuratedPractice';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected Routes */}
        <Route
          path="/language-selection"
          element={
            <ProtectedRoute>
              <LanguageSelection />
            </ProtectedRoute>
          }
        />
        <Route
          path="/accent-selection/:languageId"
          element={
            <ProtectedRoute>
              <AccentSelection />
            </ProtectedRoute>
          }
        />
        <Route
          path="/initial-test"
          element={
            <ProtectedRoute>
              <InitialTest />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/practice"
          element={
            <ProtectedRoute>
              <Practice />
            </ProtectedRoute>
          }
        />
        <Route
          path="/curated-practice"
          element={
            <ProtectedRoute>
              <CuratedPractice />
            </ProtectedRoute>
          }
        />

        {/* Default Route */}
        <Route
          path="/"
          element={
            authService.isAuthenticated() ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
