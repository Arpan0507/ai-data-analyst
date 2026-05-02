export default function ReportView({ report }) {
  if (!report) return null

  const cleaningSteps = report.cleaning_steps || []
  const validationNotes = report.validation_notes || []
  const explanations = report.cleaning_explanations || {}

  return (
    <div className="report-section">
      {/* Cleaning Steps */}
      <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
        <div className="glass-card-header">
          <span className="icon">🧹</span>
          <h2>Data Cleaning Report</h2>
        </div>

        {cleaningSteps.length > 0 ? (
          <ul className="exec-log">
            {cleaningSteps.map((step, i) => (
              <li key={i} className="exec-log-item">
                <span className="exec-log-icon">
                  {step.success ? '✅' : '❌'}
                </span>
                <div>
                  <div style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                    {step.action}{step.column ? ` → ${step.column}` : ''}
                  </div>
                  <div className="exec-log-message">{step.message}</div>
                  {step.rows_before !== step.rows_after && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Rows: {step.rows_before?.toLocaleString()} → {step.rows_after?.toLocaleString()}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No cleaning steps were applied.</p>
        )}
      </div>

      {/* Explanations */}
      {Object.keys(explanations).length > 0 && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <div className="glass-card-header">
            <span className="icon">📝</span>
            <h2>Cleaning Explanations</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {Object.entries(explanations).map(([key, value]) => (
              <div key={key} style={{
                padding: '0.75rem',
                background: 'var(--bg-glass)',
                borderRadius: 'var(--radius-sm)',
                borderLeft: '3px solid var(--accent-indigo)',
              }}>
                <div style={{ fontWeight: 600, fontSize: '0.82rem', color: 'var(--text-accent)', marginBottom: '0.25rem' }}>
                  {key}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Notes */}
      {validationNotes.length > 0 && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <div className="glass-card-header">
            <span className="icon">🛡️</span>
            <h2>Validation Notes</h2>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {validationNotes.map((note, i) => (
              <li key={i} style={{
                padding: '0.5rem 0.75rem',
                background: 'rgba(245, 158, 11, 0.05)',
                border: '1px solid rgba(245, 158, 11, 0.15)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.85rem',
                color: 'var(--accent-amber)',
              }}>
                ⚡ {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
