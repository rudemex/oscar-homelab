import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("oscar_approvals", Path(__file__).parents[1] / "files/oscar_approvals/__init__.py")
approvals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(approvals)


class ApprovalRulesTests(unittest.TestCase):
    def test_delicate_actions_ask_with_a_readable_description(self):
        cases = {
            ("mcp__oscar__oscar_delete_vm", (("vmid", 105),)): "BORRAR la VM 105",
            ("mcp_oscar_oscar_vm_power", (("vmid", 103), ("action", "shutdown"))): "Apagar la VM 103",
            ("oscar_docker_service_action", (("host", "devops"), ("project", "infisical"), ("action", "down"))):
                "Bajar (down) infisical en devops",
            ("oscar_forgejo_merge_pull_request", (("repo", "gitops"), ("number", 7))): "Fusionar el PR #7 en gitops",
            ("oscar_adguard_add_rewrite", (("domain", "x.oscar.home"), ("answer", "1.2.3.4"))):
                "DNS: agregar x.oscar.home → 1.2.3.4",
        }
        for (tool, args), expected in cases.items():
            self.assertEqual(approvals.describe(tool, dict(args)), expected)

    def test_safe_variants_run_without_asking(self):
        self.assertIsNone(approvals.describe("oscar_vm_power", {"vmid": 103, "action": "start"}))
        self.assertIsNone(approvals.describe("oscar_scale_workload", {"namespace": "a", "name": "b", "replicas": 2}))
        self.assertIsNone(approvals.describe("oscar_docker_service_action", {"host": "core", "project": "x", "action": "restart"}))
        self.assertIsNone(approvals.describe("oscar_ha_call_service", {"domain": "light", "service": "turn_on"}))
        for tool in ("oscar_get_status", "oscar_paperless_organize", "oscar_disks_smart_test", "oscar_led_power"):
            self.assertIsNone(approvals.describe(tool, {}))

    def test_risky_variants_ask(self):
        self.assertIsNotNone(approvals.describe("oscar_scale_workload", {"namespace": "a", "name": "b", "replicas": 0}))
        self.assertIsNotNone(approvals.describe("oscar_ha_call_service", {"domain": "lock", "service": "unlock"}))
        self.assertIsNotNone(approvals.describe("oscar_n8n_set_workflow_active", {"workflow_id": "x", "active": False}))

    def test_hook_uses_a_unique_rule_key_and_blocks_under_yolo(self):
        with patch.object(approvals, "_yolo_active", return_value=False):
            first = approvals._on_pre_tool_call("oscar_delete_vm", {"vmid": 105})
            second = approvals._on_pre_tool_call("oscar_delete_vm", {"vmid": 105})
            self.assertEqual(first["action"], "approve")
            self.assertNotEqual(first["rule_key"], second["rule_key"])
            self.assertIsNone(approvals._on_pre_tool_call("oscar_list_vms", {}))
        with patch.object(approvals, "_yolo_active", return_value=True):
            self.assertEqual(approvals._on_pre_tool_call("oscar_delete_vm", {"vmid": 105})["action"], "block")


if __name__ == "__main__":
    unittest.main()
