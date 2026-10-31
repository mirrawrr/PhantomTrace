FROM node:22-bookworm-slim AS dashboard
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src
RUN npm run build

FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PHANTOMTRACE_STATIC_DIR=/app/static PORT=8000
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 phantomtrace
COPY backend/app ./app
COPY --from=dashboard /build/dist ./static
USER 10001
EXPOSE 8000
CMD ["python", "-m", "app.serve"]
