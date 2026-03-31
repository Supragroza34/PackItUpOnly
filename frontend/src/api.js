const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE = isLocal ? "http://localhost:8000/api" : `${window.location.origin}/api`;


export function authHeaders() {
  const token = sessionStorage.getItem("access");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function parseApiError(text, status) {
  let errorMessage = `HTTP ${status}`;
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
  return errorMessage;
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
    const errorMessage = parseApiError(text, res.status);
    throw new Error(errorMessage);
  }

  if (res.status === 204) {
    return null;
  }

  return res.json();
}