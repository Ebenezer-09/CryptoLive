import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = {
  // Health check
  health: () => axios.get(`${API_BASE_URL}/health`),
  
  // Latest data (données temps réel)
  getLatest: () => axios.get(`${API_BASE_URL}/api/latest`),
  
  // Root endpoint
  getRoot: () => axios.get(`${API_BASE_URL}/`),
};

// WebSocket connection
export class BinanceWebSocket {
  constructor(onMessage, onError) {
    this.ws = null;
    this.onMessage = onMessage;
    this.onError = onError;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    try {
      this.ws = new WebSocket('ws://localhost:8000/ws');
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connecté');
        this.reconnectAttempts = 0;
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket erreur:', error);
        if (this.onError) this.onError(error);
      };
      
      this.ws.onclose = () => {
        console.log('🔌 WebSocket déconnecté');
        this.reconnect();
      };
    } catch (error) {
      console.error('Erreur connexion WebSocket:', error);
      this.reconnect();
    }
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Reconnexion tentative ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export default api;