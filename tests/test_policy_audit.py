from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.policy_audit import export_policy_audit_bundle, policy_audit_status, record_policy_audit_event


class PolicyAuditTests(unittest.TestCase):
    def test_record_and_export_audit_event(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "policy-audit.jsonl"
            record_policy_audit_event("policy_test_run", payload={"passed": 2}, log_path=log)
            status = policy_audit_status(log_path=log)
            bundle = export_policy_audit_bundle(log_path=log)
        self.assertEqual(status.event_count, 1)
        self.assertEqual(bundle["event_count"], 1)


if __name__ == "__main__":
    unittest.main()