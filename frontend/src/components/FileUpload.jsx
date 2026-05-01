import { useState, useRef } from 'react'

export default function FileUpload({ onUpload }) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const inputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => setDragOver(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleFileInput = (e) => {
    const file = e.target.files[0]
    if (file) handleFile(file)
  }

  const handleFile = (file) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      alert('Please upload a CSV or Excel file.')
      return
    }
    if (file.size > 50 * 1024 * 1024) {
      alert('File size exceeds 50MB limit.')
      return
    }
    setSelectedFile(file)
  }

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile)
    }
  }

  return (
    <div className="glass-card" style={{ maxWidth: 640, margin: '0 auto' }}>
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        id="file-upload-zone"
      >
        <input
          ref={inputRef}
          type="file"
          className="upload-input"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileInput}
          id="file-input"
        />
        <span className="upload-icon">📂</span>
        <p className="upload-title">
          {selectedFile ? selectedFile.name : 'Drop your dataset here'}
        </p>
        <p className="upload-subtitle">
          {selectedFile
            ? `${(selectedFile.size / 1024).toFixed(1)} KB — Click to change`
            : 'Supports CSV and Excel files up to 50MB'}
        </p>
      </div>

      {selectedFile && (
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            style={{ padding: '10px 32px', fontSize: '0.95rem' }}
            id="analyze-button"
          >
            🚀 Analyze Dataset
          </button>
        </div>
      )}

      {/* Feature highlights */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '0.75rem',
        marginTop: '1.5rem',
      }}>
        {[
          { icon: '🧠', label: 'AI-Powered Planning' },
          { icon: '🧹', label: 'Auto Data Cleaning' },
          { icon: '📊', label: 'Smart Visualizations' },
          { icon: '💡', label: 'Business Insights' },
        ].map((f) => (
          <div key={f.label} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
            padding: '0.5rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-glass)',
          }}>
            <span>{f.icon}</span>
            <span>{f.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
