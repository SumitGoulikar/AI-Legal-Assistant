// frontend/src/pages/Dashboard.jsx
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { MessageSquare, FileText, FileCheck, TrendingUp } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();

  const stats = [
    {
      icon: <MessageSquare className="w-8 h-8" />,
      label: 'Chat Sessions',
      value: '0',
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      icon: <FileText className="w-8 h-8" />,
      label: 'Documents Uploaded',
      value: '0',
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      icon: <FileCheck className="w-8 h-8" />,
      label: 'Documents Generated',
      value: '0',
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      label: 'Total Queries',
      value: '0',
      color: 'text-orange-600',
      bg: 'bg-orange-50',
    },
  ];

  const quickActions = [
    {
      title: 'Ask a Legal Question',
      description: 'Get AI-powered answers to legal questions',
      link: '/chat',
      icon: '💬',
    },
    {
      title: 'Analyze Document',
      description: 'Analyze legal documents',
      link: '/analyze',
      icon: '📄',
    },
    {
      title: 'Generate Document',
      description: 'Create legal documents from templates',
      link: '/generate',
      icon: '✍️',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name || 'User'}! 👋
        </h1>
        <p className="text-gray-600 mt-2">
          Here's what's happening with your legal assistant today.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          ⚠️ <strong>Reminder:</strong> This AI assistant provides general information only, 
          not legal advice. Always consult a qualified advocate for legal matters.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {stat.value}
                  </p>
                </div>
                <div className={`${stat.bg} ${stat.color} p-3 rounded-lg`}>
                  {stat.icon}
                </div>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => (
            <Card
              key={index}
              className="hover:shadow-md transition cursor-pointer"
              onClick={() => window.location.href = action.link}
            >
              <CardBody>
                <div className="text-4xl mb-3">{action.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {action.title}
                </h3>
                <p className="text-sm text-gray-600">
                  {action.description}
                </p>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <h2 className="text-xl font-bold text-gray-900">Recent Activity</h2>
        </CardHeader>
        <CardBody>
          <div className="text-center py-12 text-gray-500">
            <p>No recent activity yet.</p>
            <p className="text-sm mt-2">Start by asking a question or uploading a document!</p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}