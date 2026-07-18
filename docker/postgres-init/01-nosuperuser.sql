-- Downgrade the application role to non-superuser so that
-- FORCE ROW LEVEL SECURITY policies actually apply.
-- The application role is created by POSTGRES_USER env var.
ALTER USER wa NOSUPERUSER;
