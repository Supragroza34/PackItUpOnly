import React, { useState, useRef, useEffect } from "react";
import { authHeaders } from "../api";
import "./Chatbot.css";

const API_CHAT = `${window.location.protocol}//${window.location.hostname}:8000/api/ai-chatbot/chat/`;

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

  return (
    <div className="ai-chatbot">
      <div className="ai-chatbot-messages" role="log" aria-live="polite">
        {messages.length === 0 && (
          <div className="ai-chatbot-welcome">
            <p>Ask me anything about support, tickets, or studying. I’ll try to help.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`ai-chatbot-msg ai-chatbot-msg--${m.role}`}>
            <span className="ai-chatbot-msg-role">
              {m.role === "user" ? "You" : "Assistant"}
            </span>
            <div className="ai-chatbot-msg-content">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="ai-chatbot-msg ai-chatbot-msg--assistant">
            <span className="ai-chatbot-msg-role">Assistant</span>
            <div className="ai-chatbot-msg-content ai-chatbot-typing">Thinking…</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="ai-chatbot-error" role="alert">
          {error}
        </div>
      )}

      <form className="ai-chatbot-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="ai-chatbot-input"
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
