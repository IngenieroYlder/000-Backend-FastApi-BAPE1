FROM node:18-slim

# Install necessary libraries for libsignal-node / canvas
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Explicitly expose the port from .env
EXPOSE 3005

CMD ["node", "server.js"]
