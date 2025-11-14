# ============================================
# FRONTEND REACT - Production Build
# ============================================
FROM node:18-alpine

WORKDIR /app

# Copier package.json et installer dépendances
COPY package*.json ./
RUN npm ci --only=production

# Copier tout le code
COPY . .

# Builder l'application React
RUN npm run build

# Installer serve pour servir le build
RUN npm install -g serve

# Exposer le port
EXPOSE 5173

# Démarrer le serveur
CMD ["serve", "-s", "dist", "-l", "5173"]
