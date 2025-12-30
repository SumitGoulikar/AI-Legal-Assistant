// frontend/src/pages/Landing.jsx
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.jsx';
import { Scale, FileText, MessageSquare, FileCheck } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: 'Legal Q&A',
      description: 'Ask questions about Indian law and get AI-powered answers with source citations.',
    },
    {
      icon: <FileText className="w-8 h-8" />,
      title: 'Document Analysis',
      description: 'Upload legal documents for AI analysis, risk assessment, and clause extraction.',
    },
    {
      icon: <FileCheck className="w-8 h-8" />,
      title: 'Document Generation',
      description: 'Generate legal documents from templates - NDAs, agreements, notices, and more.',
    },
    {
      icon: <Scale className="w-8 h-8" />,
      title: 'Indian Law Focused',
      description: 'Specialized in Indian legal context with references to IPC, Contract Act, and more.',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Scale className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">AI Legal Assistant</span>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={() => navigate('/login')}>
                Login
              </Button>
              <Button onClick={() => navigate('/signup')}>
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Your AI-Powered Legal Assistant
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Get instant answers to legal questions, analyze documents, and generate legal paperwork
            with AI specialized in Indian law.
          </p>
          
          {/* Disclaimer */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8 max-w-3xl mx-auto">
            <p className="text-sm text-yellow-800">
              ⚠️ <strong>Disclaimer:</strong> This is an AI assistant for informational purposes only, 
              not legal advice. Always consult a qualified advocate registered with the Bar Council of India 
              for legal matters.
            </p>
          </div>

          <div className="flex justify-center space-x-4">
            <Button size="lg" onClick={() => navigate('/signup')}>
              Start Free Trial
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/login')}>
              Sign In
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Powerful Features
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition"
            >
              <div className="text-primary-600 mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600 text-sm">
            <p>© 2024 AI Legal Assistant. Built for educational purposes.</p>
            <p className="mt-2">
              This project focuses on Indian law and legal context.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}