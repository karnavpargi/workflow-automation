-- Create the pgvector extension (must run before the wa role is
-- downgraded to NOSUPERUSER in 01-nosuperuser.sql, since CREATE
-- EXTENSION requires superuser privileges).
CREATE EXTENSION IF NOT EXISTS vector;
