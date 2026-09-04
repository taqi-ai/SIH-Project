# Multi-stage build for Railway deployment
# Backend: FastAPI
FROM python:3.12-slim as backend-builder

WORKDIR /app/backend

COPY backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY backend/ .

# Frontend: Next.js
FROM node:22-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json .
RUN npm ci

COPY frontend/ .
RUN npm run build

# Production runtime: Node + Python
FROM node:22-alpine

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy Python runtime from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend
COPY --from=backend-builder /app/backend /app/backend

# Copy frontend build
COPY --from=frontend-builder /app/frontend/.next /app/frontend/.next
COPY --from=frontend-builder /app/frontend/public /app/frontend/public
COPY frontend/package*.json /app/frontend/
RUN cd /app/frontend && npm ci --production

EXPOSE 3000 8000

# Start both services
CMD ["sh", "-c", "cd /app/frontend && npm start & cd /app/backend && gunicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
