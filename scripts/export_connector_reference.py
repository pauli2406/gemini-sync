#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class FieldRow:
    path: str
    schema: dict[str, Any]
    required: bool


def _load_doc(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _type_string(node: dict[str, Any]) -> str:
    raw_type = node.get("type")
    if isinstance(raw_type, str):
        return raw_type
    if isinstance(raw_type, list):
        return " | ".join(str(item) for item in raw_type)
    if "properties" in node:
        return "object"
    if "items" in node:
        return "array"
    if "const" in node:
        return type(node["const"]).__name__
    return "unknown"


def _fmt_scalar(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _default_string(node: dict[str, Any]) -> str:
    if "default" in node:
        return _fmt_scalar(node["default"])
    if "const" in node:
        return _fmt_scalar(node["const"])
    return "-"


def _allowed_string(node: dict[str, Any]) -> str:
    parts: list[str] = []
    if "const" in node:
        parts.append(f"const: `{_fmt_scalar(node['const'])}`")
    if "enum" in node:
        enum_values = ", ".join(f"`{_fmt_scalar(value)}`" for value in node["enum"])
        parts.append(f"enum: {enum_values}")
    if "pattern" in node:
        parts.append(f"pattern: `{node['pattern']}`")
    return "<br>".join(parts) if parts else "-"


def _collect_rows(schema: dict[str, Any]) -> list[FieldRow]:
    rows: list[FieldRow] = []

    def walk(node: dict[str, Any], prefix: str = "") -> None:
        properties = node.get("properties")
        if not isinstance(properties, dict):
            return
        required_fields = set(node.get("required", []))
        for key, child in properties.items():
            if not isinstance(child, dict):
                continue
            path = f"{prefix}.{key}" if prefix else key
            rows.append(FieldRow(path=path, schema=child, required=key in required_fields))
            walk(child, path)

    walk(schema)
    return rows


def _resolve_field_meta(path: str, meta_fields: dict[str, Any]) -> dict[str, Any]:
    if path in meta_fields and isinstance(meta_fields[path], dict):
        return meta_fields[path]
    return {}


def _escape_cell(value: str) -> str:
    return (
        value.replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("\n", "<br>")
    )


def render_connector_reference(schema: dict[str, Any], meta: dict[str, Any]) -> str:
    defaults = meta.get("defaults", {})
    meta_fields = meta.get("fields", {})
    default_modes = defaults.get("modes", ["sql_pull", "rest_pull", "rest_push"])
    default_description = defaults.get("description", "-")
    default_example = defaults.get("example", "-")
    default_notes = defaults.get("operationalNotes", "-")

    header = (
        "| Field Path | Type | Required | Default | Allowed Values / Pattern | "
        "Modes | Description | Example | Operational Notes |"
    )

    lines: list[str] = [
        "# Connector Field Reference",
        "",
        "> Generated from `schemas/connector.schema.json` and `schemas/connector.docs-meta.yaml`.",
        "> Do not edit manually. Run `python scripts/export_connector_reference.py`.",
        "",
        header,
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for row in _collect_rows(schema):
        field_meta = _resolve_field_meta(row.path, meta_fields)
        modes = field_meta.get("modes", default_modes)
        if not isinstance(modes, list) or not modes:
            modes = default_modes

        description = str(field_meta.get("description", default_description))
        example = str(field_meta.get("example", default_example))
        notes = str(field_meta.get("operationalNotes", default_notes))

        cells = [
            f"`{row.path}`",
            f"`{_type_string(row.schema)}`",
            "Yes" if row.required else "No",
            f"`{_default_string(row.schema)}`" if _default_string(row.schema) != "-" else "-",
            _allowed_string(row.schema),
            ", ".join(f"`{mode}`" for mode in modes),
            _escape_cell(description),
            f"`{_escape_cell(example)}`" if example != "-" else "-",
            _escape_cell(notes),
        ]
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export connector field reference markdown.")
    parser.add_argument("--schema", default="schemas/connector.schema.json")
    parser.add_argument("--meta", default="schemas/connector.docs-meta.yaml")
    parser.add_argument("--output", default="docs/connector-field-reference.md")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    meta_path = Path(args.meta)
    output_path = Path(args.output)

    schema_doc = _load_doc(schema_path)
    meta_doc = _load_doc(meta_path)
    rendered = render_connector_reference(schema_doc, meta_doc)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote connector field reference to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
