"""Fixtures for user-centric database tests."""

from pathlib import Path

import pytest

from axiom.core.db import Database
from scripts.init_db import init_database


@pytest.fixture()
def user_db(tmp_path: Path) -> Database:
    """Create a temporary database with user tables for testing."""
    db_path = tmp_path / "user_test.duckdb"
    init_database(str(db_path))
    return Database(str(db_path))
