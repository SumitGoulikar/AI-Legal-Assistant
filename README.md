
# ⚖️ AI Legal Assistant

> An intelligent, full-stack legal document assistant powered by AI. Upload contracts, policies, or agreements — and get instant summaries, risk detection, clause extraction, and conversational Q&A.

Built with **FastAPI**, **React + Vite**, **RAG**, and **LLMs**, this tool enables users to interact with legal documents using natural language — like chatting with an AI lawyer.

---

## ✅ Key Features

### 📄 Document Processing
- Upload PDFs, DOCX, and TXT files  
- Automatic text extraction & page-aware chunking  
- Secure server-side storage  

### 🧠 AI-Powered Insights
- Generate concise summaries  
- Identify high-risk clauses  
- Extract key terms and obligations  
- Answer questions using context from the document  

### 💬 Conversational Chat
- Chat with your document naturally  
- Maintain chat history across sessions  
- Real-time token usage tracking  

### 🔐 Secure User Experience
- JWT-based authentication  
- User-specific document isolation  
- Sign-up, login, and profile management  

### 🌗 Modern UI Design
- Light & dark mode toggle  
- Side-by-side document viewer and AI output  
- Responsive design with Tailwind CSS  
- Clean, intuitive interface  

---

## 🛠️ Tech Stack

| Layer        | Technologies |
|-------------|--------------|
| **Backend** | FastAPI, SQLAlchemy (Async), SQLite, PyMuPDF, python-docx, ChromaDB, SentenceTransformers |
| **Frontend** | React + Vite, Tailwind CSS, React Router, Axios, Lucide Icons |
| **AI/LLM**  | RAG architecture, Pluggable LLMs (Ollama, OpenAI, Groq, OpenRouter) |
| **Auth**    | JWT tokens, secure password hashing |

---

## 📁 Project Structure

```
legal-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── api/                # API routes
│   │   ├── models/             # DB models
│   │   ├── services/           # LLM, document, vector services
│   │   ├── core/               # Auth, security
│   │   └── utils/              # File processing
│   ├── data/                   # DB & vector store
│   ├── requirements.txt
│   └── .env                    # Config variables
│
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Dashboard, Analyze, Chat
│   │   ├── services/           # API client
│   │   └── main.jsx
│   ├── vite.config.js
│   └── index.css
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
# or on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/legal_assistant.db
SECRET_KEY=your-secret-key-here
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:1b
```

Start the server:

```bash
uvicorn app.main:app --reload
```

👉 Access API Docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

👉 Open in browser: [http://localhost:5173](http://localhost:5173)

---

## 🔍 API Endpoints

- `POST /api/v1/documents/extract_text` – Extract text from uploaded document  
- `POST /api/v1/documents/analyze_text` – Get summary, risks, and key clauses  
- `POST /api/v1/chat/query` – Ask questions about the document  
- `POST /api/v1/auth/login` – User login  
- `POST /api/v1/auth/signup` – Create new account  

---

## 🧪 Testing

Run tests for backend functionality:

```bash
python test_auth.py
python test_documents.py
python test_llms.py
```

---

## 🎯 Ideal Use Cases

- Law students analyzing case documents  
- Legal professionals reviewing contracts quickly  
- Compliance officers detecting risks  
- Researchers summarizing policy texts  
- Anyone needing AI-assisted legal insight  

---

## ⚠️ Important Note

This is a **prototype for educational and research purposes only**.  
It does **not** provide legal advice. Always consult a qualified attorney.

---

## 👨‍💻 About Me

**Sumit Goulikar**  
Computer Science Undergraduate | AI & Full-Stack Developer  
Passionate about building intelligent, user-centric applications that bridge technology and real-world problems.


---

✅ *Open source. Built with ❤️ and Python.*  
📅 Last updated: Wednesday, January 14, 2026
