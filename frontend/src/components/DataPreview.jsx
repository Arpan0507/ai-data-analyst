export default function DataPreview({ data, title }) {
  if (!data || data.length === 0) return null

  const columns = Object.keys(data[0])

  return (
    <div className="glass-card report-section">
      <div className="glass-card-header">
        <span className="icon">🗂️</span>
        <h2>{title || 'Data Preview'}</h2>
      </div>
      <div className="data-table-wrapper" style={{ maxHeight: 300 }}>
        <table className="data-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, i) => (
              <tr key={i}>
                {columns.map(col => (
                  <td key={col}>{row[col] != null ? String(row[col]) : '—'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
