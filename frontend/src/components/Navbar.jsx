export default function Navbar({ status, onReset }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <img src="/logo.png" alt="Ai Data Analyst Logo" style={{ width: '32px', height: '32px', borderRadius: '50%', objectFit: 'cover' }} />
          <span className="navbar-logo" style={{ marginLeft: '8px' }}>Ai Data Analyst</span>
        </div>
        <div className="navbar-status">
          {status === 'complete' && (
            <button className="btn btn-secondary" onClick={onReset} style={{ padding: '4px 12px', fontSize: '0.8rem' }}>
              New Analysis
            </button>
          )}
          <span className="status-dot" style={{
            background: status === 'error' ? 'var(--accent-rose)' :
                         status === 'analyzing' ? 'var(--accent-amber)' :
                         'var(--accent-emerald)',
            boxShadow: status === 'error' ? '0 0 8px rgba(244,63,94,0.5)' :
                        status === 'analyzing' ? '0 0 8px rgba(245,158,11,0.5)' :
                        '0 0 8px rgba(16,185,129,0.5)',
          }}></span>
          <span>{status === 'idle' ? 'Ready' : status === 'analyzing' ? 'Processing...' : status === 'complete' ? 'Complete' : status === 'error' ? 'Error' : 'Ready'}</span>
        </div>
      </div>
    </nav>
  )
}
