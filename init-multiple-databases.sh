#!/bin/bash
set -e

# Create multiple databases for service isolation
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create databases only if they don't exist
    SELECT 'CREATE DATABASE "Users"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'Users')\gexec
    SELECT 'CREATE DATABASE "Khan_Academy"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'Khan_Academy')\gexec
    SELECT 'CREATE DATABASE "Evaluation"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'Evaluation')\gexec
    
    -- Grant privileges (these are idempotent)
    GRANT ALL PRIVILEGES ON DATABASE "Users" TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE "Khan_Academy" TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE "Evaluation" TO $POSTGRES_USER;
EOSQL

echo "Multiple databases created successfully!"
