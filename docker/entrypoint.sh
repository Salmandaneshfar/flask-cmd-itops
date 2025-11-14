#!/bin/sh
set -e

# Ensure writable directories exist
mkdir -p /app/instance /app/static/uploads /app/logs

# Touch SQLite DB file if using default path to avoid permission issues
if [ -n "${DATABASE_URL}" ] && printf '%s' "$DATABASE_URL" | grep -q '^sqlite:'; then
    db_path=$(printf '%s' "$DATABASE_URL" | sed 's|^sqlite:/*||')
    if [ -n "$db_path" ]; then
        mkdir -p "$(dirname "$db_path")"
        touch "$db_path"
    fi
fi

exec "$@"



