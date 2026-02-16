from __future__ import annotations

import yaml


def test_schedule_jobs_include_enabled_defaults() -> None:
    payload = yaml.safe_load(
        """
        scheduleJobs:
          - name: a
            schedule: \"*/5 * * * *\"
            connectorPath: connectors/a.yaml
            enabled: true
        """
    )

    assert payload["scheduleJobs"][0]["enabled"] is True
