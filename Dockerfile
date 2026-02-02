# ==========================================
# STAGE 1: Build Frontend (Vite)
# ==========================================
FROM node:20-alpine AS build-stage
WORKDIR /app/frontend

# Copy frontend source
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Final Production Image
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend source DIRECTLY to /app
COPY backend/ .

# Copy built frontend to /app/dist
COPY --from=build-stage /app/frontend/dist ./dist

# Set Environment Variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Command to run the application
# Use gunicorn for production (better for Cloud Run)
# Fallback to uvicorn if gunicorn not available
CMD ["sh", "-c", "if command -v gunicorn > /dev/null; then gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 300; else uvicorn main:app --host 0.0.0.0 --port $PORT; fi"]
