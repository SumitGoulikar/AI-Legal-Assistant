// frontend/src/pages/Documents.jsx
import { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, Download, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import toast from 'react-hot-toast';

export default function Documents() {
  const navigate = useNavigate();
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
      console.error("Load Error:", error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    console.log("Uploading file:", file.name);

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    try {
      // Note: Don't set Content-Type manually, axios does it with boundary
      await api.post('/documents/upload', formData);
      toast.success('Document uploaded successfully');
      loadDocuments();
    } catch (error) {
      console.error("Upload Error:", error);
      const msg = error.response?.data?.detail || 'Upload failed';
      toast.error(msg);
    } finally {
      setUploading(false);
      e.target.value = null; // Reset input to allow re-uploading same file
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.delete(`/documents/${id}`);
      toast.success('Document deleted');
      setDocuments(docs => docs.filter(d => d.id !== id));
    } catch (error) {
      console.error("Delete Error:", error);
      toast.error('Failed to delete document');
    }
  };

  const handleDownload = (doc) => {
    // Construct absolute URL for download
    // VITE_API_URL is typically "http://localhost:8000/api/v1"
    const baseUrl = import.meta.env.VITE_API_URL;
    const downloadUrl = `${baseUrl}/documents/${doc.id}/download`;
    
    console.log("Download URL:", downloadUrl);
    window.open(downloadUrl, '_blank');
  };

  const handleChat = async (doc) => {
    if (doc.status !== 'ready') {
        toast.error('Document is still processing. Please wait.');
        return;
    }
    
    try {
        const response = await api.post('/chat/sessions', {
            session_type: 'document',
            document_id: doc.id,
            title: `Chat: ${doc.original_name}`
        });
        navigate(`/chat?session=${response.data.id}`);
    } catch (error) {
        console.error("Chat Start Error:", error);
        toast.error('Failed to start chat session');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
          <p className="text-gray-500 mt-1">Upload documents to analyze with AI.</p>
        </div>
        
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
              {uploading ? "Uploading..." : "Upload Document"}
            </Button>
          </label>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <Card className="p-12 text-center border-dashed border-2 bg-gray-50">
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
            <FileText size={32} className="text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900">No documents yet</h3>
          <p className="mt-1 text-gray-500 mb-6">Upload PDF, DOCX, or TXT files to analyze them.</p>
          <label htmlFor="file-upload">
            <Button variant="outline" as="span" className="cursor-pointer">
              Upload Now
            </Button>
          </label>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((doc) => (
            <Card key={doc.id} className="hover:shadow-md transition group">
              <div className="p-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="p-2 bg-primary-50 rounded-lg text-primary-600 flex-shrink-0">
                      <FileText size={24} />
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-medium text-gray-900 truncate" title={doc.original_name}>
                        {doc.original_name}
                      </h3>
                      <p className="text-xs text-gray-500 truncate">
                        {doc.file_size_formatted} • {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <span className={`flex-shrink-0 px-2 py-1 text-xs rounded-full font-medium ${
                    doc.status === 'ready' ? 'bg-green-100 text-green-700' :
                    doc.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {doc.status === 'ready' ? 'Analyzed' : doc.status}
                  </span>
                </div>
                
                <div className="flex space-x-2 pt-4 border-t border-gray-100">
                  <button 
                    onClick={() => handleChat(doc)}
                    className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition"
                  >
                    <MessageSquare size={14} className="mr-2" />
                    Chat
                  </button>
                  
                  <button 
                    onClick={() => handleDownload(doc)}
                    className="p-2 text-gray-500 hover:text-primary-600 hover:bg-gray-50 rounded-lg border border-gray-200"
                    title="Download"
                  >
                    <Download size={18} />
                  </button>
                  
                  <button 
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg border border-gray-200"
                    title="Delete"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}