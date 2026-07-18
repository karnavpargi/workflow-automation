"""Block UPDATE/DELETE on audit_auditlog so entries are append-only."""

from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION audit_block_modify() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_auditlog is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_no_update ON audit_auditlog;
DROP TRIGGER IF EXISTS audit_no_delete ON audit_auditlog;
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_auditlog
    FOR EACH ROW EXECUTE FUNCTION audit_block_modify();
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_auditlog
    FOR EACH ROW EXECUTE FUNCTION audit_block_modify();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS audit_no_update ON audit_auditlog;
DROP TRIGGER IF EXISTS audit_no_delete ON audit_auditlog;
DROP FUNCTION IF EXISTS audit_block_modify();
"""


class Migration(migrations.Migration):
    """Add append-only triggers to audit_auditlog."""

    dependencies = [("audit", "0001_initial")]

    operations = [migrations.RunSQL(SQL, reverse_sql=REVERSE_SQL)]
