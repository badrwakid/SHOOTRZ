"""Canonical DDL in supabase/schema_complete.sql must keep promised indexes and checks."""

from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
SCHEMA_PATH = project_root / "supabase" / "schema_complete.sql"


@pytest.fixture(scope="module")
def ddl() -> str:
    if not SCHEMA_PATH.is_file():
        pytest.skip(f"Missing {SCHEMA_PATH}")
    return SCHEMA_PATH.read_text(encoding="utf-8")


def test_schema_file_exists():
    assert SCHEMA_PATH.is_file(), f"expected {SCHEMA_PATH}"


def test_schema_has_history_composite_indexes(ddl: str):
    """User-scoped, time-ordered list queries (see data-layer plan)."""
    assert "idx_analysis_summaries_user_created_at" in ddl
    assert "idx_chat_history_user_created_at" in ddl
    assert "idx_sessions_user_timestamp" in ddl
    assert "idx_videos_user_created_at" in ddl
    assert "idx_drill_completions_user_completed_at" in ddl
    assert "idx_workout_progress_user_started_at" in ddl


def test_schema_defines_metrics_confidence_check(ddl: str):
    assert "metrics_confidence_range_chk" in ddl
    assert "confidence" in ddl


def test_analysis_summaries_index_is_on_user_id_and_created_at(ddl: str):
    # Guard against a typo that creates an index on the wrong columns.
    start = ddl.find("idx_analysis_summaries_user_created_at")
    assert start != -1
    chunk = ddl[start : start + 400]
    assert "user_id" in chunk and "created_at" in chunk
