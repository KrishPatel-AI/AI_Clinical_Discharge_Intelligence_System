"""Tests for Alembic database migration scripts."""

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


@pytest.fixture
def alembic_config(tmp_path: Path) -> tuple[Config, str]:
    """Create an Alembic config pointing to an isolated SQLite test database."""
    db_path = tmp_path / "migration_test.sqlite"
    db_url = f"sqlite:///{db_path}"

    root_dir = Path(__file__).resolve().parent.parent
    ini_path = root_dir / "alembic.ini"

    config = Config(str(ini_path))
    config.set_main_option("sqlalchemy.url", db_url)
    config.set_main_option("script_location", str(root_dir / "alembic"))
    return config, db_url


def test_alembic_migration_upgrade_and_downgrade(alembic_config: tuple[Config, str]) -> None:
    """Validate that upgrading to head creates all schema objects and downgrading clears them."""
    config, db_url = alembic_config
    engine = create_engine(db_url)

    # 1. Run upgrade to head
    command.upgrade(config, "head")

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "users" in tables
    assert "reports" in tables
    assert "suggestions" in tables
    assert "audit_logs" in tables
    assert "alembic_version" in tables

    # Verify columns in reports table
    report_columns = {col["name"] for col in inspector.get_columns("reports")}
    assert "id" in report_columns
    assert "user_id" in report_columns
    assert "filename" in report_columns
    assert "diagnosis" in report_columns
    assert "status" in report_columns
    assert "message" in report_columns
    assert "completeness_score" in report_columns
    assert "initial_score" in report_columns
    assert "source_text" in report_columns
    assert "langfuse_trace_id" in report_columns
    assert "langfuse_parent_observation_id" in report_columns
    assert "created_at" in report_columns

    suggestion_columns = {col["name"] for col in inspector.get_columns("suggestions")}
    assert "action" in suggestion_columns
    assert "target_text" in suggestion_columns
    assert "suggested_text" in suggestion_columns

    # 2. Downgrade to base
    command.downgrade(config, "base")

    inspector = inspect(engine)
    post_downgrade_tables = set(inspector.get_table_names())
    assert "reports" not in post_downgrade_tables
    assert "suggestions" not in post_downgrade_tables
    assert "audit_logs" not in post_downgrade_tables
    assert "users" not in post_downgrade_tables

    # 3. Re-upgrade to head (idempotency check)
    command.upgrade(config, "head")
    inspector = inspect(engine)
    reupgraded_tables = set(inspector.get_table_names())
    assert "reports" in reupgraded_tables

    engine.dispose()
