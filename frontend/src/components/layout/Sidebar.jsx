// frontend/src/components/layout/Sidebar.jsx
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, FileText, FileCheck, User, Scale, Shield } from 'lucide-react';

export default function Sidebar() {
  
  const navItems = [
    { icon: <LayoutDashboard className="w-5 h-5" />, label: 'Dashboard', path: '/dashboard' },
    { icon: <MessageSquare className="w-5 h-5" />, label: 'Chat', path: '/chat' },
    { icon: <FileText className="w-5 h-5" />, label: 'Documents', path: '/documents' },
    { icon: <FileCheck className="w-5 h-5" />, label: 'Generate', path: '/generate' },
    { icon: <User className="w-5 h-5" />, label: 'Profile', path: '/profile' },
    { icon: <Shield className="w-5 h-5" />, label: 'Admin', path: '/admin' },
  ];

  return (
    <div className="h-screen w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <Scale className="w-8 h-8 text-primary-600 mr-2" />
        <span className="text-lg font-bold text-gray-900">Legal Assistant</span>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition ${
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-50'
              }`
            }
          >
            {item.icon}
            <span className="ml-3 font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      {/* Logout button removed */}
    </div>
  );
}