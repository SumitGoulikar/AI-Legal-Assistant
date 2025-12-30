// frontend/src/pages/Chat.jsx
import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Send, Plus, MessageSquare, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import toast from 'react-hot-toast';

// Chat Bubble Component (Internal)
function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-700'
      }`}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${
        isUser 
          ? 'bg-primary-600 text-white' 
          : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
      }`}>
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100/20">
                <p className="text-xs font-semibold opacity-70 mb-1">Sources:</p>
                <div className="space-y-1">
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="text-xs bg-black/5 p-2 rounded">
                      <p className="font-medium">
                        {source.title || source.document || 'Legal Source'}
                        {source.page && ` (Page ${source.page})`}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get('q');
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState(initialQuery || '');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await api.get('/chat/sessions');
      setSessions(response.data.sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const createSession = async () => {
    try {
      const response = await api.post('/chat/sessions', {
        session_type: 'general',
        title: 'New Legal Query'
      });
      setSessionId(response.data.id);
      setMessages([]);
      loadSessions();
      return response.data.id;
    } catch (error) {
      toast.error('Failed to start chat');
      return null;
    }
  };

  const loadSession = async (id) => {
    try {
      setLoading(true);
      const response = await api.get(`/chat/sessions/${id}`);
      setSessionId(id);
      setMessages(response.data.messages);
    } catch (error) {
      toast.error('Failed to load chat');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        currentSessionId = await createSession();
        if (!currentSessionId) return;
      }

      const response = await api.post(`/chat/sessions/${currentSessionId}/messages`, {
        content: currentInput
      });

      setMessages(prev => [...prev, response.data.assistant_message]);
      if (messages.length === 0) loadSessions(); // Refresh sidebar list
      
    } catch (error) {
      toast.error('Failed to get answer');
      setMessages(prev => prev.slice(0, -1)); // Remove failed message
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-100px)] gap-6">
      {/* Sidebar: Chat History */}
      <Card className="w-64 flex flex-col h-full hidden md:flex">
        <div className="p-4 border-b border-gray-200">
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2"
            onClick={() => {
              setSessionId(null);
              setMessages([]);
            }}
          >
            <Plus size={16} />
            New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => loadSession(session.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition ${
                sessionId === session.id 
                  ? 'bg-primary-50 text-primary-700 font-medium' 
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageSquare size={14} />
                <span className="truncate">{session.title || 'Untitled Chat'}</span>
              </div>
            </button>
          ))}
        </div>
      </Card>

      {/* Main Chat Area */}
      <Card className="flex-1 flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
              <div className="w-16 h-16 bg-primary-50 text-primary-600 rounded-full flex items-center justify-center">
                <Bot size={32} />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900">AI Legal Assistant</h3>
                <p className="text-sm mt-1">Ask questions about Indian Law.</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {['What is a contract?', 'Breach of contract penalties', 'IPC Section 420', 'Draft an NDA'].map(q => (
                  <button 
                    key={q}
                    onClick={() => { setInput(q); }} 
                    className="px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))
          )}
          {loading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <Bot size={16} className="text-gray-500 animate-pulse" />
              </div>
              <div className="bg-gray-100 rounded-lg px-4 py-3 text-sm text-gray-500">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a legal question..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              <Send size={18} />
            </Button>
          </form>
          <p className="text-xs text-center text-gray-400 mt-2">
            AI responses are for informational purposes only. Consult a lawyer for legal advice.
          </p>
        </div>
      </Card>
    </div>
  );
}