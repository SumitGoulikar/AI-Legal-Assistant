// frontend/src/pages/Analyze.jsx
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, AlertTriangle, List, MessageSquare, ArrowRight, Upload, X, Eye, Edit3 } from 'lucide-react';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import toast from 'react-hot-toast';

export default function Analyze() {
  const navigate = useNavigate();
  
  // State
  const [text, setText] = useState(''); // Extracted text for AI
  const [fileUrl, setFileUrl] = useState(null); // URL for PDF preview
  const [fileType, setFileType] = useState(null); // 'pdf' or 'text'
  const [viewMode, setViewMode] = useState('preview'); // 'preview' or 'edit'
  
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  
  const fileInputRef = useRef(null);

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (fileUrl) URL.revokeObjectURL(fileUrl);
    };
  }, [fileUrl]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast.error("File too large (Max 10MB)");
      return;
    }

    // 1. Create Preview URL
    const objectUrl = URL.createObjectURL(file);
    setFileUrl(objectUrl);
    const ext = file.name.split('.').pop().toLowerCase();
    setFileType(ext === 'pdf' || ext === 'docx' || ext === 'txt' ? ext : 'text');
    setViewMode(file.type === 'application/pdf' ? 'preview' : 'edit');

    // 2. Extract Text in Background
    setExtracting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/documents/extract_text', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      setText(response.data.full_text);
      toast.success("Document loaded for analysis");
    } catch (error) {
      console.error(error);
      toast.error("Could not extract text for AI analysis");
    } finally {
      setExtracting(false);
      e.target.value = null;
    }
  };

  const handleAnalyze = async (type) => {
    if (!text.trim()) {
      toast.error("Please upload a document first");
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await api.post('/documents/analyze_text', {
        text: text,
        analysis_type: type
      });
      setResult(response.data.result);
    } catch (error) {
      toast.error("Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = () => {
    navigate('/chat', { state: { context: text } });
  };

  const clearAll = () => {
    setText('');
    setResult('');
    if (fileUrl) URL.revokeObjectURL(fileUrl);
    setFileUrl(null);
    setFileType(null);
  };

  return (
    <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Document Analysis</h1>
          <p className="text-gray-600 dark:text-gray-400">View and analyze legal documents side-by-side.</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* LEFT COLUMN: DOCUMENT VIEWER */}
        <Card className="flex flex-col h-full overflow-hidden border-2 border-dashed border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900">
          
          {/* Header */}
          <div className="p-3 border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
              />
              <Button size="sm" onClick={() => fileInputRef.current?.click()} disabled={extracting}>
                <Upload size={14} className="mr-2" />
                {extracting ? "Processing..." : "Upload Document"}
              </Button>
              
              {fileUrl && fileType === 'pdf' && (
                <div className="flex bg-gray-100 dark:bg-slate-700 rounded-lg p-1 ml-2">
                  <button
                    onClick={() => setViewMode('preview')}
                    className={`p-1.5 rounded ${viewMode === 'preview' ? 'bg-white dark:bg-slate-600 shadow text-primary-600' : 'text-gray-500'}`}
                    title="View PDF"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => setViewMode('edit')}
                    className={`p-1.5 rounded ${viewMode === 'edit' ? 'bg-white dark:bg-slate-600 shadow text-primary-600' : 'text-gray-500'}`}
                    title="View Extracted Text"
                  >
                    <Edit3 size={16} />
                  </button>
                </div>
              )}
            </div>

            {text && (
              <Button size="sm" variant="ghost" onClick={clearAll} className="text-red-500 hover:text-red-700">
                <X size={16} />
              </Button>
            )}
          </div>
          
          {/* Viewer Area */}
          <div className="flex-1 relative bg-gray-100 dark:bg-slate-950">
            {!fileUrl && !text ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
                <FileText size={48} className="mb-4 opacity-20" />
                <p>Upload a PDF to view it here</p>
                <p className="text-sm mt-2 opacity-60">or paste text directly in Edit mode</p>
              </div>
            ) : viewMode === 'preview' && fileType === 'pdf' ? (
              <iframe
                src={`${fileUrl}#toolbar=0&navpanes=0`}
                className="w-full h-full border-none"
                title="Document Preview"
              />
            ) : (
              <textarea
                className="w-full h-full p-6 bg-white dark:bg-slate-900 resize-none focus:outline-none font-mono text-sm leading-relaxed"
                placeholder="Extracted text will appear here..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            )}
          </div>

          {/* Action Bar */}
          <div className="p-4 border-t border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex gap-3 flex-wrap">
            <Button onClick={() => handleAnalyze('summary')} disabled={loading || !text}>
              Summarize
            </Button>
            <Button variant="outline" onClick={() => handleAnalyze('risks')} disabled={loading || !text}>
              <AlertTriangle className="w-4 h-4 mr-2" /> Find Risks
            </Button>
            <Button variant="outline" onClick={() => handleAnalyze('clauses')} disabled={loading || !text}>
              <List className="w-4 h-4 mr-2" /> Key Clauses
            </Button>
          </div>
        </Card>

        {/* RIGHT COLUMN: AI ANALYSIS */}
        <Card className="flex flex-col h-full overflow-hidden bg-white dark:bg-slate-800 border-l-4 border-primary-500">
          <div className="p-4 border-b border-gray-200 dark:border-slate-700 flex justify-between items-center bg-gray-50 dark:bg-slate-800">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <MessageSquare size={18} /> AI Analysis
            </h2>
            {result && (
              <Button size="sm" onClick={handleChat}>
                Chat with Doc <ArrowRight size={14} className="ml-2" />
              </Button>
            )}
          </div>
          
          <div className="flex-1 p-6 overflow-y-auto">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500 animate-pulse">
                <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mb-4"></div>
                <p>Analyzing document...</p>
                <p className="text-xs mt-2">Reading clauses & checking risks</p>
              </div>
            ) : result ? (
              <div className="prose dark:prose-invert max-w-none text-sm">
                <div className="whitespace-pre-wrap">{result}</div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <MessageSquare className="w-16 h-16 mb-4 opacity-20" />
                <p className="text-center max-w-xs">
                  Analysis results will appear here.
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}