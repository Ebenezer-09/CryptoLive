# ============================================
# FRONTEND REACT - Development Mode
# ============================================
# Utilisation de Node.js 20 (requis par Vite 20.19+)
FROM node:20-alpine

WORKDIR /app

# Copier package.json et installer toutes les dependances
COPY package*.json ./
RUN npm install

# Copier tout le code
COPY . .

# Exposer le port
EXPOSE 5173

# Demarrer en mode developpement
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
