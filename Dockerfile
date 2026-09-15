# Single-container deploy for Render/Railway: Next.js frontend (public port)
# proxies /api/* to a FastAPI backend running on an internal port.
# Uses one consistent Debian base throughout to avoid glibc/musl ABI mismatches
# between pip-installed native wheels (psycopg2, etc.) and the runtime image.

# Stage 1: build the Next.js frontend
FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

# Baked in at build time: browser calls same-origin /api/*, proxied by next.config.mjs
ENV NEXT_PUBLIC_API_BASE=/api
RUN npm run build

# Stage 2: production runtime (Node + Python, same Debian base as builder)
FROM node:22-bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend: install deps into a venv using this image's own Python (no cross-image copy)
COPY backend/requirements-prod.txt /app/backend/requirements-prod.txt
RUN python3 -m venv /app/backend/venv && \
    /app/backend/venv/bin/pip install --no-cache-dir -r /app/backend/requirements-prod.txt
COPY backend/ /app/backend/

# Frontend: runtime deps + built output
COPY frontend/package*.json /app/frontend/
COPY --from=frontend-builder /app/frontend/.next /app/frontend/.next
COPY --from=frontend-builder /app/frontend/public /app/frontend/public
RUN cd /app/frontend && npm ci --omit=dev

# Frontend is the only publicly routed port - Render/Railway inject $PORT for
# it, and that value varies per service (whatever the host assigned, often the
# same port an earlier iteration of this service used for something else).
# The backend's internal port must NOT be a value $PORT could ever collide
# with, or the frontend (the container's foreground/main process) fails to
# bind and the whole container crash-loops. 8811 is deliberately unlikely to
# ever be assigned as a public $PORT.
ENV BACKEND_PORT=8811
EXPOSE 3000

CMD ["sh", "-c", "cd /app/backend && ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port ${BACKEND_PORT} & cd /app/frontend && npm start -- -p ${PORT:-3000}"]
