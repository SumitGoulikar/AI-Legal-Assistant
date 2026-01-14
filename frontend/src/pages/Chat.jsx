// frontend/src/pages/Chat.jsx
import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { Send, Plus, MessageSquare, Bot, User, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import toast from 'react-hot-toast';

function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300'
      }`}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${
        isUser 
          ? 'bg-primary-600 text-white' 
          : 'bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-800 dark:text-gray-200 shadow-sm'
      }`}>
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose dark:prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  
  const initialQuery = searchParams.get('q');
  const initialSessionId = searchParams.get('session');
  const documentContext = location.state?.context;
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState(initialQuery || '');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(initialSessionId || null);
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

  useEffect(() => {
    if (initialSessionId) {
      loadSession(initialSessionId);
    }
  }, [initialSessionId]);

  // Handle Document Context from Analyze Page
  useEffect(() => {
    const initChatWithContext = async () => {
      if (documentContext && !sessionId) {
        // Create a new session specifically for this document
        const newId = await createSession("Document Analysis Chat");
        if (newId) {
          // Send the context as a hidden "system" message (or first user prompt)
          // We send it as user message so the LLM sees it in history
          const contextPrompt = `I have a legal document I want to discuss. Here is the text:\n\n${documentContext}\n\nPlease acknowledge you have read it and are ready to answer questions about it.`;
          
          setLoading(true);
          try {
            await api.post(`/chat/sessions/${newId}/messages`, {
              content: contextPrompt
            });
            // Add a welcome message from bot (simulated)
            setMessages([{ 
              role: 'assistant', 
              content: "I have read the document you provided. What would you like to know about it? You can ask about specific clauses, risks, or summaries." 
            }]);
          } catch (error) {
            toast.error("Failed to initialize document chat");
          } finally {
            setLoading(false);
          }
        }
      }
    };
    
    if (documentContext) {
      initChatWithContext();
      // Clear state so it doesn't re-run on refresh
      window.history.replaceState({}, document.title);
    }
  }, [documentContext]);

  const loadSessions = async () => {
    try {
      const response = await api.get('/chat/sessions');
      setSessions(response.data.sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const createSession = async (title = 'New Legal Query') => {
    try {
      const response = await api.post('/chat/sessions', {
        session_type: 'general',
        title: title
      });
      const newId = response.data.id;
      setSessionId(newId);
      setMessages([]);
      loadSessions();
      setSearchParams({ session: newId });
      return newId;
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
      setSearchParams({ session: id });
    } catch (error) {
      toast.error('Failed to load chat');
    } finally {
      setLoading(false);
    }
  };

  const deleteSession = async (e, id) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation?")) return;

    try {
      await api.delete(`/chat/sessions/${id}`);
      toast.success("Chat deleted");
      setSessions(prev => prev.filter(s => s.id !== id));
      if (sessionId === id) {
        handleNewChat();
      }
    } catch (error) {
      toast.error("Failed to delete chat");
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
      if (messages.length === 0) loadSessions(); 
      
    } catch (error) {
      console.error(error);
      toast.error('Failed to get answer');
      setMessages(prev => prev.slice(0, -1)); 
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setSearchParams({});
  };

  return (
    <div className="flex h-[calc(100vh-100px)] gap-6">
      {/* Sidebar: Chat History */}
      <Card className="w-64 flex flex-col h-full hidden md:flex">
        <div className="p-4 border-b border-gray-200 dark:border-slate-700">
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2"
            onClick={handleNewChat}
          >
            <Plus size={16} />
            New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => loadSession(session.id)}
              className={`group flex items-center justify-between w-full px-3 py-2 rounded-lg text-sm cursor-pointer transition ${
                sessionId === session.id 
                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 font-medium' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800'
              }`}
            >
              <div className="flex items-center gap-2 truncate flex-1">
                <MessageSquare size={14} />
                <span className="truncate">{session.title || 'Untitled Chat'}</span>
              </div>
              
              <button 
                onClick={(e) => deleteSession(e, session.id)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 rounded transition"
                title="Delete Chat"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Main Chat Area */}
      <Card className="flex-1 flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
              <div className="w-16 h-16 bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 rounded-full flex items-center justify-center">
                <Bot size={32} />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Legal Assistant</h3>
                <p className="text-sm mt-1 text-gray-600 dark:text-gray-400">Ask questions about Indian Law.</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {['What is a contract?', 'Breach of contract penalties', 'IPC Section 420', 'Draft an NDA'].map(q => (
                  <button 
                    key={q}
                    onClick={() => { setInput(q); }} 
                    className="px-3 py-2 bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 rounded border border-gray-200 dark:border-slate-700 transition"
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
              <div className="w-8 h-8 bg-gray-200 dark:bg-slate-700 rounded-full flex items-center justify-center">
                <Bot size={16} className="text-gray-500 dark:text-gray-400 animate-pulse" />
              </div>
              <div className="bg-gray-100 dark:bg-slate-800 rounded-lg px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900">
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a legal question..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              <Send size={18} />
            </Button>
          </form>
          <p className="text-xs text-center text-gray-400 dark:text-gray-500 mt-2">
            AI responses are for informational purposes only. Consult a lawyer for legal advice.
          </p>
        </div>
      </Card>
    </div>
  );
}