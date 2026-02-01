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
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source DIRECTLY to /app
COPY backend/ .

# Copy built frontend to /app/dist
COPY --from=build-stage /app/frontend/dist ./dist

# Set Environment Variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Command to run the application via our diagnostic bootstrap
# This ensures we see full tracebacks if imports fail
CMD ["python", "bootstrap.py"]
