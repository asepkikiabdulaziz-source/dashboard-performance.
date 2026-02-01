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
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend from stage 1
COPY --from=build-stage /app/frontend/dist ./frontend/dist

# Set Environment Variables
# We set WORKDIR to /app/backend so local imports (auth, rbac) work
WORKDIR /app/backend
ENV PORT=8080
ENV PYTHONPATH=/app:/app/backend

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Command to run the application
# We are already in /app/backend, so we use main:app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
