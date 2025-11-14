import './AlertsPanel.css'

function AlertsPanel({ alerts }) {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'HIGH': return '#ef4444'
      case 'MEDIUM': return '#f97316'
      default: return '#64748b'
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'HIGH': return '🚨'
      case 'MEDIUM': return '⚠️'
      default: return 'ℹ️'
    }
  }

  return (
    <div className="alerts-panel">
      <div className="panel-header">
        <h3>🔔 Alertes Temps Réel</h3>
        <span className="alerts-count">{alerts.length}</span>
      </div>

      <div className="alerts-list">
        {alerts.length === 0 ? (
          <div className="no-alerts">
            <span>✅ Aucune alerte active</span>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div 
              key={index} 
              className="alert-item"
              style={{ borderLeftColor: getSeverityColor(alert.severity) }}
            >
              <div className="alert-header">
                <span className="alert-icon">{getSeverityIcon(alert.severity)}</span>
                <span className="alert-symbol">{alert.symbol}</span>
                <span 
                  className="alert-severity"
                  style={{ color: getSeverityColor(alert.severity) }}
                >
                  {alert.severity}
                </span>
              </div>
              <p className="alert-message">{alert.message}</p>
              <span className="alert-time">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default AlertsPanel