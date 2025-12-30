// src/pages/Profile.jsx
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { User, Shield, Key } from 'lucide-react';

export default function Profile() {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>

      {/* User Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-50 rounded-full text-primary-600">
              <User size={24} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Personal Information</h2>
              <p className="text-sm text-gray-500">Manage your account details</p>
            </div>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 text-gray-900">
                {user?.full_name}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email Address</label>
              <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 text-gray-900">
                {user?.email}
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Account Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-50 rounded-full text-green-600">
              <Shield size={24} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Account Status</h2>
              <p className="text-sm text-gray-500">Your subscription and role</p>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Plan: Free Tier</p>
              <p className="text-sm text-gray-500">You have access to basic features.</p>
            </div>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              Active
            </span>
          </div>
        </CardBody>
      </Card>

      {/* Actions */}
      <div className="flex justify-end space-x-4">
        <Button variant="outline" onClick={logout} className="text-red-600 border-red-200 hover:bg-red-50">
          Sign Out
        </Button>
      </div>
    </div>
  );
}