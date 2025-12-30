// src/pages/Documents.jsx
import { useState, useEffect } from 'react';
import { Upload, FileText, Search, Trash2, Download } from 'lucide-react';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import toast from 'react-hot-toast';

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await api.get('/documents');
      setDocuments(response.data.documents);
    } catch (error) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    try {
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Document uploaded successfully');
      loadDocuments();
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.delete(`/documents/${id}`);
      toast.success('Document deleted');
      setDocuments(docs => docs.filter(d => d.id !== id));
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
        <div className="relative">
          <input
            type="file"
            id="file-upload"
            className="hidden"
            onChange={handleFileUpload}
            accept=".pdf,.docx,.txt"
            disabled={uploading}
          />
          <label htmlFor="file-upload">
            <Button as="span" loading={uploading} className="cursor-pointer">
              <Upload size={18} className="mr-2" />
              Upload Document
            </Button>
          </label>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : documents.length === 0 ? (
        <Card className="p-12 text-center text-gray-500">
          <FileText size={48} className="mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900">No documents yet</h3>
          <p className="mt-1">Upload PDF, DOCX, or TXT files to get started.</p>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((doc) => (
            <Card key={doc.id} className="hover:shadow-md transition">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary-50 rounded-lg text-primary-600">
                      <FileText size={24} />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 truncate max-w-[150px]" title={doc.original_name}>
                        {doc.original_name}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {doc.file_size_formatted} • {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    <button 
                      onClick={() => window.open(`${import.meta.env.VITE_API_URL}/documents/${doc.id}/download`, '_blank')}
                      className="p-1 text-gray-400 hover:text-primary-600 rounded"
                    >
                      <Download size={16} />
                    </button>
                    <button 
                      onClick={() => handleDelete(doc.id)}
                      className="p-1 text-gray-400 hover:text-red-600 rounded"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="mt-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    doc.status === 'ready' ? 'bg-green-100 text-green-800' :
                    doc.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}