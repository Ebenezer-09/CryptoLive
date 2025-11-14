import './TechnicalIndicators.css'

function TechnicalIndicators({ symbol, data }) {
  const getRSIStatus = (rsi) => {
    if (rsi > 70) return { label: 'Surachat', color: '#ef4444' }
    if (rsi < 30) return { label: 'Survente', color: '#10b981' }
    return { label: 'Neutre', color: '#64748b' }
  }

  const getMACDSignal = (macd) => {
    if (macd > 0) return { label: '🚀 Haussier', color: '#10b981' }
    return { label: '📉 Baissier', color: '#ef4444' }
  }

  const getBBStatus = (bbPos) => {
    if (bbPos > 0.8) return { label: 'Suracheté', color: '#ef4444' }
    if (bbPos < 0.2) return { label: 'Survendu', color: '#10b981' }
    return { label: 'Normal', color: '#64748b' }
  }

  const rsiStatus = getRSIStatus(data.rsi)
  const macdSignal = getMACDSignal(data.macd)
  const bbStatus = getBBStatus(data.bb_position)

  return (
    <div className="technical-indicators">
      <div className="indicators-header">
        <h3>{symbol} - Indicateurs</h3>
      </div>

      <div className="indicator-item">
        <div className="indicator-info">
          <span className="indicator-label">RSI (14)</span>
          <span className="indicator-status" style={{ color: rsiStatus.color }}>
            {rsiStatus.label}
          </span>
        </div>
        <div className="indicator-value-bar">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ 
                width: `${data.rsi || 0}%`, 
                background: rsiStatus.color 
              }}
            />
          </div>
          <span className="indicator-number">{(data.rsi || 0).toFixed(1)}</span>
        </div>
      </div>

      <div className="indicator-item">
        <div className="indicator-info">
          <span className="indicator-label">MACD</span>
          <span className="indicator-status" style={{ color: macdSignal.color }}>
            {macdSignal.label}
          </span>
        </div>
        <div className="indicator-value">
          <span className="indicator-number" style={{ color: macdSignal.color }}>
            {(data.macd || 0).toFixed(4)}
          </span>
        </div>
      </div>

      <div className="indicator-item">
        <div className="indicator-info">
          <span className="indicator-label">Bollinger Bands</span>
          <span className="indicator-status" style={{ color: bbStatus.color }}>
            {bbStatus.label}
          </span>
        </div>
        <div className="indicator-value-bar">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ 
                width: `${(data.bb_position || 0) * 100}%`, 
                background: bbStatus.color 
              }}
            />
          </div>
          <span className="indicator-number">{((data.bb_position || 0) * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  )
}

export default TechnicalIndicators