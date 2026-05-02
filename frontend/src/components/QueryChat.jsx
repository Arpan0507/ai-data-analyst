import { useState } from 'react'
const API_BASE = "https://ai-data-analyst-backend-xyt7.onrender.com"
export default function QueryChat({ sessionId }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const q = question.trim()
    setMessages(prev => [...prev, { type: 'user', text: q }])
    setQuestion('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/query/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, session_id: sessionId }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Query failed')
      }

      const data = await res.json()
      setMessages(prev => [...prev, {
        type: 'assistant',
        text: data.answer,
        code: data.query_code,
      }])
    } catch (err) {
      // TypeError means the browser couldn't reach the server at all
      const isNetworkError = err instanceof TypeError
      const userMsg = isNetworkError
        ? 'Cannot reach the backend server. Make sure it is running on port 8000.'
        : err.message
      setMessages(prev => [...prev, {
        type: 'error',
        text: `Error: ${userMsg}`,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="report-section">
      <div className="section-header">
        <h2 className="section-title">💬 Ask Your Data</h2>
        <p className="section-subtitle">Ask questions about your dataset in natural language</p>
      </div>
      <div className="glass-card">
        {/* Messages */}
        {messages.length > 0 && (
          <div style={{
            maxHeight: 400,
            overflowY: 'auto',
            marginBottom: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}>
            {messages.map((msg, i) => (
              <div key={i} style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: msg.type === 'user'
                  ? 'rgba(99, 102, 241, 0.1)'
                  : msg.type === 'error'
                    ? 'rgba(244, 63, 94, 0.1)'
                    : 'var(--bg-glass)',
                borderLeft: `3px solid ${
                  msg.type === 'user' ? 'var(--accent-indigo)' :
                  msg.type === 'error' ? 'var(--accent-rose)' :
                  'var(--accent-cyan)'
                }`,
              }}>
                <div style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: msg.type === 'user' ? 'var(--accent-indigo)' :
                         msg.type === 'error' ? 'var(--accent-rose)' :
                         'var(--accent-cyan)',
                  marginBottom: '0.25rem',
                }}>
                  {msg.type === 'user' ? 'You' : msg.type === 'error' ? 'Error' : 'AI Analyst'}
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                  {msg.text}
                </div>
                {msg.code && (
                  <details style={{ marginTop: '0.5rem' }}>
                    <summary style={{ fontSize: '0.75rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                      View generated code
                    </summary>
                    <pre style={{
                      background: 'rgba(0,0,0,0.3)',
                      padding: '0.5rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.78rem',
                      color: 'var(--accent-cyan)',
                      marginTop: '0.25rem',
                      overflow: 'auto',
                    }}>
                      {msg.code}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} className="query-input-wrapper">
          <input
            className="query-input"
            type="text"
            placeholder="e.g., What product has the highest average profit?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            id="query-input"
          />
          <button
            className="btn btn-primary"
            type="submit"
            disabled={loading || !question.trim()}
            id="query-submit"
          >
            {loading ? <span className="spinner"></span> : '🔍 Ask'}
          </button>
        </form>
      </div>
    </div>
  )
}
