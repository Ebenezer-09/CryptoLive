import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import './PriceChart.css'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

function PriceChart({ data, color }) {
  // Vérification de sécurité et limitation des données
  const safeData = Array.isArray(data) ? data : []
  const limitedData = safeData.slice(-50)
  
  // Si pas de données, afficher un message
  if (limitedData.length === 0) {
    return (
      <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <p style={{ color: '#94a3b8' }}>En attente de données...</p>
      </div>
    )
  }
  
  const chartData = {
    labels: limitedData.map(d => d.time || ''),
    datasets: [
      {
        label: 'Prix',
        data: limitedData.map(d => d.price || 0),
        borderColor: color,
        backgroundColor: `${color}20`,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: color,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2,
      }
    ]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 300, // Animation plus rapide et douce
      easing: 'easeInOutQuad'
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: '#1e293b',
        titleColor: '#f1f5f9',
        bodyColor: '#cbd5e1',
        borderColor: '#334155',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: function(context) {
            return `$${context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: '#334155',
          drawTicks: false
        },
        ticks: {
          color: '#94a3b8',
          maxTicksLimit: 10
        }
      },
      y: {
        display: true,
        grid: {
          color: '#334155',
          drawTicks: false
        },
        ticks: {
          color: '#94a3b8',
          callback: function(value) {
            return '$' + value.toLocaleString()
          }
        },
        // Fixer les limites min/max pour éviter les sauts brusques
        suggestedMin: limitedData.length > 0 ? Math.min(...limitedData.map(d => d.price)) * 0.9995 : undefined,
        suggestedMax: limitedData.length > 0 ? Math.max(...limitedData.map(d => d.price)) * 1.0005 : undefined,
        // Activer l'animation douce
        beginAtZero: false
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  }

  return (
    <div className="chart-container">
      <div className="price-chart">
        <Line data={chartData} options={options} />
      </div>
    </div>
  )
}

export default PriceChart