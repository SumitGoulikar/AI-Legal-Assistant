// frontend/src/context/AuthContext.jsx
import { createContext, useContext } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  // Hardcoded Guest User
  const guestUser = {
    id: "guest-id",
    full_name: "Guest User",
    email: "guest@example.com",
    is_guest: true
  };

  const value = {
    user: guestUser,
    isAuthenticated: true,
    loading: false,
    // Dummy functions that do nothing
    login: async () => {},
    signup: async () => {},
    logout: () => {},
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};