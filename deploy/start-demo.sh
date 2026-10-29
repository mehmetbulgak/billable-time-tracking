#!/bin/sh
set -eu

# Disposable sample data: the database is private to this single demo container.
install -d -m 700 -o postgres -g postgres "$PGDATA"
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    runuser -u postgres -- initdb -D "$PGDATA" --auth=trust --encoding=UTF8 --no-locale >/dev/null
fi
runuser -u postgres -- pg_ctl -D "$PGDATA" -l /tmp/billable-postgres.log \
    -o "-h 127.0.0.1 -c unix_socket_directories=/tmp -c shared_buffers=16MB -c max_connections=25" \
    -w start

export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_urlsafe(64))')}"
if ! runuser -u postgres -- psql -h 127.0.0.1 -tAc "SELECT 1 FROM pg_database WHERE datname='billable'" | grep -q 1; then
    runuser -u postgres -- createdb -h 127.0.0.1 billable
fi
runuser -u app -- python manage.py migrate --noinput
runuser -u app -- python manage.py seed_demo --reset
# The public demo must never grant access to Django administration.
runuser -u app -- python manage.py shell -c \
    'from apps.accounts.models import User; User.objects.update(is_staff=False, is_superuser=False)'

runuser -u app -- daphne --bind 0.0.0.0 --port "$PORT" --proxy-headers config.asgi:application &
api_pid=$!
trap 'kill -TERM "$api_pid" 2>/dev/null || true; runuser -u postgres -- pg_ctl -D "$PGDATA" -m fast -w stop' TERM INT EXIT
wait "$api_pid"
