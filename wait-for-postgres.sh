#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

# Note: We use the variable names exactly as they are in the .env files
until PGPASSWORD=$PG_PASSWORD psql -h "$host" -U "postgres" -d "$DB_NAME" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd
