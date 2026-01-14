// frontend/src/components/layout/Sidebar.jsx
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, MessageSquare, FileText, FileCheck, 
  User, LogOut, Scale, Shield, Sun, Moon 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';

export default function Sidebar() {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { icon: <LayoutDashboard className="w-5 h-5" />, label: 'Dashboard', path: '/dashboard' },
    { icon: <MessageSquare className="w-5 h-5" />, label: 'Chat', path: '/chat' },
    { icon: <FileText className="w-5 h-5" />, label: 'Analyze', path: '/analyze' },
    { icon: <FileCheck className="w-5 h-5" />, label: 'Generate', path: '/generate' },
    { icon: <User className="w-5 h-5" />, label: 'Profile', path: '/profile' },
    { icon: <Shield className="w-5 h-5" />, label: 'Admin', path: '/admin' },
  ];

  return (
    <div className="h-screen w-64 bg-white dark:bg-dark-card border-r border-gray-200 dark:border-dark-border flex flex-col transition-colors duration-300">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-dark-border">
        <Scale className="w-8 h-8 text-primary-600 mr-2" />
        <span className="text-lg font-bold text-gray-900 dark:text-white">Legal AI</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition ${
                isActive
                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`
            }
          >
            {item.icon}
            <span className="ml-3 font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 dark:border-dark-border space-y-2">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="flex items-center px-4 py-3 w-full rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
        >
          {theme === 'light' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          <span className="ml-3 font-medium">
            {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
          </span>
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          className="flex items-center px-4 py-3 w-full rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
        >
          <LogOut className="w-5 h-5" />
          <span className="ml-3 font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}