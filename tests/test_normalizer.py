from __future__ import annotations

from ingest_relay.schemas import MappingConfig
from ingest_relay.services.normalizer import normalize_records


def test_normalize_records_builds_canonical_docs() -> None:
    mapping = MappingConfig(
        idField="employee_id",
        titleField="full_name",
        contentTemplate="{{ department }} {{ role }}",
        uriTemplate="https://hr.local/{{ employee_id }}",
        aclUsersField="allowed_users",
        aclGroupsField="allowed_groups",
        metadataFields=["department"],
    )

    docs = normalize_records(
        connector_id="hr-employees",
        mapping=mapping,
        source_watermark_field="updated_at",
        rows=[
            {
                "employee_id": 123,
                "full_name": "Jane Doe",
                "department": "Engineering",
                "role": "Manager",
                "allowed_users": ["jane@example.com"],
                "allowed_groups": ["eng-managers"],
                "updated_at": "2026-02-16T08:30:00Z",
            }
        ],
    )

    assert len(docs) == 1
    assert docs[0].doc_id == "hr-employees:123"
    assert docs[0].title == "Jane Doe"
    assert docs[0].content == "Engineering Manager"
    assert docs[0].uri == "https://hr.local/123"
    assert docs[0].acl_groups == ["eng-managers"]
    assert docs[0].metadata["department"] == "Engineering"
    assert docs[0].checksum.startswith("sha256:")
