import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { from: 'bot', text: 'Hello! Ask me anything.' }
  ]);
  const [input, setInput] = useState('');
  const chatBoxRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMessage = { from: 'user', text: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      const API_URL = process.env.REACT_APP_API_URL;

      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_id:'test', 
          input:trimmed,
          use_memory: true,
        })
      });

      const data = await res.text();
      console.log('API Response:', data);

      const cleanText=data
      .replace(/^"|"$/g, '')
      .replace(/\\n/g, '\n');

      const botMessage = { from: 'bot', text: cleanText || 'No response from server' };
      setMessages((prev) => [...prev, botMessage]);

    } catch (err) {
      console.error('Error sending message:', err);
      setMessages((prev) => [
        ...prev,
        { from: 'bot', text: 'Error connecting to server.' }
      ]);
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-header">MCP Chatbot 🤖</h2>

      <div className="chat-box" ref={chatBoxRef}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-message ${msg.from}`}
            style={{whiteSpace:"pre-line"}} // respects \n
            >
            <strong>{msg.from === 'user' ? 'You' : 'Bot'}:</strong>{msg.text}
          </div>
        ))}
      </div>

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              sendMessage();
            }
          }}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;
