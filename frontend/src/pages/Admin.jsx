// frontend/src/pages/Admin.jsx
import { useState, useEffect } from 'react';
import { Upload, Trash2, Database, Users, FileText, MessageSquare } from 'lucide-react';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import toast from 'react-hot-toast';

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [kbEntries, setKbEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  
  // Upload Form
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('acts');
  const [file, setFile] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, kbRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/knowledge-base')
      ]);
      setStats(statsRes.data);
      setKbEntries(kbRes.data.entries);
    } catch (error) {
      console.error(error);
      if (error.response?.status === 403) {
        toast.error("Access Denied: Admins Only");
      } else {
        toast.error("Failed to load admin data");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !title) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('category', category);
    formData.append('source', 'Admin Upload');

    try {
      await api.post('/admin/knowledge-base/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Added to Knowledge Base');
      setTitle('');
      setFile(null);
      loadData(); // Refresh list
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this knowledge base entry?")) return;
    try {
      await api.delete(`/admin/knowledge-base/${id}`);
      toast.success("Deleted");
      setKbEntries(prev => prev.filter(e => e.id !== id));
    } catch (error) {
      toast.error("Delete failed");
    }
  };

  if (loading) return <div className="p-8 text-center">Loading Admin Panel...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={<Users />} label="Users" value={stats?.total_users} color="text-blue-600" bg="bg-blue-50" />
        <StatCard icon={<FileText />} label="Documents" value={stats?.total_documents} color="text-green-600" bg="bg-green-50" />
        <StatCard icon={<MessageSquare />} label="Chats" value={stats?.total_chat_sessions} color="text-purple-600" bg="bg-purple-50" />
        <StatCard icon={<Database />} label="KB Items" value={stats?.total_knowledge_base_items} color="text-orange-600" bg="bg-orange-50" />
      </div>

      {/* Knowledge Base Manager */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Upload Form */}
        <Card className="h-fit">
          <CardHeader><h3 className="font-bold">Add to Knowledge Base</h3></CardHeader>
          <CardBody>
            <form onSubmit={handleUpload} className="space-y-4">
              <Input label="Title" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Indian Contract Act" required />
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select 
                  className="w-full border rounded-lg p-2"
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                >
                  <option value="acts">Act / Law</option>
                  <option value="judgments">Judgment</option>
                  <option value="rules">Rules / Regulation</option>
                  <option value="textbooks">Textbook</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">File (PDF/TXT)</label>
                <input 
                  type="file" 
                  accept=".pdf,.txt"
                  onChange={e => setFile(e.target.files[0])}
                  className="w-full text-sm"
                  required
                />
              </div>

              <Button type="submit" loading={uploading} className="w-full">Upload & Train AI</Button>
            </form>
          </CardBody>
        </Card>

        {/* KB List */}
        <Card className="lg:col-span-2">
          <CardHeader><h3 className="font-bold">Knowledge Base Entries</h3></CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                  <tr>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Chunks</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {kbEntries.map(entry => (
                    <tr key={entry.id} className="border-b">
                      <td className="px-4 py-3 font-medium">{entry.title}</td>
                      <td className="px-4 py-3">{entry.category}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          entry.status === 'ready' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {entry.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">{entry.chunk_count}</td>
                      <td className="px-4 py-3">
                        <button onClick={() => handleDelete(entry.id)} className="text-red-600 hover:text-red-800">
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {kbEntries.length === 0 && (
                    <tr>
                      <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                        Knowledge base is empty.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color, bg }) {
  return (
    <Card>
      <div className="p-4 flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${bg} ${color}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}