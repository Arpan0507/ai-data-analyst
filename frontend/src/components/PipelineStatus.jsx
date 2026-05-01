export default function PipelineStatus({ steps, currentStep, progress, complete }) {
  const getStepStatus = (stepKey) => {
    if (complete) return 'complete'
    const currentIdx = steps.findIndex(s => s.key === currentStep)
    const stepIdx = steps.findIndex(s => s.key === stepKey)
    if (stepIdx < currentIdx) return 'complete'
    if (stepIdx === currentIdx) return 'active'
    return 'pending'
  }

  return (
    <div style={{ marginBottom: '1rem' }}>
      <div className="pipeline-steps">
        {steps.map((step, i) => (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div className={`pipeline-step ${getStepStatus(step.key)}`}>
              <span>{step.icon}</span>
              <span>{step.label}</span>
            </div>
            {i < steps.length - 1 && <div className="pipeline-connector"></div>}
          </div>
        ))}
      </div>
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{ width: `${Math.round(progress * 100)}%` }}
        ></div>
      </div>
    </div>
  )
}
