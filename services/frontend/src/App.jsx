import { useState, useRef, useEffect } from 'react'
import './App.css'

const GATEWAY_URL = "http://localhost:8000";
// Ingestion might be proxied or direct. Using direct for now as per spec gap.
const INGESTION_URL = "http://localhost:8001";

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  // Chat State
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hello! I am your RAG assistant. Ask me anything about your documents.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Upload State
  const [uploadStatus, setUploadStatus] = useState([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${GATEWAY_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userMsg }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      // Assuming API returns { answer: "...", citations: [...] }
      const botContent = data.answer || "I received your message but got an empty response.";

      setMessages(prev => [...prev, { role: 'bot', content: botContent, citations: data.citations }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'bot',
        content: "Sorry, I couldn't reach the server. Make sure the Gateway service is running on Port 8000."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const statusId = Date.now();
    setUploadStatus(prev => [...prev, { id: statusId, name: file.name, status: 'Uploading...' }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${INGESTION_URL}/ingest`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setUploadStatus(prev => prev.map(item =>
          item.id === statusId ? { ...item, status: 'Completed' } : item
        ));
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      setUploadStatus(prev => prev.map(item =>
        item.id === statusId ? { ...item, status: 'Error: Is Ingestion Service on Port 8001?' } : item
      ));
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">MyRAG System</div>
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button
            className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Manage Documents
          </button>
        </div>
      </header>

      <main className="content-area">
        {activeTab === 'chat' ? (
          <div className="chat-container">
            <div className="messages-list">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`}>
                  {msg.content}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations-section">
                      <h4 className="citations-title">📚 Sources:</h4>
                      {msg.citations.map((citation, citIdx) => (
                        <div key={citIdx} className="citation-item">
                          <div className="citation-header">
                            <strong>{citation.title || citation.doi}</strong>
                            {citation.published_date && (
                              <span className="citation-date"> ({citation.published_date})</span>
                            )}
                          </div>

                          {citation.authors && citation.authors.length > 0 && (
                            <div className="citation-authors">
                              {citation.authors.slice(0, 3).join(', ')}
                              {citation.authors.length > 3 && ' et al.'}
                            </div>
                          )}

                          {citation.journal && (
                            <div className="citation-journal">
                              <em>{citation.journal}</em>
                            </div>
                          )}

                          <div className="citation-meta">
                            <span className="citation-doi">
                              DOI: <a href={citation.url} target="_blank" rel="noopener noreferrer">
                                {citation.doi}
                              </a>
                            </span>
                            {citation.pages && citation.pages.length > 0 && (
                              <span className="citation-pages">
                                {' | Pages: ' + citation.pages.join(', ')}
                              </span>
                            )}
                          </div>

                          <div className="citation-links">
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="citation-link"
                            >
                              🔗 View Paper
                            </a>
                            {citation.pdf_url && (
                              <a
                                href={citation.pdf_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="citation-link pdf-link"
                              >
                                📄 Download PDF
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {isLoading && <div className="message bot">Thinking...</div>}
              <div ref={messagesEndRef} />
            </div>
            <form className="input-area" onSubmit={handleSendMessage}>
              <input
                type="text"
                className="chat-input"
                placeholder="Ask a question about your documents..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button type="submit" className="send-btn">Send</button>
            </form>
          </div>
        ) : (
          <div className="upload-container">
            <label className="drop-zone">
              <span className="upload-icon">📁</span>
              <span className="upload-text">Click or Drop PDF files here</span>
              <input
                type="file"
                className="file-input"
                accept=".pdf"
                onChange={handleFileUpload}
              />
            </label>

            <div className="status-log">
              <h3>Upload Status</h3>
              {uploadStatus.map((item) => (
                <div key={item.id} className="status-item">
                  <span>{item.name}</span>
                  <span style={{ color: item.status.includes('Error') ? '#ff6b6b' : '#51cf66' }}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
