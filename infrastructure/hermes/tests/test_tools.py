import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("oscar_tools", Path(__file__).parents[1] / "files/oscar_tools.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class OscarToolsTests(unittest.TestCase):
    def test_missing_metrics_are_unknown(self):
        with patch.object(tools, "query", return_value=[]):
            status = tools.oscar_get_status()
        self.assertTrue(all(s["status"] == "no_data" for s in status["sources"].values()))
        self.assertEqual(status["probe_summary"], {"ok": 0, "failed": 0, "unknown": 0, "total": 0})

    def test_status_labels_targets_with_human_names(self):
        result = tools.rows([{"metric": {"instance": "http://192.168.0.151:3000/", "job": "blackbox"},
                              "value": [1, "1"]}])
        self.assertEqual(result[0]["name"], "Forgejo (devops)")

    def test_partial_failure_keeps_other_evidence(self):
        def query(metric):
            if metric == "monitor_status":
                raise TimeoutError("private diagnostic must not leak")
            return [{"metric": {"instance": "test"}, "value": [1, "0"]}]
        with patch.object(tools, "query", side_effect=query):
            status = tools.oscar_get_status()
        self.assertEqual(status["sources"]["probe_success"]["series"][0]["value"], 0)
        self.assertEqual(status["sources"]["monitor_status"]["status"], "unavailable")
        self.assertNotIn("private diagnostic", str(status))

    def test_vm_power_actions_are_allowlisted(self):
        with patch.object(tools, "_pve_request", return_value="UPID:oscar-core:test") as api:
            result = tools.oscar_vm_power(102, "shutdown")
        self.assertEqual(result["status"], "submitted")
        self.assertIn("/qemu/102/status/shutdown", api.call_args.args[1])
        with patch.object(tools, "_pve_request") as api:
            with self.assertRaises(ValueError):
                tools.oscar_vm_power(102, "shell")
            api.assert_not_called()

    def test_vm_create_validates_parameters_before_proxmox_call(self):
        with patch.object(tools, "_pve_request") as api:
            with self.assertRaises(ValueError):
                tools.oscar_create_vm(102, "bad name")
            api.assert_not_called()

    def test_restart_rejects_protected_namespaces(self):
        with patch.object(tools, "_k8s_request") as api:
            with self.assertRaises(ValueError):
                tools.oscar_restart_workload("kube-system", "coredns")
            api.assert_not_called()

    def test_availability_cannot_inject_promql(self):
        with patch.object(tools, "query") as query:
            with self.assertRaises(ValueError):
                tools.oscar_get_availability('24h]) or up #')
            query.assert_not_called()

    def test_availability_reports_unknown_coverage_even_when_all_samples_pass(self):
        with patch.object(tools, "query", return_value=[{"metric": {}, "value": [1, "100"]}]):
            result = tools.oscar_get_availability()
        self.assertEqual(result["coverage"], "unknown")
        self.assertNotIn("downtime", result)

    def test_search_limits_and_marks_untrusted_content(self):
        payload = {"results": [{"title": "x", "url": "javascript:bad", "content": "x"}] +
                   [{"title": "x", "url": "https://example.org/", "content": "x" * 5000}] * 20}
        with patch.object(tools, "get_json", return_value=payload):
            result = tools.oscar_web_search("test")
        self.assertTrue(result["untrusted_content"])
        self.assertEqual(len(result["results"]), 8)
        self.assertEqual(len(result["results"][0]["snippet"]), 1500)

    def test_redirects_are_refused(self):
        with self.assertRaises(ValueError):
            tools.NoRedirect().redirect_request(None, None, 302, "", {}, "http://127.0.0.1")

    def test_nonfinite_values_do_not_become_healthy(self):
        self.assertIsNone(tools.rows([{"metric": {}, "value": [1, "NaN"]}])[0]["value"])

    def test_led_state_and_power_use_fixed_service_api(self):
        with patch.object(tools, "_fixed_http_request", return_value={"state": "offline"}) as req:
            tools.oscar_led_set_state("offline")
            tools.oscar_led_power(True)
        self.assertEqual(req.call_args_list[0].args[:2], (tools.LED_API, "/state/offline"))
        self.assertEqual(req.call_args_list[0].kwargs["method"], "POST")
        self.assertEqual(req.call_args_list[1].args[:2], (tools.LED_API, "/on"))

    def test_led_rejects_unknown_states(self):
        with patch.object(tools, "_fixed_http_request") as req:
            with self.assertRaises(ValueError):
                tools.oscar_led_set_state("execute-shell")
            req.assert_not_called()

    def test_ha_calls_any_validated_service_on_fixed_origin(self):
        with patch.dict("os.environ", {"OSCAR_HOME_ASSISTANT_TOKEN": "test-token"}):
            with patch.object(tools, "_fixed_http_request", return_value=[]) as req:
                result = tools.oscar_ha_call_service("light", "turn_off", {"entity_id": "light.office"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(req.call_args.args[:2], (tools.HA_API, "/api/services/light/turn_off"))
        self.assertEqual(req.call_args.kwargs["method"], "POST")
        self.assertEqual(req.call_args.kwargs["headers"]["Authorization"], "Bearer test-token")

    def test_ha_rejects_invalid_service_path_before_request(self):
        with patch.dict("os.environ", {"OSCAR_HOME_ASSISTANT_TOKEN": "test-token"}):
            with patch.object(tools, "_fixed_http_request") as req:
                with self.assertRaises(ValueError):
                    tools.oscar_ha_call_service("light/../../etc", "turn_off", {})
                req.assert_not_called()

    def test_ha_entity_discovery_returns_friendly_names_and_domain_filter(self):
        states = [
            {"entity_id": "light.office", "state": "on", "attributes": {"friendly_name": "Office"}},
            {"entity_id": "switch.fan", "state": "off", "attributes": {"friendly_name": "Fan"}},
        ]
        with patch.dict("os.environ", {"OSCAR_HOME_ASSISTANT_TOKEN": "test-token"}):
            with patch.object(tools, "_fixed_http_request", return_value=states):
                result = tools.oscar_ha_list_entities("light")
        self.assertEqual(result["entities"], [{"entity_id": "light.office", "name": "Office", "state": "on"}])


if __name__ == "__main__":
    unittest.main()
