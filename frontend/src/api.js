// Same origin in production (Heroku); localhost:8000 when developing
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = process.env.NODE_ENV === 'production'
  ? 'https://packituponly-940a2f158db0.herokuapp.com/api'
  : 'http://localhost:8000/api';


export function authHeaders() {
  const token = localStorage.getItem("access");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch(path, options = {}, { auth = false } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(auth ? authHeaders() : {}),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    let errorMessage = `HTTP ${res.status}`;
    
    try {
      const errorData = JSON.parse(text);
      
      if (typeof errorData === 'object') {
        const messages = [];
        for (const [field, errors] of Object.entries(errorData)) {
          if (Array.isArray(errors)) {
            messages.push(...errors);
          } else if (typeof errors === 'string') {
            messages.push(errors);
          }
        }
        if (messages.length > 0) {
          errorMessage = messages.join(' ');
        }
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      }
    } catch (e) {
      errorMessage = text || errorMessage;
    }
    
    throw new Error(errorMessage);
  }

  if (res.status === 204) {
    return null;
  }

  return res.json();
}