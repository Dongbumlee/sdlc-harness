// CANARY: No copyright header (Code Quality Reviewer should catch)

import React, { useState } from "react";

// CANARY: Hardcoded color — should use CSS variable (UX Reviewer should catch)
const headerStyle = {
  backgroundColor: "#1a1a2e",
  color: "#ffffff",
  padding: "20px",
  width: "2000px", // CANARY: Fixed width > viewport (UX Reviewer should catch)
};

// CANARY: outline: none without replacement (UX Reviewer should catch)
const inputStyle = {
  outline: "none",
  border: "1px solid #ccc",
  padding: "8px",
};

interface ChatMessage {
  role: string;
  content: string;
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    // CANARY: No input validation before submit (UX Reviewer should catch)
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: input }),
    });
    const data = await response.json();
    setMessages([...messages, { role: "user", content: input }, data]);
    setInput("");
  };

  return (
    <div style={headerStyle}>
      <h1>Document Chat</h1>

      {/* CANARY: img without alt attribute (UX Reviewer should catch) */}
      <img src="/logo.png" />

      {/* CANARY: div with onClick but no keyboard handler (UX Reviewer should catch) */}
      <div onClick={() => console.log("clicked")} style={{ cursor: "pointer" }}>
        Click me
      </div>

      {/* CANARY: No empty state handling (UX Reviewer should catch) */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i}>{msg.content}</div>
        ))}
      </div>

      <input
        style={inputStyle}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        // CANARY: No onKeyDown handler for Enter key (UX Reviewer should catch)
      />

      <button onClick={sendMessage}>Send</button>

      {/* CANARY: dangerouslySetInnerHTML without sanitization (Security Reviewer should catch) */}
      <div dangerouslySetInnerHTML={{ __html: messages[0]?.content || "" }} />

      {/* CANARY: No Error Boundary component (UX Reviewer should catch) */}

      {/* CANARY: console.log in production code (Code Quality Reviewer should catch) */}
      {console.log("App rendered")}
    </div>
  );
}
