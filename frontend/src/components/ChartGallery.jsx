export default function ChartGallery({ charts }) {
  if (!charts || charts.length === 0) {
    return (
      <div className="glass-card report-section">
        <div className="glass-card-header">
          <span className="icon">📊</span>
          <h2>Visualizations</h2>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p>No charts were generated for this dataset.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="report-section">
      <div className="section-header">
        <h2 className="section-title">📊 Visualizations</h2>
        <p className="section-subtitle">{charts.length} charts generated from your data</p>
      </div>
      <div className="chart-grid">
        {charts.map((chart, i) => (
          <div key={i} className="chart-card animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
            {chart.image_base64 ? (
              <img
                src={`data:image/png;base64,${chart.image_base64}`}
                alt={chart.title || `Chart ${i + 1}`}
                loading="lazy"
              />
            ) : (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                Image not available
              </div>
            )}
            <div className="chart-card-footer">
              <div className="chart-card-title">{chart.title || `Chart ${i + 1}`}</div>
              <div className="chart-card-type">{chart.chart_type}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
