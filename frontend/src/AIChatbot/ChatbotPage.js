import React from "react";
import Chatbot from "./Chatbot";
import "./ChatbotPage.css";
import UserNavbar from "../components/UserNavbar";

export default function ChatbotPage() {
  return (
    <>
      <UserNavbar />
      <div className="ai-chatbot-page">
        <div className="ai-chatbot-page-header">
          <h1 className="ai-chatbot-page-title">AI Helper</h1>
          <p className="ai-chatbot-page-subtitle">
            Ask questions about support, tickets, or general help.
          </p>
        </div>
        <div className="ai-chatbot-page-content">
          <Chatbot />
        </div>
      </div>
    </>
  );
}
