FROM node:20-alpine AS dashboard-builder
WORKDIR /app
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci
COPY dashboard/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements.txt && apt-get purge -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
COPY *.py .env.example ./
COPY --from=dashboard-builder /app/out/ ./dashboard/out/
EXPOSE 8000
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
