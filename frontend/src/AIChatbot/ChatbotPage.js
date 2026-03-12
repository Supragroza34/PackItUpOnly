import React from "react";
import { Link } from "react-router-dom";
import Chatbot from "./Chatbot";
import "./ChatbotPage.css";

export default function ChatbotPage() {
  return (
    <div className="ai-chatbot-page">
      <div className="ai-chatbot-page-header">
        <Link to="/dashboard" className="ai-chatbot-back">
          ← Back to Dashboard
        </Link>
        <h1 className="ai-chatbot-page-title">AI Helper</h1>
        <p className="ai-chatbot-page-subtitle">
          Ask questions about support, tickets, or general help.
        </p>
      </div>
      <div className="ai-chatbot-page-content">
        <Chatbot />
      </div>
    </div>
  );
}
