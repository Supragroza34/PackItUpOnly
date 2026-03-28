import React, { useState, useRef, useEffect } from "react";
import { authHeaders } from "../api";
import "./Chatbot.css";



export function getApiChatUrl() {
  const { hostname, protocol, origin } = window.location;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
  return isLocal
    ? `${protocol}//${hostname}:8000/api/ai-chatbot/chat/`
    : `${origin}/api/ai-chatbot/chat/`;
}

export const API_CHAT = getApiChatUrl();

function getApiError(data, status) {
  return data.error || data.detail || `Error ${status}`;
}

function toAssistantMessage(data) {
  return data.message || { role: "assistant", content: "" };
}

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function sendChatRequest(history) {
    const res = await fetch(API_CHAT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({
        messages: history.map((m) => ({ role: m.role, content: m.content })),
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(getApiError(data, res.status));
    return data;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setError("");
    const userMessage = { role: "user", content: text };
    const requestHistory = [...messages, userMessage];
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendChatRequest(requestHistory);
      setMessages((prev) => [...prev, toAssistantMessage(data)]);
    } catch (err) {
      setError(err.message || "Could not reach the chat service.");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }

  // Welcome message for initial render
  const welcomeText = "Ask me anything about support, tickets, or studying.";

  return (
    <div className="ai-chatbot">
      <div className="ai-chatbot-messages">
        {/* Welcome message only if no messages yet */}
        {messages.length === 0 && (
          <div className="ai-chatbot-welcome">{welcomeText}</div>
        )}
        {/* Render chat messages */}
        {messages.map((msg, idx) => (
          <div key={idx} className={`ai-chatbot-msg ai-chatbot-msg-${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="ai-chatbot-typing" aria-live="polite">
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {/* Error alert for accessibility */}
      {error && (
        <div role="alert" className="ai-chatbot-error">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="ai-chatbot-form">
        <input
          type="text"
          placeholder="Type your question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          aria-label="Chat message"
        />
        <button type="submit" className="ai-chatbot-send" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}
