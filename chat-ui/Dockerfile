# Use the official Node.js 18 image (not Alpine to avoid native module issues)
FROM node:18-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the Next.js application
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
# Default to localhost for development, will be overridden by docker-compose
ENV NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000

# Start the application
CMD ["npm", "start"]
