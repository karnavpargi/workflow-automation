"""Block UPDATE/DELETE on ai_audit_llmcall so entries are append-only."""

from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION ai_audit_block_modify() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'ai_audit_llmcall is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ai_audit_no_update ON ai_audit_llmcall;
DROP TRIGGER IF EXISTS ai_audit_no_delete ON ai_audit_llmcall;
CREATE TRIGGER ai_audit_no_update BEFORE UPDATE ON ai_audit_llmcall
    FOR EACH ROW EXECUTE FUNCTION ai_audit_block_modify();
CREATE TRIGGER ai_audit_no_delete BEFORE DELETE ON ai_audit_llmcall
    FOR EACH ROW EXECUTE FUNCTION ai_audit_block_modify();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS ai_audit_no_update ON ai_audit_llmcall;
DROP TRIGGER IF EXISTS ai_audit_no_delete ON ai_audit_llmcall;
DROP FUNCTION IF EXISTS ai_audit_block_modify();
"""


class Migration(migrations.Migration):
    """Add append-only triggers to ai_audit_llmcall."""

    dependencies = [("ai_audit", "0001_initial")]

    operations = [migrations.RunSQL(SQL, reverse_sql=REVERSE_SQL)]
