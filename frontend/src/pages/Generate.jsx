// frontend/src/pages/Generate.jsx
import { useState, useEffect } from 'react';
import { FilePlus, ChevronRight, Loader2, Download } from 'lucide-react';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import toast from 'react-hot-toast';

export default function Generate() {
  const [step, setStep] = useState(1);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await api.get('/generate/templates');
      setTemplates(response.data.templates);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load templates');
    }
  };

  const handleTemplateSelect = async (template) => {
    try {
      const response = await api.get(`/generate/templates/${template.id}`);
      setSelectedTemplate(response.data);
      setStep(2);
      setFormData({}); // Reset form
    } catch (error) {
      toast.error('Failed to load template details');
    }
  };

  const handleInputChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePreview = async () => {
    setLoading(true);
    try {
      const response = await api.post('/generate/preview', {
        template_id: selectedTemplate.id,
        title: 'Draft Document',
        form_data: formData
      });
      setPreview(response.data);
      setStep(3);
    } catch (error) {
      toast.error('Failed to generate preview');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await api.post('/generate/create', {
        template_id: selectedTemplate.id,
        title: `${selectedTemplate.name} - ${new Date().toLocaleDateString()}`,
        form_data: formData
      });
      toast.success('Document generated successfully!');
      
      // Store the relative URL from backend (e.g., "/generate/documents/123/download")
      setDownloadUrl(response.data.download_url);
      
    } catch (error) {
      console.error(error);
      toast.error('Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!downloadUrl) return;

    // Construct the full download URL
    // VITE_API_URL is typically "http://localhost:8000/api/v1"
    // downloadUrl from backend typically starts with "/api/v1/..." or just "/generate/..."
    
    // We need to clean this up to avoid double /api/v1
    const baseUrl = import.meta.env.VITE_API_URL; // e.g. http://localhost:8000/api/v1
    const rootUrl = baseUrl.replace('/api/v1', ''); // e.g. http://localhost:8000
    
    // If backend returns full path like "/api/v1/generate...", use rootUrl
    // If backend returns relative path like "/generate...", use baseUrl (if needed) or rootUrl + path
    
    // Safest bet: backend usually returns relative path from API root or App root.
    // Let's assume backend returns "/api/v1/generate/documents/..."
    const finalUrl = `${rootUrl}${downloadUrl}`;
    
    console.log("Downloading from:", finalUrl);
    window.open(finalUrl, '_blank');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Generate Legal Document</h1>

      {/* Progress Steps */}
      <div className="flex items-center space-x-4 text-sm text-gray-500 mb-8 overflow-x-auto">
        <span className={step >= 1 ? 'text-primary-600 font-bold whitespace-nowrap' : 'whitespace-nowrap'}>1. Select Template</span>
        <ChevronRight size={16} />
        <span className={step >= 2 ? 'text-primary-600 font-bold whitespace-nowrap' : 'whitespace-nowrap'}>2. Fill Details</span>
        <ChevronRight size={16} />
        <span className={step >= 3 ? 'text-primary-600 font-bold whitespace-nowrap' : 'whitespace-nowrap'}>3. Preview & Download</span>
      </div>

      {/* STEP 1: Select Template */}
      {step === 1 && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              {loading ? "Loading templates..." : "No templates available."}
            </div>
          ) : (
            templates.map(template => (
              <Card 
                key={template.id} 
                className="cursor-pointer hover:shadow-md hover:border-primary-300 transition group"
                onClick={() => handleTemplateSelect(template)}
              >
                <div className="p-6">
                  <div className="w-12 h-12 bg-primary-50 text-primary-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition">
                    <FilePlus size={24} />
                  </div>
                  <h3 className="font-bold text-gray-900 mb-2">{template.name}</h3>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{template.description}</p>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 uppercase font-medium">
                    {template.category}
                  </span>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* STEP 2: Fill Form */}
      {step === 2 && selectedTemplate && (
        <Card className="max-w-2xl mx-auto">
          <div className="p-6 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-bold">{selectedTemplate.name}</h2>
            <Button variant="ghost" size="sm" onClick={() => setStep(1)}>Change Template</Button>
          </div>
          <div className="p-6 space-y-6">
            {selectedTemplate.form_schema.fields.map(field => (
              <div key={field.name}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label} {field.required && <span className="text-red-500">*</span>}
                </label>
                
                {field.type === 'textarea' ? (
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none min-h-[100px]"
                    value={formData[field.name] || ''}
                    onChange={(e) => handleInputChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                  />
                ) : field.type === 'select' ? (
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none bg-white"
                    value={formData[field.name] || ''}
                    onChange={(e) => handleInputChange(field.name, e.target.value)}
                  >
                    <option value="">Select an option...</option>
                    {field.options?.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : (
                  <Input
                    type={field.type}
                    value={formData[field.name] || ''}
                    onChange={(e) => handleInputChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                  />
                )}
                
                {field.help_text && <p className="text-xs text-gray-500 mt-1">{field.help_text}</p>}
              </div>
            ))}
            <div className="pt-4">
              <Button onClick={handlePreview} loading={loading} className="w-full" size="lg">
                Generate Preview
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* STEP 3: Preview & Download */}
      {step === 3 && preview && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Preview Panel */}
          <Card className="h-[600px] flex flex-col">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h2 className="text-lg font-bold">Document Preview</h2>
            </div>
            <div className="flex-1 p-6 overflow-y-auto bg-white text-sm font-serif leading-relaxed whitespace-pre-wrap">
              {preview.preview_text}
            </div>
          </Card>
          
          {/* Action Panel */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="font-bold text-lg mb-2">Ready to Download?</h3>
              <p className="text-sm text-gray-600 mb-6">
                Please review the document carefully. Once you confirm, we will generate the final PDF for you to download.
              </p>
              
              {!downloadUrl ? (
                <div className="flex gap-4">
                  <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                    Edit Details
                  </Button>
                  <Button onClick={handleGenerate} loading={loading} className="flex-1">
                    Confirm & Generate
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-green-50 text-green-700 p-4 rounded-lg flex items-center gap-2">
                    <FilePlus size={20} />
                    <span className="font-medium">Document Ready!</span>
                  </div>
                  <Button 
                    className="w-full" 
                    size="lg"
                    onClick={handleDownload}
                  >
                    <Download size={20} className="mr-2" />
                    Download PDF
                  </Button>
                  <Button variant="ghost" onClick={() => { setStep(1); setDownloadUrl(null); }} className="w-full">
                    Create Another Document
                  </Button>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}