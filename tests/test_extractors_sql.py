from __future__ import annotations

import sqlite3

from gemini_sync_bridge.adapters import extractors
from gemini_sync_bridge.schemas import SourceConfig


def test_extract_sql_rows_returns_rows_and_max_watermark(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "hr.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE employees (employee_id INTEGER, full_name TEXT, updated_at TEXT)"
        )
        conn.execute(
            "INSERT INTO employees VALUES (?, ?, ?)",
            (1, "Old User", "2026-02-14T00:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO employees VALUES (?, ?, ?)",
            (2, "New User", "2026-02-16T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(
        extractors,
        "resolve_secret",
        lambda _: f"sqlite+pysqlite:///{db_path}",
    )

    source = SourceConfig(
        type="postgres",
        secretRef="hr-db-credentials",
        query=(
            "SELECT employee_id, full_name, updated_at FROM employees "
            "WHERE updated_at > :watermark"
        ),
        watermarkField="updated_at",
    )

    result = extractors.extract_sql_rows(source, "2026-02-15T00:00:00+00:00")

    assert len(result.rows) == 1
    assert result.rows[0]["employee_id"] == 2
    assert result.watermark == "2026-02-16T00:00:00+00:00"


def test_extract_sql_rows_supports_oracle_source_type(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "finance.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE invoices (invoice_id INTEGER, title TEXT, updated_at TEXT)")
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?)",
            (10, "Invoice A", "2026-02-16T12:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(
        extractors,
        "resolve_secret",
        lambda _: f"sqlite+pysqlite:///{db_path}",
    )

    source = SourceConfig(
        type="oracle",
        secretRef="oracle-finance-credentials",
        query=(
            "SELECT invoice_id, title, updated_at FROM invoices "
            "WHERE updated_at > :watermark"
        ),
        watermarkField="updated_at",
    )

    result = extractors.extract_sql_rows(source, "2026-02-15T00:00:00+00:00")

    assert len(result.rows) == 1
    assert result.rows[0]["invoice_id"] == 10
    assert result.watermark == "2026-02-16T12:00:00+00:00"
