import { 
  Home, 
  TrendingUp, 
  BarChart3, 
  Bell,
  Settings,
  X
} from 'lucide-react'
import './Sidebar.css'

function Sidebar({ activeSection, setActiveSection, isOpen, onClose }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'trading', label: 'Trading', icon: TrendingUp },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'alerts', label: 'Alertes', icon: Bell },
  ]

  const handleItemClick = (id) => {
    setActiveSection(id)
    if (onClose) onClose() // Fermer sur mobile
  }

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <TrendingUp size={32} />
          <span>CryptoLive</span>
        </div>
        <button className="close-btn" onClick={onClose} aria-label="Fermer le menu">
          <X size={24} />
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map(item => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
              onClick={() => handleItemClick(item.id)}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="nav-item">
          <Settings size={20} />
          <span>Paramètres</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar