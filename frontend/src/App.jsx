import { useState } from 'react'
import Navbar from './components/Navbar'
import FileUpload from './components/FileUpload'
import DataPreview from './components/DataPreview'
import PipelineStatus from './components/PipelineStatus'
import ChartGallery from './components/ChartGallery'
import InsightsPanel from './components/InsightsPanel'
import ReportView from './components/ReportView'

const API_BASE = "https://ai-data-analyst-backend-xyt7.onrender.com"

const PIPELINE_STEPS = [
  { key: 'profiling', label: 'Profile', icon: '📋' },
  { key: 'planning', label: 'Plan', icon: '🧠' },
  { key: 'validating', label: 'Validate', icon: '🛡️' },
  { key: 'cleaning', label: 'Clean', icon: '🧹' },
  { key: 'visualizing', label: 'Visualize', icon: '📊' },
  { key: 'analyzing', label: 'Statistics', icon: '📈' },
  { key: 'generating_insights', label: 'Insights', icon: '💡' },
  { key: 'recomputing', label: 'Recomputing', icon: '🔄' },
  { key: 'complete', label: 'Done', icon: '✅' },
]

export default function App() {
  const [uploadInfo, setUploadInfo] = useState(null)
  const [status, setStatus] = useState('idle')
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

      // ✅ FIXED UPLOAD API
      const uploadRes = await fetch(`${API_BASE}/api/upload`, {
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

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_BASE}/api/status/${sessionId}`)
          if (!statusRes.ok) return

          const s = await statusRes.json()
          setCurrentStep(s.status)
          setProgress(s.progress ?? 0)

          if (s.status === 'recomputing') {
            setRetryCount(prev => prev + 1)
          }
        } catch {}
      }, 2000)

      // ✅ FIXED ANALYZE API
      const analyzeRes = await fetch(`${API_BASE}/api/analyze/${sessionId}`, {
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

        {status === 'idle' && (
          <div className="animate-fade-in">
            <FileUpload onUpload={handleUpload} />
          </div>
        )}

        {status === 'uploading' && (
          <div className="glass-card">
            <p>Uploading...</p>
          </div>
        )}

        {status === 'analyzing' && (
          <PipelineStatus
            steps={PIPELINE_STEPS}
            currentStep={currentStep}
            progress={progress}
          />
        )}

        {status === 'error' && (
          <div className="glass-card">
            <p>❌ {error}</p>
            <button onClick={handleReset}>Retry</button>
          </div>
        )}

        {status === 'complete' && report && (
          <>
            <ReportView report={report} />
            <ChartGallery charts={report.charts || []} />
            <InsightsPanel insights={report.insights || []} />

            <a
              href={`${API_BASE}/api/download/${report.session_id}`}
              download
            >
              Download CSV
            </a>
          </>
        )}

      </main>
    </div>
  )
}