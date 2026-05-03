import { useState } from 'react'
import Navbar from './components/Navbar'
import FileUpload from './components/FileUpload'
import DataPreview from './components/DataPreview'
import PipelineStatus from './components/PipelineStatus'
import ChartGallery from './components/ChartGallery'
import InsightsPanel from './components/InsightsPanel'

import ReportView from './components/ReportView'
import { getApiUrl } from './api'

const PIPELINE_STEPS = [
  { key: 'profiling',           label: 'Profile',       icon: '📋' },
  { key: 'planning',            label: 'Plan',          icon: '🧠' },
  { key: 'validating',          label: 'Validate',      icon: '🛡️' },
  { key: 'cleaning',            label: 'Clean',         icon: '🧹' },
  { key: 'visualizing',         label: 'Visualize',     icon: '📊' },
  { key: 'analyzing',           label: 'Statistics',    icon: '📈' },
  { key: 'generating_insights', label: 'Insights',      icon: '💡' },
  { key: 'recomputing',         label: 'Recomputing',   icon: '🔄' },
  { key: 'complete',            label: 'Done',          icon: '✅' },
]

export default function App() {

  const [uploadInfo, setUploadInfo] = useState(null)
  const [status, setStatus] = useState('idle') // idle, uploading, analyzing, complete, error
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [retryCount, setRetryCount] = useState(0)

  const handleUpload = async (file) => {
    setError(null)
    setStatus('uploading')
    setReport(null)
    setRetryCount(0)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const uploadRes = await fetch(getApiUrl('/api/upload'), {
        method: 'POST',
        body: formData,
      })

      if (!uploadRes.ok) {
        const err = await uploadRes.json()
        throw new Error(err.detail || 'Upload failed')
      }

      const uploadData = await uploadRes.json()
      const sessionId = uploadData.session_id
      setUploadInfo(uploadData)
      setStatus('analyzing')
      setCurrentStep('profiling')
      setProgress(0.05)

      // Poll /api/status every 2 s so the UI mirrors the live pipeline step.
      // The backend explicitly sets status='recomputing' when the Critic Agent
      // rejects an attempt, so we just reflect whatever it reports.
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(getApiUrl(`/api/status/${uploadData.session_id}`))
          if (!statusRes.ok) return
          const s = await statusRes.json()
          setCurrentStep(s.status)
          setProgress(s.progress ?? 0)
          if (s.status === 'recomputing') {
            setRetryCount(prev => prev + 1)
          }
        } catch (_) { /* ignore transient poll errors */ }
      }, 2000)

      // Start analysis (long-running — wait for full response)
      const analyzeRes = await fetch(getApiUrl(`/api/analyze/${uploadData.session_id}`), {
        method: 'POST',
      })

      clearInterval(pollInterval)

      if (!analyzeRes.ok) {
        const err = await analyzeRes.json()
        throw new Error(err.detail || 'Analysis failed')
      }

      const reportData = await analyzeRes.json()
      setReport(reportData)
      setStatus('complete')
      setProgress(1)
      setCurrentStep('complete')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  const handleReset = () => {

    setUploadInfo(null)
    setStatus('idle')
    setProgress(0)
    setCurrentStep('')
    setReport(null)
    setError(null)
  }

  return (
    <div className="app">
      <Navbar status={status} onReset={handleReset} />

      <main className="app-container">
        {/* Upload Section */}
        {status === 'idle' && (
          <div className="animate-fade-in">
            <div className="section-header" style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <h1 className="section-title" style={{ fontSize: '2.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem' }}>
                <img src="/logo.png" alt="logo" style={{ width: '48px', height: '48px', borderRadius: '50%', objectFit: 'cover' }} />
                Ai Data Analyst
              </h1>
              <p className="section-subtitle" style={{ fontSize: '1rem', maxWidth: 600, margin: '0.5rem auto 0' }}>
                Upload your dataset and let our multi-agent AI system automatically
                clean, visualize, and generate insights from your data.
              </p>
            </div>
            <FileUpload onUpload={handleUpload} />
          </div>
        )}

        {/* Uploading */}
        {status === 'uploading' && (
          <div className="glass-card animate-fade-in" style={{ textAlign: 'center', padding: '3rem' }}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }}></div>
            <p style={{ color: 'var(--text-secondary)' }}>Uploading your file...</p>
          </div>
        )}

        {/* Analyzing */}
        {status === 'analyzing' && (
          <div className="animate-fade-in">
            {uploadInfo && (
              <div className="metrics-grid" style={{ marginBottom: '1.5rem' }}>
                <div className="metric-card">
                  <div className="metric-value">{uploadInfo.rows?.toLocaleString()}</div>
                  <div className="metric-label">Rows</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{uploadInfo.columns}</div>
                  <div className="metric-label">Columns</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{uploadInfo.filename}</div>
                  <div className="metric-label">File</div>
                </div>
              </div>
            )}

            <div className="glass-card">
              <PipelineStatus
                steps={PIPELINE_STEPS}
                currentStep={currentStep}
                progress={progress}
              />
              <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }}></div>
                {currentStep === 'recomputing' ? (
                  <>
                    <p style={{ color: 'var(--accent-amber, #f59e0b)', fontWeight: 600 }}>
                      🔄 Critic rejected output — recomputing analysis…
                    </p>
                    {retryCount > 0 && (
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: '0.4rem' }}>
                        Retry attempt {retryCount}
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p style={{ color: 'var(--text-secondary)' }}>
                      Running multi-agent analysis pipeline…
                    </p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                      This may take 1–2 minutes depending on dataset size and LLM response times.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {status === 'error' && (
          <div className="glass-card animate-fade-in" style={{ borderColor: 'var(--accent-rose)' }}>
            <h2 style={{ color: 'var(--accent-rose)', marginBottom: '1rem' }}>❌ Analysis Failed</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{error}</p>
            <button className="btn btn-primary" onClick={handleReset}>
              Try Again
            </button>
          </div>
        )}

        {/* Complete — Show Report */}
        {status === 'complete' && report && (
          <div className="animate-slide-up stagger">
            {/* Overview Metrics */}
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-value">
                  {report.dataset_overview?.rows_before_cleaning?.toLocaleString()}
                </div>
                <div className="metric-label">Original Rows</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {report.dataset_overview?.rows_after_cleaning?.toLocaleString()}
                </div>
                <div className="metric-label">Cleaned Rows</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {report.dataset_overview?.columns_after_cleaning}
                </div>
                <div className="metric-label">Columns</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {report.charts?.length || 0}
                </div>
                <div className="metric-label">Charts</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {report.insights?.length || 0}
                </div>
                <div className="metric-label">Insights</div>
              </div>

            </div>

            {/* Pipeline Complete Status */}
            <PipelineStatus
              steps={PIPELINE_STEPS}
              currentStep="complete"
              progress={1}
              complete
            />

            {/* Cleaning Log */}
            <ReportView report={report} />

            {/* Charts */}
            <ChartGallery charts={report.charts || []} />

            {/* Insights */}
            <InsightsPanel insights={report.insights || []} />


            {/* Actions */}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', flexWrap: 'wrap' }}>
              <button className="btn btn-primary" onClick={handleReset}>
                📁 Analyze Another File
              </button>
              <a
                className="btn btn-secondary"
                href={getApiUrl(`/api/download/${report.session_id}`)}
                download
              >
                ⬇️ Download Cleaned CSV
              </a>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
