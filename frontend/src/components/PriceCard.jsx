import { useEffect, useRef } from 'react'
import './PriceCard.css'

function PriceCard({ symbol, data }) {
  const prevPriceRef = useRef(data?.price || 0)
  const priceChangeClass = data?.price > prevPriceRef.current ? 'price-up' : 
                          data?.price < prevPriceRef.current ? 'price-down' : ''
  
  useEffect(() => {
    if (data?.price) {
      prevPriceRef.current = data.price
    }
  }, [data?.price])

  const formatPrice = (price) => {
    if (!price || isNaN(price)) return '$0.00'
    return `$${Number(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatChange = (change) => {
    if (!change || isNaN(change) || change === 0) return '' // Ne rien afficher si 0
    const numChange = Number(change)
    const sign = numChange >= 0 ? '+' : ''
    return `${sign}${numChange.toFixed(2)}%`
  }

  // Valeurs par défaut sécurisées
  const safeData = {
    price: data?.price || 0,
    change: data?.change || 0,
    volume: data?.volume || 0,
    volatility: data?.volatility || 0
  }

  return (
    <div className="price-card">
      <div className="price-card-header">
        <div className="symbol-info">
          <span className="symbol-icon">{symbol === 'BTC' ? '₿' : 'Ξ'}</span>
          <div>
            <h3>{symbol}</h3>
            <span className="symbol-name">{symbol === 'BTC' ? 'Bitcoin' : 'Ethereum'}</span>
          </div>
        </div>
      </div>

      <div className={`price-main ${priceChangeClass}`}>
        <span className="price-value">{formatPrice(safeData.price)}</span>
        {safeData.change !== 0 && (
          <span className={`price-change ${safeData.change >= 0 ? 'positive' : 'negative'}`}>
            {formatChange(safeData.change)}
          </span>
        )}
      </div>

      <div className="price-stats">
        <div className="stat-item">
          <span className="stat-label">Volume (5min)</span>
          <span className="stat-value">{safeData.volume}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Volatilité</span>
          <span className="stat-value">{safeData.volatility.toFixed(4)}</span>
        </div>
      </div>
    </div>
  )
}

export default PriceCard