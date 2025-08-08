# Use Node.js for building CSS assets
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source files
COPY . .

# Build CSS assets
RUN npm run build

# Use Python for the application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/index.html ./
COPY --from=builder /app/pyscript.json ./

# Copy Python files
COPY hello_world.py ./
COPY puepy-0.6.5-py3-none-any.whl ./

# Install Python dependencies
RUN pip install puepy-0.6.5-py3-none-any.whl

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Start the server
CMD ["python", "-m", "http.server", "8000"]
