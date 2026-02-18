from __future__ import annotations

import json
from pathlib import Path

import pytest

from gemini_sync_bridge.adapters import extractors
from gemini_sync_bridge.schemas import SourceConfig


def _file_source(
    *,
    path: str,
    glob: str = "*.csv",
    document_mode: str = "row",
    delimiter: str = ",",
    has_header: bool = True,
    encoding: str = "utf-8",
    watermark_field: str | None = "updated_at",
) -> SourceConfig:
    return SourceConfig(
        type="file",
        path=path,
        glob=glob,
        format="csv",
        watermarkField=watermark_field,
        csv={
            "documentMode": document_mode,
            "delimiter": delimiter,
            "hasHeader": has_header,
            "encoding": encoding,
        },
    )


def test_extract_file_rows_row_mode_injects_metadata_and_compact_checkpoint(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "a.csv").write_text(
        "employee_id,full_name,updated_at\n1,Ada,2026-02-16T08:00:00+00:00\n2,Bob,2026-02-16T09:00:00+00:00\n",
        encoding="utf-8",
    )
    (source_dir / "b.csv").write_text(
        "employee_id,full_name,updated_at\n3,Cam,2026-02-16T10:00:00+00:00\n",
        encoding="utf-8",
    )

    result = extractors.extract_file_rows(_file_source(path=str(source_dir)), None)

    assert len(result.rows) == 3
    assert [row["file_name"] for row in result.rows] == ["a.csv", "a.csv", "b.csv"]
    assert result.rows[0]["file_path"].endswith("a.csv")
    assert isinstance(result.rows[0]["file_size_bytes"], int)
    assert result.rows[0]["file_mtime"]

    checkpoint = json.loads(result.watermark or "")
    assert checkpoint["v"] == 1
    assert checkpoint["fc"] == 2
    assert checkpoint["rw"] == "2026-02-16T10:00:00+00:00"
    assert checkpoint["lm"] is not None
    assert checkpoint["fh"].startswith("sha256:")
    assert len(result.watermark or "") <= 255


def test_extract_file_rows_file_mode_includes_raw_content_and_rows_json(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "employees.csv").write_text(
        "employee_id,full_name\n1,Ada\n2,Bob\n",
        encoding="utf-8",
    )

    result = extractors.extract_file_rows(
        _file_source(path=str(source_dir), document_mode="file"),
        None,
    )

    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["file_name"] == "employees.csv"
    assert "employee_id,full_name" in row["file_content_raw"]
    parsed = json.loads(row["file_rows_json"])
    assert parsed[0]["employee_id"] == "1"
    assert parsed[1]["full_name"] == "Bob"


def test_extract_file_rows_supports_delimiter_header_and_encoding_controls(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    content = "1;Jörg;2026-02-16T08:30:00+00:00\n"
    (source_dir / "latin.csv").write_bytes(content.encode("latin-1"))

    result = extractors.extract_file_rows(
        _file_source(
            path=str(source_dir),
            delimiter=";",
            has_header=False,
            encoding="latin-1",
            watermark_field="column_3",
        ),
        None,
    )

    assert len(result.rows) == 1
    assert result.rows[0]["column_1"] == "1"
    assert result.rows[0]["column_2"] == "Jörg"
    checkpoint = json.loads(result.watermark or "")
    assert checkpoint["rw"] == "2026-02-16T08:30:00+00:00"


def test_extract_file_rows_checkpoint_fallback_accepts_legacy_plain_row_watermark(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "employees.csv").write_text(
        "employee_id,full_name\n1,Ada\n",
        encoding="utf-8",
    )

    result = extractors.extract_file_rows(
        _file_source(path=str(source_dir), watermark_field="updated_at"),
        "2026-02-01T00:00:00+00:00",
    )

    checkpoint = json.loads(result.watermark or "")
    assert checkpoint["rw"] == "2026-02-01T00:00:00+00:00"


def test_extract_file_rows_checkpoint_fallback_accepts_v1_checkpoint_json(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "employees.csv").write_text(
        "employee_id,full_name\n1,Ada\n",
        encoding="utf-8",
    )
    previous_checkpoint = (
        '{"v":1,"rw":"2026-02-03T00:00:00+00:00","fc":3,"lm":null,"fh":"sha256:abc"}'
    )

    result = extractors.extract_file_rows(
        _file_source(path=str(source_dir), watermark_field="updated_at"),
        previous_checkpoint,
    )

    checkpoint = json.loads(result.watermark or "")
    assert checkpoint["rw"] == "2026-02-03T00:00:00+00:00"


def test_extract_file_rows_rejects_recursive_glob(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "employees.csv").write_text("id,name\n1,Ada\n", encoding="utf-8")

    source = _file_source(path=str(source_dir), glob="**/*.csv")
    with pytest.raises(extractors.ExtractionError):
        extractors.extract_file_rows(source, None)


def test_extract_sql_rows_requires_secret_ref() -> None:
    source = SourceConfig(
        type="postgres",
        query="SELECT 1",
        watermarkField="updated_at",
    )
    with pytest.raises(extractors.ExtractionError, match="source.secretRef is required"):
        extractors.extract_sql_rows(source, None)


def test_extract_rest_rows_requires_secret_ref_without_oauth() -> None:
    source = SourceConfig(
        type="http",
        url="https://api.local/v1/articles",
        method="GET",
    )
    with pytest.raises(extractors.ExtractionError, match="source.secretRef is required"):
        extractors.extract_rest_rows(source, None)


def test_extract_file_rows_requires_csv_format() -> None:
    source = SourceConfig(type="file", path=".", glob="*.csv", csv={"documentMode": "row"})
    with pytest.raises(extractors.ExtractionError, match="source.format must be csv"):
        extractors.extract_file_rows(source, None)


def test_extract_file_rows_requires_source_path() -> None:
    source = SourceConfig(type="file", glob="*.csv", format="csv", csv={"documentMode": "row"})
    with pytest.raises(extractors.ExtractionError, match="source.path is required"):
        extractors.extract_file_rows(source, None)


def test_extract_file_rows_requires_source_glob() -> None:
    source = SourceConfig(type="file", path=".", format="csv", csv={"documentMode": "row"})
    with pytest.raises(extractors.ExtractionError, match="source.glob is required"):
        extractors.extract_file_rows(source, None)


def test_extract_file_rows_requires_csv_config() -> None:
    source = SourceConfig(type="file", path=".", glob="*.csv", format="csv")
    with pytest.raises(extractors.ExtractionError, match="source.csv is required"):
        extractors.extract_file_rows(source, None)


def test_extract_file_rows_rejects_missing_directory(tmp_path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(extractors.ExtractionError, match="source.path does not exist"):
        extractors.extract_file_rows(_file_source(path=str(missing)), None)


def test_extract_file_rows_rejects_source_path_that_is_not_directory(tmp_path) -> None:
    file_path = tmp_path / "not-dir.csv"
    file_path.write_text("id,name\n1,Ada\n", encoding="utf-8")
    with pytest.raises(extractors.ExtractionError, match="source.path must be a directory"):
        extractors.extract_file_rows(_file_source(path=str(file_path)), None)


def test_extract_file_rows_wraps_file_read_errors(tmp_path, monkeypatch) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    csv_file = source_dir / "employees.csv"
    csv_file.write_text("id,name\n1,Ada\n", encoding="utf-8")

    original_read_text = Path.read_text

    def fake_read_text(path: Path, *args, **kwargs):  # type: ignore[override]
        if path == csv_file:
            raise OSError("permission denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    with pytest.raises(extractors.ExtractionError, match="Unable to read CSV file"):
        extractors.extract_file_rows(_file_source(path=str(source_dir)), None)


def test_extract_file_rows_keeps_non_v1_json_watermark_as_legacy_fallback(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "employees.csv").write_text("id,name\n1,Ada\n", encoding="utf-8")

    result = extractors.extract_file_rows(
        _file_source(path=str(source_dir), watermark_field="updated_at"),
        '{"foo":"bar"}',
    )

    checkpoint = json.loads(result.watermark or "")
    assert checkpoint["rw"] == '{"foo":"bar"}'


def test_file_checkpoint_builder_enforces_compact_length_limit() -> None:
    with pytest.raises(extractors.ExtractionError, match="checkpoint exceeded 255 characters"):
        extractors._build_file_checkpoint(  # noqa: SLF001
            row_watermark="x" * 240,
            file_count=1,
            latest_file_mtime="2026-02-16T10:00:00+00:00",
            file_manifest_hash="sha256:test",
        )


def test_resolve_source_path_normalizes_relative_paths() -> None:
    resolved = extractors._resolve_source_path("./runtime/sources/hr")  # noqa: SLF001
    assert resolved.is_absolute()
