export default function CriticPanel({ feedback }) {
  if (!feedback) return null

  const scoreColor = feedback.quality_score >= 0.7
    ? 'var(--accent-emerald)'
    : feedback.quality_score >= 0.4
      ? 'var(--accent-amber)'
      : 'var(--accent-rose)'

  return (
    <div className="report-section">
      <div className="section-header">
        <h2 className="section-title">🔍 Critic Agent Review</h2>
        <p className="section-subtitle">Quality validation by the Critic Agent</p>
      </div>
      <div className={`glass-card critic-card ${feedback.approved ? 'approved' : 'rejected'}`}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1rem' }}>
          <div>
            <div className="critic-score" style={{ color: scoreColor }}>
              {(feedback.quality_score * 100).toFixed(0)}%
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Quality Score
            </div>
          </div>
          <div style={{
            padding: '6px 16px',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.82rem',
            fontWeight: 600,
            background: feedback.approved ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
            color: feedback.approved ? 'var(--accent-emerald)' : 'var(--accent-rose)',
            border: `1px solid ${feedback.approved ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}`,
          }}>
            {feedback.approved ? '✅ Approved' : '⚠️ Needs Improvement'}
          </div>
        </div>

        {feedback.summary && (
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem', lineHeight: 1.6 }}>
            {feedback.summary}
          </p>
        )}

        {feedback.issues && feedback.issues.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-rose)', marginBottom: '0.5rem' }}>
              Issues Found
            </h4>
            <ul className="critic-issues">
              {feedback.issues.map((issue, i) => (
                <li key={i}>{issue}</li>
              ))}
            </ul>
          </div>
        )}

        {feedback.corrections && feedback.corrections.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>
              Suggested Corrections
            </h4>
            <ul className="critic-issues">
              {feedback.corrections.map((corr, i) => (
                <li key={i} style={{ }}>{corr}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
