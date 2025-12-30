// frontend/src/services/api.js
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1.js';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// REMOVED: Request interceptor (Token injection)
// REMOVED: Response interceptor (401 Redirect)

export default api;