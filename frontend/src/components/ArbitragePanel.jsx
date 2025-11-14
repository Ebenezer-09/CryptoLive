import './ArbitragePanel.css'

function ArbitragePanel({ opportunities }) {
  return (
    <div className="arbitrage-panel">
      <div className="panel-header">
        <h3>💱 Opportunités d'Arbitrage</h3>
        <span className="opps-count">{opportunities.length}</span>
      </div>

      <div className="arbitrage-list">
        {opportunities.length === 0 ? (
          <div className="no-opportunities">
            <span>🔍 Aucune opportunité détectée</span>
          </div>
        ) : (
          opportunities.map((opp, index) => (
            <div key={index} className="arbitrage-item">
              <div className="arb-header">
                <span className="arb-symbol">{opp.symbol}</span>
                <span className="arb-profit">
                  +{opp.arbitrage_percentage?.toFixed(2)}%
                </span>
              </div>

              <div className="arb-details">
                <div className="arb-exchange">
                  <span className="exchange-label">Acheter</span>
                  <span className="exchange-name">{opp.buy_exchange}</span>
                  <span className="exchange-price">${opp.buy_price?.toFixed(2)}</span>
                </div>

                <div className="arb-arrow">→</div>

                <div className="arb-exchange">
                  <span className="exchange-label">Vendre</span>
                  <span className="exchange-name">{opp.sell_exchange}</span>
                  <span className="exchange-price">${opp.sell_price?.toFixed(2)}</span>
                </div>
              </div>

              <div className="arb-potential">
                <span>Profit potentiel: ${opp.potential_profit_usd?.toFixed(2)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default ArbitragePanel