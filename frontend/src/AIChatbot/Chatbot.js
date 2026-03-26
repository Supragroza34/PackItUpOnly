import React, { useState, useRef, useEffect } from "react";
import { authHeaders } from "../api";
import "./Chatbot.css";


const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
export const API_CHAT = isLocal
  ? `${window.location.protocol}//${window.location.hostname}:8000/api/ai-chatbot/chat/`
  : `${window.location.origin}/api/ai-chatbot/chat/`;


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

  async function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setError("");
    const userMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_CHAT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders(),
        },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || data.detail || `Error ${res.status}`);
        setMessages((prev) => prev.slice(0, -1));
        return;
      }
      const assistantMessage = data.message || { role: "assistant", content: "" };
      setMessages((prev) => [...prev, assistantMessage]);
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
