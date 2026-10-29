#!/bin/sh
set -eu

install -d -m 700 -o postgres -g postgres "$PGDATA"
install -d -m 755 -o postgres -g postgres /run/postgresql/billable
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    runuser -u postgres -- initdb -D "$PGDATA" --auth-local=peer --auth-host=scram-sha-256 --encoding=UTF8 --no-locale >/dev/null
fi
runuser -u postgres -- pg_ctl -D "$PGDATA" -l /tmp/billable-postgres.log \
    -o "-h '' -c unix_socket_directories=/run/postgresql/billable -c shared_buffers=16MB -c max_connections=25" \
    -w start

export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
if ! runuser -u postgres -- psql -h /run/postgresql/billable -tAc "SELECT 1 FROM pg_roles WHERE rolname='app'" | grep -q 1; then
    runuser -u postgres -- createuser -h /run/postgresql/billable app
fi
if ! runuser -u postgres -- psql -h /run/postgresql/billable -tAc "SELECT 1 FROM pg_database WHERE datname='billable'" | grep -q 1; then
    runuser -u postgres -- createdb -h /run/postgresql/billable --owner app billable
fi
runuser -u postgres -- psql -h /run/postgresql/billable --dbname billable -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS btree_gist'
runuser -u app -- python manage.py migrate --noinput
runuser -u app -- python manage.py seed_demo --reset

runuser -u app -- uvicorn config.asgi:application --host 0.0.0.0 --port "$PORT" --no-proxy-headers --ws-max-size 4096 --ws-max-queue 4 --ws-per-message-deflate false &
api_pid=$!
trap 'kill -TERM "$api_pid" 2>/dev/null || true; runuser -u postgres -- pg_ctl -D "$PGDATA" -m fast -w stop' TERM INT EXIT
wait "$api_pid"
