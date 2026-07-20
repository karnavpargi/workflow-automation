"""Tests for the pgvector reachability check."""

from unittest.mock import MagicMock, patch


def test_pgvector_reachable_true_when_extension_present():
    """``pgvector_reachable`` returns True when ``vector`` ext exists."""
    from ai_service import db

    fake_engine = MagicMock()
    fake_conn = MagicMock()
    fake_conn.execute.return_value = None
    fake_engine.connect.return_value.__enter__.return_value = fake_conn
    with patch("ai_service.db.create_engine", return_value=fake_engine):
        assert db.pgvector_reachable() is True


def test_pgvector_reachable_false_on_sqlalchemy_error():
    """Any ``SQLAlchemyError`` is swallowed and reported as unreachable."""
    from sqlalchemy.exc import SQLAlchemyError

    from ai_service import db

    with patch(
        "ai_service.db.create_engine",
        side_effect=SQLAlchemyError("nope"),
    ):
        assert db.pgvector_reachable() is False


def test_vector_store_url_normalizes_dsn_for_langchain_postgres():
    """``vector_store_url`` strips the SQLAlchemy ``+psycopg`` driver suffix."""
    from ai_service import db

    db.settings.database_url = "postgresql+psycopg://wa:wa@db:5432/wa"
    assert db.vector_store_url() == "postgresql://wa:wa@db:5432/wa"
