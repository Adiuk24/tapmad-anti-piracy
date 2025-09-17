#!/usr/bin/env bash
set -euo pipefail

: "${PGHOST:=postgres}"
: "${PGPORT:=5432}"
: "${PGDATABASE:=antipiracy}"
: "${PGUSER:=postgres}"
: "${PGPASSWORD:=postgres}"

export PGPASSWORD

echo "Waiting for Postgres at ${PGHOST}:${PGPORT}..."
until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" >/dev/null 2>&1; do
  sleep 1
done

echo "Applying migrations..."
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f migrations/001_init.sql
echo "Migrations applied."


