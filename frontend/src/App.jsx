import { useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import PriceCard from './components/PriceCard'
import TechnicalIndicators from './components/TechnicalIndicators'
import AlertsPanel from './components/AlertsPanel'
import PriceChart from './components/PriceChart'
import { Activity, TrendingUp, TrendingDown, Menu, BarChart3, Bell, Trash2 } from 'lucide-react'

function App() {
  const [activeSection, setActiveSection] = useState('dashboard')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [priceData, setPriceData] = useState({
    BTCUSDT: { price: 0, change: 0, volume: 0, volatility: 0 },
    ETHUSDT: { price: 0, change: 0, volume: 0, volatility: 0 }
  })
  
  const [technicalData, setTechnicalData] = useState({
    BTCUSDT: { rsi: 0, macd: 0, bollingerUpper: 0, bollingerMiddle: 0, bollingerLower: 0 },
    ETHUSDT: { rsi: 0, macd: 0, bollingerUpper: 0, bollingerMiddle: 0, bollingerLower: 0 }
  })
  
  const [alerts, setAlerts] = useState([])
  const [priceHistory, setPriceHistory] = useState({ BTC: [], ETH: [] })
  const [isConnected, setIsConnected] = useState(false)
  const [sparkData, setSparkData] = useState({
    btc: { avg: 0, min: 0, max: 0, volatility: 0, count: 0 },
    eth: { avg: 0, min: 0, max: 0, volatility: 0, count: 0 }
  })
    const [alertForm, setAlertForm] = useState({
    name: '',
    conditions: [
      { symbol: 'BTCUSDT', type: 'price_above', threshold: '' }
    ],
    email: ''
  })

  // Charger les alertes existantes au démarrage
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/alerts')
        if (response.ok) {
          const data = await response.json()
          if (data.alerts && Array.isArray(data.alerts)) {
            setAlerts(data.alerts.map(alert => ({
              ...alert,
              createdAt: alert.createdAt || new Date().toLocaleString('fr-FR')
            })))
          }
        }
      } catch (error) {
        console.error('Erreur chargement alertes:', error)
      }
    }
    
    fetchAlerts()
    // Recharger toutes les 30 secondes pour synchroniser les statuts
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [])

  // Fonction pour supprimer une alerte
  const deleteAlert = async (alertId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/alerts/${alertId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        // Supprimer de l'état local seulement si la suppression API a réussi
        setAlerts(prev => prev.filter(a => a.id !== alertId))
        console.log(`🗑️ Alerte supprimée: ${alertId}`)
      } else {
        console.error('Erreur suppression alerte:', response.statusText)
        alert('Erreur lors de la suppression de l\'alerte')
      }
    } catch (error) {
      console.error('Erreur suppression alerte:', error)
      alert('Erreur réseau lors de la suppression')
    }
  }

  // Connexion WebSocket pour streaming temps réel avec reconnexion automatique
  useEffect(() => {
    let ws = null
    let reconnectTimeout = null
    let isUnmounted = false
    let pingInterval = null

    const connectWebSocket = () => {
      if (isUnmounted) return

      console.log('🚀 Connexion au WebSocket...')
      
      try {
        ws = new WebSocket('ws://localhost:8000/ws')
        
        ws.onopen = () => {
          console.log('✅ WebSocket connecté')
          setIsConnected(true)
          
          // Envoyer un ping toutes les 30 secondes pour garder la connexion active
          pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send('ping')
              console.log('📡 Ping envoyé')
            }
          }, 30000)
        }
        
        ws.onmessage = (event) => {
          try {
            if (event.data === 'pong') return
            
            const data = JSON.parse(event.data)
            console.log('📊 Données:', data)
            
            // Gestion des alertes déclenchées
            if (data.type === 'alert_triggered') {
              console.log('🚨 Alerte déclenchée:', data.alert_name)
              setAlerts(prev => prev.map(alert => 
                alert.id === data.alert_id || alert.name === data.alert_name
                  ? { ...alert, status: 'triggered' }
                  : alert
              ))
              return
            }
            
            if (data.type === 'price' && data.symbol && data.price) {
              setPriceData(prev => {
                const oldPrice = prev[data.symbol]?.price || data.price
                const changePercent = oldPrice !== 0 
                  ? parseFloat(((data.price - oldPrice) / oldPrice * 100).toFixed(2))
                  : 0

                return {
                  ...prev,
                  [data.symbol]: {
                    price: data.price,
                    change: changePercent,
                    volume: data.volume || 0,
                    volatility: 0
                  }
                }
              })
              
              const coin = data.symbol.replace('USDT', '')
              setPriceHistory(prev => {
                const currentHistory = prev[coin] || []
                const newHistory = [...currentHistory, { 
                  time: new Date().toLocaleTimeString('fr-FR', { 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                  }), 
                  price: data.price 
                }]
                return {
                  ...prev,
                  [coin]: newHistory.slice(-50)
                }
              })
            }
          } catch (error) {
            console.error('❌ Erreur parsing:', error)
          }
        }
        
        ws.onerror = (error) => {
          console.error('❌ WebSocket erreur:', error)
          setIsConnected(false)
        }
        
        ws.onclose = () => {
          console.log('🔌 WebSocket fermé')
          setIsConnected(false)
          
          // Nettoyer l'intervalle de ping
          if (pingInterval) {
            clearInterval(pingInterval)
            pingInterval = null
          }
          
          if (!isUnmounted) {
            console.log('🔄 Reconnexion dans 3s...')
            reconnectTimeout = setTimeout(connectWebSocket, 3000)
          }
        }
      } catch (error) {
        console.error('❌ Erreur connexion:', error)
        setIsConnected(false)
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connectWebSocket, 3000)
        }
      }
    }

    connectWebSocket()

    return () => {
      isUnmounted = true
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (pingInterval) clearInterval(pingInterval)
      if (ws) {
        ws.close()
      }
    }
  }, [])

  // Calcul des indicateurs techniques basés sur l'historique des prix
  useEffect(() => {
    const calculateIndicators = (history) => {
      if (!history || history.length < 14) {
        return { 
          rsi: 0, 
          macd: 0, 
          bollingerUpper: 0, 
          bollingerMiddle: 0, 
          bollingerLower: 0 
        }
      }
      
      const prices = history.map(h => h.price)
      const lastPrice = prices[prices.length - 1]
      
      // RSI simplifié (14 périodes)
      let gains = 0, losses = 0
      for (let i = 1; i < Math.min(14, prices.length); i++) {
        const change = prices[i] - prices[i - 1]
        if (change > 0) gains += change
        else losses -= change
      }
      const avgGain = gains / 14
      const avgLoss = losses / 14
      const rs = avgGain / (avgLoss || 1)
      const rsi = 100 - (100 / (1 + rs))
      
      // MACD simplifié
      const ema12 = prices.slice(-12).reduce((a, b) => a + b, 0) / 12
      const ema26 = prices.slice(-26).reduce((a, b) => a + b, 0) / Math.min(26, prices.length)
      const macd = ema12 - ema26
      
      // Bollinger Bands (20 périodes, 2 écarts-types)
      const period = Math.min(20, prices.length)
      const recentPrices = prices.slice(-period)
      const sma20 = recentPrices.reduce((a, b) => a + b, 0) / period
      const variance = recentPrices.reduce((sq, n) => sq + Math.pow(n - sma20, 2), 0) / period
      const stdDev = Math.sqrt(variance)
      const upperBand = sma20 + (2 * stdDev)
      const lowerBand = sma20 - (2 * stdDev)
      
      return { 
        rsi: rsi.toFixed(1), 
        macd: macd.toFixed(4), 
        bollingerUpper: upperBand.toFixed(2),
        bollingerMiddle: sma20.toFixed(2),
        bollingerLower: lowerBand.toFixed(2)
      }
    }
    
    if (priceHistory.BTC.length >= 14) {
      setTechnicalData(prev => ({
        ...prev,
        BTCUSDT: calculateIndicators(priceHistory.BTC)
      }))
    }
    
    if (priceHistory.ETH.length >= 14) {
      setTechnicalData(prev => ({
        ...prev,
        ETHUSDT: calculateIndicators(priceHistory.ETH)
      }))
    }
  }, [priceHistory])

  // Récupération des données Spark agrégées
  useEffect(() => {
    const fetchSparkData = async () => {
      try {
        // Simulation des données Spark (à remplacer par l'API réelle)
        if (priceHistory.BTC.length > 0) {
          const btcPrices = priceHistory.BTC.map(h => h.price)
          const btcAvg = btcPrices.reduce((a, b) => a + b, 0) / btcPrices.length
          const btcMin = Math.min(...btcPrices)
          const btcMax = Math.max(...btcPrices)
          const btcVolatility = ((btcMax - btcMin) / btcAvg * 100).toFixed(2)
          
          setSparkData(prev => ({
            ...prev,
            btc: {
              avg: btcAvg.toFixed(2),
              min: btcMin.toFixed(2),
              max: btcMax.toFixed(2),
              volatility: btcVolatility,
              count: btcPrices.length
            }
          }))
        }
        
        if (priceHistory.ETH.length > 0) {
          const ethPrices = priceHistory.ETH.map(h => h.price)
          const ethAvg = ethPrices.reduce((a, b) => a + b, 0) / ethPrices.length
          const ethMin = Math.min(...ethPrices)
          const ethMax = Math.max(...ethPrices)
          const ethVolatility = ((ethMax - ethMin) / ethAvg * 100).toFixed(2)
          
          setSparkData(prev => ({
            ...prev,
            eth: {
              avg: ethAvg.toFixed(2),
              min: ethMin.toFixed(2),
              max: ethMax.toFixed(2),
              volatility: ethVolatility,
              count: ethPrices.length
            }
          }))
        }
      } catch (error) {
        console.error('Erreur récupération Spark:', error)
      }
    }
    
    const interval = setInterval(fetchSparkData, 5000)
    fetchSparkData()
    
    return () => clearInterval(interval)
  }, [priceHistory])

  // Gestion des alertes
  const handleAlertSubmit = async (e) => {
    e.preventDefault()
    
    // Validation
    if (!alertForm.name) {
      alert('Veuillez donner un nom à votre alerte')
      return
    }
    if (!alertForm.email) {
      alert('Veuillez fournir un email')
      return
    }
    const hasValidCondition = alertForm.conditions.some(c => c.threshold !== '' || c.type.includes('macd_') || c.type.includes('bollinger_'))
    if (!hasValidCondition) {
      alert('Veuillez définir au moins une condition avec une valeur')
      return
    }
    
    // Filtrer les conditions valides
    const validConditions = alertForm.conditions.filter(c => 
      c.threshold !== '' || c.type.includes('macd_') || c.type.includes('bollinger_')
    )
    
    const newAlert = {
      name: alertForm.name,
      conditions: validConditions,
      email: alertForm.email
    }
    
    try {
      // Envoyer à l'API backend
      const response = await fetch('http://localhost:8000/api/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newAlert)
      })
      
      if (!response.ok) {
        throw new Error('Erreur lors de la création de l\'alerte')
      }
      
      const result = await response.json()
      
      // Ajouter à la liste locale
      setAlerts(prev => [...prev, {
        id: result.alert_id || Date.now(),
        ...newAlert,
        status: 'active',
        createdAt: new Date().toLocaleString('fr-FR')
      }])
      
      // Reset form
      setAlertForm({
        name: '',
        conditions: [{ symbol: 'BTCUSDT', type: 'price_above', threshold: '' }],
        email: ''
      })
      
      alert('✅ Alerte créée avec succès! Vous recevrez un email quand les conditions seront remplies.')
      
    } catch (error) {
      console.error('Erreur création alerte:', error)
      alert('❌ Erreur lors de la création de l\'alerte. Vérifiez que le backend est actif.')
    }
  }

  const addCondition = () => {
    setAlertForm(prev => ({
      ...prev,
      conditions: [...prev.conditions, { symbol: 'BTCUSDT', type: 'price_above', threshold: '' }]
    }))
  }

  const removeCondition = (index) => {
    setAlertForm(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }))
  }

  const updateCondition = (index, field, value) => {
    setAlertForm(prev => ({
      ...prev,
      conditions: prev.conditions.map((c, i) => 
        i === index ? { ...c, [field]: value } : c
      )
    }))
  }

  return (
    <div className="app">
      {/* Overlay pour fermer sidebar sur mobile */}
      <div 
        className={`sidebar-overlay ${isSidebarOpen ? 'active' : ''}`}
        onClick={() => setIsSidebarOpen(false)}
      ></div>
      
      <Sidebar 
        activeSection={activeSection} 
        setActiveSection={setActiveSection}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />
      
      <div className="main-content">
        <header className="app-header">
          {/* Bouton menu mobile */}
          <button 
            className="mobile-menu-btn"
            onClick={() => setIsSidebarOpen(true)}
            aria-label="Ouvrir le menu"
          >
            <Menu size={24} />
          </button>
          
          <div className="header-left">
            <h1>Crypto Trading Analytics</h1>
            <p className="subtitle">Analyse en temps réel avec Binance API</p>
          </div>
          <div className="header-right">
            <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
              <Activity size={16} />
              <span>{isConnected ? 'Connecté' : 'Déconnecté'}</span>
            </div>
          </div>
        </header>

        <main className="content">
          {activeSection === 'dashboard' && (
            <>
              {/* Section prix principaux */}
              <section className="section">
                <div className="section-header">
                  <TrendingUp size={24} />
                  <h2>Prix en Temps Réel</h2>
                </div>
                <div className="price-cards">
                  <PriceCard 
                    symbol="BTC"
                    data={priceData.BTCUSDT}
                  />
                  <PriceCard 
                    symbol="ETH"
                    data={priceData.ETHUSDT}
                  />
                </div>
              </section>

              {/* Graphiques de prix */}
              <section className="section">
                <div className="section-header">
                  <TrendingDown size={24} />
                  <h2>Graphiques</h2>
                </div>
                <div className="charts-grid">
                  <div className="chart-card">
                    <h3>Bitcoin (BTC)</h3>
                    <PriceChart data={priceHistory.BTC} color="#f7931a" />
                  </div>
                  <div className="chart-card">
                    <h3>Ethereum (ETH)</h3>
                    <PriceChart data={priceHistory.ETH} color="#627eea" />
                  </div>
                </div>
              </section>
            </>
          )}

          {activeSection === 'trading' && (
            <section className="section">
              <div className="section-header">
                <TrendingUp size={24} />
                <h2>Indicateurs Techniques</h2>
              </div>
              
              {/* Bitcoin Indicators */}
              <div className="trading-card">
                <div className="card-title">
                  <BarChart3 size={20} />
                  <h3>Bitcoin (BTC) - Indicateurs</h3>
                </div>
                <div className="indicators-grid">
                  <div className="indicator-item">
                    <span className="indicator-label">RSI (14):</span>
                    <span className={`indicator-value ${
                      technicalData.BTCUSDT.rsi > 70 ? 'overbought' : 
                      technicalData.BTCUSDT.rsi < 30 ? 'oversold' : 'neutral'
                    }`}>
                      {technicalData.BTCUSDT.rsi}
                    </span>
                    <span className={`indicator-signal ${
                      technicalData.BTCUSDT.rsi > 70 ? 'sell' : 
                      technicalData.BTCUSDT.rsi < 30 ? 'buy' : 'neutral'
                    }`}>
                      {technicalData.BTCUSDT.rsi > 70 ? 'Surachat' : 
                       technicalData.BTCUSDT.rsi < 30 ? 'Survente' : 'Neutre'}
                    </span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">MACD:</span>
                    <span className={`indicator-value ${technicalData.BTCUSDT.macd >= 0 ? 'bullish' : 'bearish'}`}>
                      {technicalData.BTCUSDT.macd}
                    </span>
                    <span className={`indicator-signal ${technicalData.BTCUSDT.macd >= 0 ? 'buy' : 'sell'}`}>
                      {technicalData.BTCUSDT.macd >= 0 ? 'Haussier' : 'Baissier'}
                    </span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">Bollinger Sup:</span>
                    <span className="indicator-value">${technicalData.BTCUSDT.bollingerUpper}</span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">Bollinger Moy:</span>
                    <span className="indicator-value">${technicalData.BTCUSDT.bollingerMiddle}</span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">Bollinger Inf:</span>
                    <span className="indicator-value">${technicalData.BTCUSDT.bollingerLower}</span>
                  </div>
                </div>
              </div>

              {/* Ethereum Indicators */}
              <div className="trading-card">
                <div className="card-title">
                  <BarChart3 size={20} />
                  <h3>Ethereum (ETH) - Indicateurs</h3>
                </div>
                <div className="indicators-grid">
                  <div className="indicator-item">
                    <span className="indicator-label">RSI (14):</span>
                    <span className={`indicator-value ${
                      technicalData.ETHUSDT.rsi > 70 ? 'overbought' : 
                      technicalData.ETHUSDT.rsi < 30 ? 'oversold' : 'neutral'
                    }`}>
                      {technicalData.ETHUSDT.rsi}
                    </span>
                    <span className={`indicator-signal ${
                      technicalData.ETHUSDT.rsi > 70 ? 'sell' : 
                      technicalData.ETHUSDT.rsi < 30 ? 'buy' : 'neutral'
                    }`}>
                      {technicalData.ETHUSDT.rsi > 70 ? 'Surachat' : 
                       technicalData.ETHUSDT.rsi < 30 ? 'Survente' : 'Neutre'}
                    </span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">MACD:</span>
                    <span className={`indicator-value ${technicalData.ETHUSDT.macd >= 0 ? 'bullish' : 'bearish'}`}>
                      {technicalData.ETHUSDT.macd}
                    </span>
                    <span className={`indicator-signal ${technicalData.ETHUSDT.macd >= 0 ? 'buy' : 'sell'}`}>
                      {technicalData.ETHUSDT.macd >= 0 ? 'Haussier' : 'Baissier'}
                    </span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">Bollinger Sup:</span>
                    <span className="indicator-value">${technicalData.ETHUSDT.bollingerUpper}</span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">Bollinger Moy:</span>
                    <span className="indicator-value">${technicalData.ETHUSDT.bollingerMiddle}</span>
                  </div>
                  
                  <div className="indicator-item">
                    <span className="indicator-label">Bollinger Inf:</span>
                    <span className="indicator-value">${technicalData.ETHUSDT.bollingerLower}</span>
                  </div>
                </div>
              </div>

              <div className="trading-info">
                <div className="info-item">
                  <Activity size={18} />
                  <p><strong>RSI:</strong> Indice de Force Relative (30=survente, 70=surachat)</p>
                </div>
                <div className="info-item">
                  <TrendingUp size={18} />
                  <p><strong>MACD:</strong> Convergence/Divergence de moyennes mobiles</p>
                </div>
                <div className="info-item">
                  <BarChart3 size={18} />
                  <p><strong>Bollinger:</strong> Bandes de volatilité (écart-type)</p>
                </div>
              </div>
            </section>
          )}

          {activeSection === 'analytics' && (
            <section className="section">
              <div className="section-header">
                <BarChart3 size={24} />
                <h2>Analytics - Traitement Spark</h2>
              </div>
              
              <div className="analytics-grid">
                <div className="analytics-card">
                  <div className="card-title">
                    <Activity size={20} />
                    <h3>Bitcoin (BTC) - Analyse</h3>
                  </div>
                  <div className="analytics-stats">
                    <div className="stat-row">
                      <TrendingUp size={16} className="stat-icon" />
                      <span className="stat-label">Prix Moyen:</span>
                      <span className="stat-value">${sparkData.btc.avg}</span>
                    </div>
                    <div className="stat-row">
                      <TrendingDown size={16} className="stat-icon down" />
                      <span className="stat-label">Prix Min:</span>
                      <span className="stat-value">${sparkData.btc.min}</span>
                    </div>
                    <div className="stat-row">
                      <TrendingUp size={16} className="stat-icon up" />
                      <span className="stat-label">Prix Max:</span>
                      <span className="stat-value">${sparkData.btc.max}</span>
                    </div>
                    <div className="stat-row">
                      <Activity size={16} className="stat-icon highlight" />
                      <span className="stat-label">Volatilité:</span>
                      <span className="stat-value highlight">{sparkData.btc.volatility}%</span>
                    </div>
                    <div className="stat-row">
                      <BarChart3 size={16} className="stat-icon" />
                      <span className="stat-label">Nb de trades:</span>
                      <span className="stat-value">{sparkData.btc.count}</span>
                    </div>
                  </div>
                </div>

                <div className="analytics-card">
                  <div className="card-title">
                    <Activity size={20} />
                    <h3>Ethereum (ETH) - Analyse</h3>
                  </div>
                  <div className="analytics-stats">
                    <div className="stat-row">
                      <TrendingUp size={16} className="stat-icon" />
                      <span className="stat-label">Prix Moyen:</span>
                      <span className="stat-value">${sparkData.eth.avg}</span>
                    </div>
                    <div className="stat-row">
                      <TrendingDown size={16} className="stat-icon down" />
                      <span className="stat-label">Prix Min:</span>
                      <span className="stat-value">${sparkData.eth.min}</span>
                    </div>
                    <div className="stat-row">
                      <TrendingUp size={16} className="stat-icon up" />
                      <span className="stat-label">Prix Max:</span>
                      <span className="stat-value">${sparkData.eth.max}</span>
                    </div>
                    <div className="stat-row">
                      <Activity size={16} className="stat-icon highlight" />
                      <span className="stat-label">Volatilité:</span>
                      <span className="stat-value highlight">{sparkData.eth.volatility}%</span>
                    </div>
                    <div className="stat-row">
                      <BarChart3 size={16} className="stat-icon" />
                      <span className="stat-label">Nb de trades:</span>
                      <span className="stat-value">{sparkData.eth.count}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="analytics-info">
                <div className="info-item">
                  <Activity size={18} />
                  <p><strong>Traitement Spark:</strong> Ces statistiques sont calculées en temps réel par Apache Spark à partir du stream Kafka.</p>
                </div>
                <div className="info-item">
                  <TrendingUp size={18} />
                  <p><strong>Volatilité:</strong> Indique l'amplitude des variations de prix sur la période observée.</p>
                </div>
              </div>
            </section>
          )}

          {activeSection === 'alerts' && (
            <section className="section">
              <div className="section-header">
                <Bell size={24} />
                <h2>Système d'Alertes Avancées</h2>
              </div>

              {/* Formulaire de création d'alerte */}
              <div className="alert-form-card">
                <div className="card-title">
                  <Bell size={20} />
                  <h3>Créer une nouvelle alerte</h3>
                </div>
                <form onSubmit={handleAlertSubmit} className="alert-form-advanced">
                  <div className="form-row">
                    <div className="form-group full-width">
                      <label>Nom de l'alerte</label>
                      <input
                        type="text"
                        value={alertForm.name}
                        onChange={(e) => setAlertForm({...alertForm, name: e.target.value})}
                        placeholder="Ex: Volatilité BTC élevée + RSI survente"
                        required
                      />
                    </div>

                    <div className="form-group full-width">
                      <label>Email de notification</label>
                      <input
                        type="email"
                        value={alertForm.email}
                        onChange={(e) => setAlertForm({...alertForm, email: e.target.value})}
                        placeholder="votre@email.com"
                        required
                      />
                    </div>
                  </div>

                  {/* Conditions multiples */}
                  <div className="conditions-section">
                    <div className="conditions-header">
                      <h4>Conditions de déclenchement (flexibles)</h4>
                      <button 
                        type="button" 
                        className="btn-add-condition"
                        onClick={addCondition}
                      >
                        <Activity size={16} />
                        +
                      </button>
                    </div>

                    {alertForm.conditions.map((condition, index) => (
                      <div key={index} className="condition-row-flexible">
                        <div className="condition-number">{index + 1}</div>
                        
                        <div className="form-group">
                          <label>Cryptomonnaie</label>
                          <select 
                            value={condition.symbol}
                            onChange={(e) => updateCondition(index, 'symbol', e.target.value)}
                          >
                            <option value="BTCUSDT">Bitcoin (BTC)</option>
                            <option value="ETHUSDT">Ethereum (ETH)</option>
                          </select>
                        </div>

                        <div className="form-group">
                          <label>Type de condition</label>
                          <select 
                            value={condition.type}
                            onChange={(e) => updateCondition(index, 'type', e.target.value)}
                          >
                            <optgroup label="Prix">
                              <option value="price_above">Prix supérieur à</option>
                              <option value="price_below">Prix inférieur à</option>
                            </optgroup>
                            <optgroup label="Indicateurs techniques">
                              <option value="rsi_above">RSI supérieur à</option>
                              <option value="rsi_below">RSI inférieur à (survente)</option>
                              <option value="macd_positive">MACD positif (haussier)</option>
                              <option value="macd_negative">MACD négatif (baissier)</option>
                              <option value="bollinger_upper">Prix touche Bollinger supérieur</option>
                              <option value="bollinger_lower">Prix touche Bollinger inférieur</option>
                            </optgroup>
                            <optgroup label="Volatilité & Volume">
                              <option value="volatility_above">Volatilité supérieure à</option>
                              <option value="volatility_below">Volatilité inférieure à</option>
                              <option value="volume_above">Volume supérieur à</option>
                            </optgroup>
                          </select>
                        </div>

                        <div className="form-group">
                          <label>
                            Seuil 
                            {condition.type.includes('price') && ' (USD)'}
                            {condition.type.includes('rsi') && ' (0-100)'}
                            {condition.type.includes('volatility') && ' (%)'}
                            {condition.type.includes('volume') && ' (USD)'}
                            {(condition.type.includes('macd_') || condition.type.includes('bollinger_')) && ' (auto)'}
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            value={condition.threshold}
                            onChange={(e) => updateCondition(index, 'threshold', e.target.value)}
                            placeholder={
                              condition.type.includes('price') ? "Ex: 105000" :
                              condition.type.includes('rsi') ? "Ex: 30 (survente)" :
                              condition.type.includes('volatility') ? "Ex: 0.2" :
                              condition.type.includes('volume') ? "Ex: 1000000" :
                              condition.type.includes('macd_') ? "Pas de seuil requis" :
                              condition.type.includes('bollinger_') ? "Pas de seuil requis" :
                              "Valeur"
                            }
                            disabled={condition.type.includes('macd_') || condition.type.includes('bollinger_')}
                          />
                        </div>

                        {alertForm.conditions.length > 1 && (
                          <button 
                            type="button"
                            className="btn-remove-condition"
                            onClick={() => removeCondition(index)}
                            title="Supprimer cette condition"
                          >
                            <Trash2 size={18} />
                          </button>
                        )}
                      </div>
                    ))}

                    <p className="conditions-note">
                      <Activity size={14} />
                      Chaque condition peut cibler une crypto différente. Toutes les conditions doivent être remplies simultanément.
                    </p>
                  </div>

                  <button type="submit" className="btn-primary btn-submit">
                    <Bell size={18} />
                    Créer l'alerte
                  </button>
                </form>
              </div>

              {/* Liste des alertes */}
              <div className="alerts-list">
                <h3>
                  <Bell size={20} />
                  Mes alertes actives ({alerts.length})
                </h3>
                {alerts.length === 0 ? (
                  <p className="no-alerts">
                    <Activity size={24} />
                    Aucune alerte configurée. Créez-en une ci-dessus!
                  </p>
                ) : (
                  <div className="alerts-grid">
                    {alerts.map(alert => (
                      <div key={alert.id} className={`alert-item ${alert.status}`}>
                        <div className="alert-header">
                          <div className="alert-title">
                            <Bell size={16} />
                            <span className="alert-name">{alert.name}</span>
                          </div>
                          <span className={`alert-status ${alert.status}`}>
                            {alert.status === 'active' ? 'Active' : 'Déclenchée'}
                          </span>
                        </div>
                        <div className="alert-body">
                          <div className="alert-conditions">
                            <strong>
                              <Activity size={14} />
                              Conditions ({alert.conditions.length}):
                            </strong>
                            <ul>
                              {alert.conditions.map((cond, i) => (
                                <li key={i}>
                                  <span className="condition-symbol">{cond.symbol}</span>
                                  {' → '}
                                  {cond.type.replace(/_/g, ' ')}
                                  {cond.threshold && ` : ${cond.threshold}`}
                                  {cond.type.includes('volatility') && cond.threshold && '%'}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <p>
                            <Bell size={14} />
                            <strong>Email:</strong> {alert.email}
                          </p>
                          <p className="alert-date">Créée le {alert.createdAt}</p>
                        </div>
                        <button 
                          className="btn-delete"
                          onClick={() => deleteAlert(alert.id)}
                        >
                          <TrendingDown size={16} />
                          Supprimer
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
