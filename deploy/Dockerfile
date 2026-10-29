FROM node:22-bookworm-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_DEMO_MODE=true
RUN npm run build

FROM python:3.13-slim-bookworm AS python-builder
RUN python -m venv /opt/venv
COPY backend/requirements/base.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:/usr/lib/postgresql/15/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.demo \
    DATABASE_URL=postgres://app@localhost/billable \
    PGDATA=/tmp/billable-postgres \
    PORT=10000
RUN apt-get update \
    && apt-get install --no-install-recommends -y postgresql-15 postgresql-contrib ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home app
WORKDIR /app
COPY --from=python-builder /opt/venv /opt/venv
COPY backend/ ./
COPY --from=frontend /frontend/dist/ ./frontend_dist/
COPY deploy/start-demo.sh /usr/local/bin/start-demo
RUN chmod +x /usr/local/bin/start-demo \
    && DJANGO_SETTINGS_MODULE=config.settings.build python manage.py collectstatic --noinput
EXPOSE 10000
CMD ["/usr/local/bin/start-demo"]
