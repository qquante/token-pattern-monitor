FROM node:20-slim

WORKDIR /app

# Copiar package.json e instalar dependencias
COPY package.json .
RUN npm install

# Copiar codigo
COPY monitor.js .

# Rodar monitor
CMD ["node", "monitor.js"]
