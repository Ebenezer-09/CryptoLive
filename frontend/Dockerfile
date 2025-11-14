# ============================================
# FRONTEND REACT - Development Mode
# ============================================
FROM node:18-alpine

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
