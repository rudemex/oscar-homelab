import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("oscar_tools", Path(__file__).parents[1] / "files/oscar_tools.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class OscarToolsTests(unittest.TestCase):
    def test_docker_operator_uses_fixed_hosts_and_allows_only_safe_actions(self):
        with patch.dict("os.environ", {"OSCAR_DOCKER_OPERATOR_TOKEN_CORE": "test-token",
                                      "OSCAR_DOCKER_OPERATOR_CA": "test-ca"}):
            with patch.object(tools, "_docker_operator_request", return_value={"projects": []}) as request:
                result = tools.oscar_docker_list_services("core")
                self.assertEqual(result["host"], "core")
                self.assertEqual(request.call_args.args[:2], ("core", "/v1/projects"))
            with patch.object(tools, "_docker_operator_request", return_value={"status": "accepted"}) as request:
                tools.oscar_docker_service_action("automation", "n8n", "restart", "n8n")
                self.assertEqual(request.call_args.args[:3], ("automation", "/v1/action", "POST"))
                self.assertEqual(request.call_args.args[3], {"project": "n8n", "action": "restart", "service": "n8n"})
                with self.assertRaises(ValueError):
                    tools.oscar_docker_service_action("core", "vaultwarden", "delete")
            with self.assertRaisesRegex(ValueError, "host must be"):
                tools._docker_operator_request("arbitrary-host", "/v1/projects")

    def test_docker_operator_requires_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "credentials are not configured"):
                tools.oscar_docker_list_services("core")

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
        def api(method, path, params=None):
            if path == "/cluster/resources":
                return [{"vmid": 102, "type": "qemu"}]
            return "UPID:oscar-core:test"
        with patch.object(tools, "_pve_request", side_effect=api) as request:
            result = tools.oscar_vm_power(102, "shutdown")
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["type"], "qemu")
        self.assertIn("/qemu/102/status/shutdown", request.call_args.args[1])
        with patch.object(tools, "_pve_request") as api:
            with self.assertRaises(ValueError):
                tools.oscar_vm_power(102, "shell")
            api.assert_not_called()

    def test_vm_power_supports_lxc_and_rejects_unknown_guests(self):
        def api(method, path, params=None):
            if path == "/cluster/resources":
                return [{"vmid": 100, "type": "lxc"}]
            return "UPID:oscar-core:test"
        with patch.object(tools, "_pve_request", side_effect=api) as request:
            result = tools.oscar_vm_power(100, "start")
        self.assertEqual(result["type"], "lxc")
        self.assertEqual(request.call_args.args[1], "/nodes/oscar-core/lxc/100/status/start")
        with patch.object(tools, "_pve_request", return_value=[]) as request:
            with self.assertRaisesRegex(ValueError, "does not exist"):
                tools.oscar_vm_power(999, "start")
            self.assertEqual(request.call_count, 1)

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

    def test_workload_inventory_returns_readiness_not_raw_objects(self):
        def api(method, path, payload=None):
            if path.endswith("/deployments"):
                return {"items": [{"metadata": {"namespace": "oscar-ai", "name": "hermes-agent"},
                                   "spec": {"replicas": 1}, "status": {"readyReplicas": 1, "availableReplicas": 1}}]}
            return {"items": []}
        with patch.object(tools, "_k8s_request", side_effect=api):
            result = tools.oscar_list_workloads("oscar-ai")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["workloads"][0]["ready"], 1)

    def test_scale_rejects_system_namespaces_and_bounds_replicas(self):
        with patch.object(tools, "_k8s_request") as api:
            with self.assertRaises(ValueError):
                tools.oscar_scale_workload("argocd", "argocd-server", 0)
            with self.assertRaises(ValueError):
                tools.oscar_scale_workload("oscar-lab", "ci-demo", 99)
            api.assert_not_called()

    def test_scale_patches_only_replica_count(self):
        with patch.object(tools, "_k8s_request", return_value={"metadata": {"generation": 4}}) as api:
            result = tools.oscar_scale_workload("oscar-lab", "ci-demo", 2)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(api.call_args.args[2], {"spec": {"replicas": 2}})

    def test_argocd_sync_disables_prune_and_validates_name(self):
        with patch.object(tools, "_k8s_request", return_value={"metadata": {"generation": 3}}) as api:
            result = tools.oscar_argocd_sync_application("hermes")
        self.assertEqual(result["prune"], False)
        self.assertEqual(api.call_args.args[2], {"operation": {"sync": {"revision": "HEAD", "prune": False}}})
        with patch.object(tools, "_k8s_request") as api:
            with self.assertRaises(ValueError):
                tools.oscar_argocd_sync_application("../root-app")
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

    def test_forgejo_repository_allowlist_and_write_protection(self):
        self.assertEqual(tools._forgejo_repo("gitops"), "apps/gitops")
        with self.assertRaises(ValueError):
            tools._forgejo_repo("unknown")
        with self.assertRaisesRegex(ValueError, "read-only"):
            tools._forgejo_repo("nestjs-starter", write=True)

    def test_forgejo_file_read_refuses_traversal_before_request(self):
        with patch.dict("os.environ", {"HERMES_FORGEJO_TOKEN": "test-token"}):
            with patch.object(tools, "_forgejo_request") as req:
                with self.assertRaises(ValueError):
                    tools.oscar_forgejo_read_file("gitops", "../../secret")
                req.assert_not_called()

    def test_forgejo_write_uses_post_to_create_and_put_to_update(self):
        with patch.dict("os.environ", {"HERMES_FORGEJO_TOKEN": "test-token"}):
            with patch.object(tools, "_forgejo_request", return_value={"commit": {"sha": "abc"}, "content": {"sha": "def"}}) as req:
                result = tools.oscar_forgejo_write_file("gitops", "apps/demo/values.yaml", "enabled: true", "hermes/turn-on-demo", "Enable demo")
        self.assertEqual(result["status"], "committed")
        self.assertEqual(req.call_args.args[0], "POST")
        self.assertNotIn("sha", req.call_args.args[2])
        self.assertIn("hermes/turn-on-demo", req.call_args.args[2]["branch"])
        with patch.dict("os.environ", {"HERMES_FORGEJO_TOKEN": "test-token"}):
            with patch.object(tools, "_forgejo_request", return_value={"commit": {"sha": "abc"}, "content": {"sha": "def"}}) as req:
                tools.oscar_forgejo_write_file("gitops", "apps/demo/values.yaml", "enabled: false", "hermes/turn-on-demo",
                                               "Disable demo", sha="a" * 40)
        self.assertEqual(req.call_args.args[0], "PUT")
        self.assertEqual(req.call_args.args[2]["sha"], "a" * 40)
        with patch.dict("os.environ", {"HERMES_FORGEJO_TOKEN": "test-token"}):
            with patch.object(tools, "_forgejo_request") as req:
                with self.assertRaises(ValueError):
                    tools.oscar_forgejo_write_file("gitops", "apps/demo/values.yaml", "x", "main", "Direct main write")
                req.assert_not_called()

    def test_forgejo_create_pr_requires_hermes_branch(self):
        with patch.dict("os.environ", {"HERMES_FORGEJO_TOKEN": "test-token"}):
            with patch.object(tools, "_forgejo_request", return_value={"number": 7, "state": "open"}) as req:
                result = tools.oscar_forgejo_create_pull_request("gitops", "Add demo", "Details", "hermes/demo")
        self.assertEqual(result["number"], 7)
        self.assertEqual(req.call_args.args[0], "POST")
        with patch.dict("os.environ", {"HERMES_FORGEJO_TOKEN": "test-token"}):
            with patch.object(tools, "_forgejo_request") as req:
                with self.assertRaises(ValueError):
                    tools.oscar_forgejo_create_pull_request("gitops", "Add demo", "Details", "main")
                req.assert_not_called()

    def test_n8n_list_workflows_requires_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "API key is not configured"):
                tools.oscar_n8n_list_workflows()

    def test_n8n_list_workflows_returns_id_name_active(self):
        with patch.dict("os.environ", {"OSCAR_N8N_API_KEY": "test-key"}):
            with patch.object(tools, "_n8n_request", return_value={"data": [{"id": "abc", "name": "Discord Broker", "active": True}]}) as req:
                result = tools.oscar_n8n_list_workflows()
        self.assertEqual(result["workflows"], [{"id": "abc", "name": "Discord Broker", "active": True}])
        self.assertEqual(req.call_args.args, ("GET", "/workflows?limit=100"))

    def test_n8n_set_workflow_active_validates_id_and_calls_correct_endpoint(self):
        with patch.dict("os.environ", {"OSCAR_N8N_API_KEY": "test-key"}):
            with patch.object(tools, "_n8n_request", return_value={"active": True}) as req:
                result = tools.oscar_n8n_set_workflow_active("abc123", True)
        self.assertEqual(result["active"], True)
        self.assertEqual(req.call_args.args, ("POST", "/workflows/abc123/activate"))
        with patch.dict("os.environ", {"OSCAR_N8N_API_KEY": "test-key"}):
            with patch.object(tools, "_n8n_request") as req:
                with self.assertRaises(ValueError):
                    tools.oscar_n8n_set_workflow_active("../etc", True)
                req.assert_not_called()

    def test_paperless_upload_only_accepts_files_from_the_gateway_document_cache(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as cache, tempfile.TemporaryDirectory() as elsewhere:
            good = os.path.join(cache, "doc_0123456789ab_Factura marzo.pdf")
            with open(good, "wb") as handle:
                handle.write(b"%PDF-1.4 test")
            outside = os.path.join(elsewhere, "secreto.pdf")
            with open(outside, "wb") as handle:
                handle.write(b"%PDF-1.4 no")
            os.symlink(outside, os.path.join(cache, "doc_aaaaaaaaaaaa_link.pdf"))
            script = os.path.join(cache, "doc_bbbbbbbbbbbb_run.sh")
            with open(script, "wb") as handle:
                handle.write(b"echo")
            os.mkdir(os.path.join(cache, "sub"))
            nested = os.path.join(cache, "sub", "doc_cccccccccccc_x.pdf")
            with open(nested, "wb") as handle:
                handle.write(b"%PDF-1.4")
            with patch.object(tools, "PAPERLESS_UPLOAD_DIR", cache), \
                    patch.dict("os.environ", {"OSCAR_PAPERLESS_TOKEN": "t"}):
                calls = []

                def fake(method, path, params=None, body=None, content_type=None):
                    calls.append((method, path, params, body, content_type))
                    if method == "POST":
                        return "11111111-2222-3333-4444-555555555555"
                    return [{"status": "SUCCESS", "related_document": "42", "result": "ok"}]
                with patch.object(tools, "_paperless_request", side_effect=fake):
                    result = tools.oscar_paperless_upload(good)
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["document_id"], 42)
                self.assertEqual(result["filename"], "Factura marzo.pdf")
                self.assertEqual(result["title"], "Factura marzo")
                method, path, _, body, content_type = calls[0]
                self.assertEqual((method, path), ("POST", "/api/documents/post_document/"))
                self.assertTrue(content_type.startswith("multipart/form-data; boundary="))
                self.assertIn(b'filename="Factura marzo.pdf"', body)
                self.assertIn(b"%PDF-1.4 test", body)
                with patch.object(tools, "_paperless_request") as request:
                    for bad in (outside, os.path.join(cache, "doc_aaaaaaaaaaaa_link.pdf"), script, nested,
                                "/etc/passwd", os.path.join(cache, "..", "x.pdf"), "", cache,
                                os.path.join(cache, "no-existe.pdf")):
                        with self.assertRaises(ValueError):
                            tools.oscar_paperless_upload(bad)
                    with self.assertRaises(ValueError):
                        tools.oscar_paperless_upload(good, title="linea\notra")
                    request.assert_not_called()

    def test_paperless_upload_reports_duplicates_and_slow_ocr_without_claiming_success(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as cache:
            good = os.path.join(cache, "doc_0123456789ab_a.pdf")
            with open(good, "wb") as handle:
                handle.write(b"%PDF-1.4")
            with patch.object(tools, "PAPERLESS_UPLOAD_DIR", cache):
                answers = ["11111111-2222-3333-4444-555555555555",
                           [{"status": "FAILURE", "result": "a.pdf: Not consuming: It is a duplicate of X (#7)"}]]
                with patch.object(tools, "_paperless_request", side_effect=answers):
                    result = tools.oscar_paperless_upload(good)
                self.assertEqual(result["status"], "failed")
                self.assertIn("duplicate", result["reason"])
                with patch.object(tools, "_paperless_request",
                                  side_effect=lambda *a, **k: "11111111-2222-3333-4444-555555555555"
                                  if a[0] == "POST" else []), \
                        patch.object(tools.time, "sleep"), \
                        patch.object(tools.time, "time", side_effect=[0, 1, 50, 100, 200]):
                    result = tools.oscar_paperless_upload(good)
                self.assertEqual(result["status"], "processing")

    def test_paperless_requires_token_and_fixed_api_paths(self):
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("OSCAR_PAPERLESS_TOKEN", None)
            with self.assertRaisesRegex(ValueError, "not configured"):
                tools.oscar_paperless_search("factura")
        with patch.dict("os.environ", {"OSCAR_PAPERLESS_TOKEN": "t"}):
            for bad in ("/admin/", "//evil/api/", "/api/../admin/", "api/documents/"):
                with self.assertRaises(ValueError):
                    tools._paperless_request("GET", bad)

    def test_paperless_search_bounds_input_and_strips_html_from_untrusted_results(self):
        payload = {"count": 1, "results": [{
            "id": 7, "title": "Contrato <b>alquiler</b>", "created": "2026-01-02",
            "original_file_name": "contrato.pdf", "page_count": 3,
            "__search_hit__": {"score": 1.5, "highlights": "el <span class=\"match\">alquiler</span>  vence"}}]}
        with patch.object(tools, "_paperless_request", return_value=payload) as request:
            result = tools.oscar_paperless_search("  alquiler ", limit=3)
        self.assertTrue(result["untrusted"])
        self.assertEqual(result["documents"][0]["excerpt"], "el alquiler vence")
        self.assertEqual(result["documents"][0]["title"], "Contrato alquiler")
        self.assertEqual(request.call_args_list[0].args[2]["query"], "alquiler")
        self.assertEqual(request.call_args_list[0].args[2]["page_size"], 3)
        with patch.object(tools, "_paperless_request") as request:
            for bad in ("", " ", "x" * 301, None):
                with self.assertRaises(ValueError):
                    tools.oscar_paperless_search(bad)
            for bad in (0, 11, True, "5"):
                with self.assertRaises(ValueError):
                    tools.oscar_paperless_search("a", limit=bad)
            request.assert_not_called()

    def test_paperless_get_document_truncates_content_and_validates_id(self):
        with patch.object(tools, "_paperless_request",
                          return_value={"id": 7, "title": "T", "content": "x" * 5000}) as request:
            result = tools.oscar_paperless_get_document(7, max_chars=500)
        self.assertEqual(len(result["content"]), 500)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["total_chars"], 5000)
        self.assertEqual(request.call_args.args[:2], ("GET", "/api/documents/7/"))
        with patch.object(tools, "_paperless_request") as request:
            for bad in (0, -1, True, "7", 1.5):
                with self.assertRaises(ValueError):
                    tools.oscar_paperless_get_document(bad)
            with self.assertRaises(ValueError):
                tools.oscar_paperless_get_document(7, max_chars=100)
            request.assert_not_called()

    def _paperless_fake(self, calls):
        catalog = {"/api/storage_paths/": [{"id": 3, "name": "Hogar/Expensas", "document_count": 2}],
                   "/api/tags/": [{"id": 5, "name": "Pagado", "document_count": 0, "children": []},
                                  {"id": 6, "name": "Hogar", "document_count": 0, "children": [5]}],
                   "/api/document_types/": [], "/api/correspondents/": []}
        def fake(method, path, params=None, body=None, content_type=None):
            calls.append((method, path, params, body))
            if method == "GET" and path in catalog:
                return {"results": catalog[path], "next": None}
            if method == "GET" and path.startswith("/api/documents/") and path != "/api/documents/":
                return {"id": 9, "tags": [6]}
            return {"id": 99, "name": "nuevo"}
        return fake

    def test_paperless_folder_names_are_safe_paths(self):
        self.assertEqual(tools._paperless_name(" Hogar / Expensas ", "folder"), "Hogar/Expensas")
        for bad in ["../etc", "Hogar//x", "a:b", "", "x" * 129, "linea\notra"]:
            with self.assertRaises(ValueError):
                tools._paperless_name(bad, "folder")

    def test_paperless_manage_creates_without_auto_matching_and_reuses_existing(self):
        calls = []
        with patch.object(tools, "_paperless_request", side_effect=self._paperless_fake(calls)):
            self.assertEqual(tools.oscar_paperless_manage("folder", "create", "hogar/expensas")["status"], "exists")
            tools.oscar_paperless_manage("folder", "create", "Trabajo/Recibos")
            tools.oscar_paperless_manage("tag", "create", "Vencido", parent="Hogar")
        posts = [__import__("json").loads(c[3]) for c in calls if c[0] == "POST"]
        self.assertEqual(posts[0]["path"], "Trabajo/Recibos/{{ title }}")
        self.assertEqual(posts[0]["matching_algorithm"], 0)
        self.assertEqual(posts[1]["parent"], 6)

    def test_paperless_manage_refuses_to_delete_what_is_in_use(self):
        calls = []
        with patch.object(tools, "_paperless_request", side_effect=self._paperless_fake(calls)):
            with self.assertRaisesRegex(ValueError, "still has 2 documents"):
                tools.oscar_paperless_manage("folder", "delete", "Hogar/Expensas")
            with self.assertRaisesRegex(ValueError, "child tags"):
                tools.oscar_paperless_manage("tag", "delete", "Hogar")
            tools.oscar_paperless_manage("tag", "delete", "Pagado")
        self.assertIn(("DELETE", "/api/tags/5/", None, None), calls)

    def test_paperless_organize_resolves_everything_before_changing_documents(self):
        calls = []
        with patch.object(tools, "_paperless_request", side_effect=self._paperless_fake(calls)):
            with self.assertRaisesRegex(ValueError, "does not exist"):
                tools.oscar_paperless_organize([9, 10], folder="Hogar/Expensas", add_tags=["Inexistente"])
            self.assertFalse([c for c in calls if c[0] == "PATCH"])
            result = tools.oscar_paperless_organize([9], folder="hogar/expensas", add_tags=["Pagado"],
                                                    remove_tags=["Hogar"], document_type="-")
        patch_body = __import__("json").loads([c for c in calls if c[0] == "PATCH"][0][3])
        self.assertEqual(patch_body, {"storage_path": 3, "document_type": None, "tags": [5]})
        self.assertEqual(result["updated"], [9])
        with self.assertRaisesRegex(ValueError, "one document"):
            tools.oscar_paperless_organize([1, 2], title="x")

    def test_disks_status_adds_roles_and_flags_benign_alerts(self):
        answers = {
            "/api/storage": {"disk_count": 1, "healthy_disks": 1, "disks": [
                {"name": "sdc", "serial": "2527VDD02140", "model": "WD Green", "health": "healthy",
                 "is_system_disk": False, "temperature": 37}]},
            "/api/storage/observations": {"observations": [
                {"serial": "2527VDD02140", "dismissed": False, "raw_message":
                 "/dev/sdc [SAT], no ATA CHECK POWER STATUS support, ignoring -n Directive"},
                {"serial": "2527VDD02140", "dismissed": True, "raw_message": "old"}]},
            "/api/proxmox-storage": {"storage": [{"name": "local-lvm", "percent": 57.6}]}}
        with patch.object(tools, "_proxmenux_request", side_effect=lambda path: answers[path]):
            result = tools.oscar_disks_status()
        disk = result["disks"][0]
        self.assertIn("BackupsCopia", disk["role"])
        self.assertEqual(len(disk["alerts"]), 1)
        self.assertTrue(disk["alerts"][0]["benign"])
        self.assertEqual(result["proxmox_storages"][0]["name"], "local-lvm")
        with self.assertRaises(ValueError):
            tools.oscar_disks_status("../etc")

    def test_disks_smart_test_only_on_known_disks(self):
        calls = []
        def fake(path, payload=None):
            calls.append((path, payload))
            return {"disks": [{"name": "sdc"}]} if path == "/api/storage" else {"success": True}
        with patch.object(tools, "_proxmenux_request", side_effect=fake):
            self.assertEqual(tools.oscar_disks_smart_test("sdc")["status"], "started")
            with self.assertRaisesRegex(ValueError, "not found"):
                tools.oscar_disks_smart_test("sdz")
            for bad in [("sda;rm", "long"), ("sdc", "conveyance")]:
                with self.assertRaises(ValueError):
                    tools.oscar_disks_smart_test(*bad)
        self.assertIn(("/api/storage/smart/sdc/test", {"test_type": "long"}), calls)

    def test_protected_infrastructure_vms_cannot_be_destroyed_or_resized(self):
        with patch.object(tools, "_pve_request") as request:
            for vmid in (102, 103, 108, 9000):
                with self.assertRaisesRegex(ValueError, "protected"):
                    tools.oscar_delete_vm(vmid, confirm=True)
                with self.assertRaisesRegex(ValueError, "protected"):
                    tools.oscar_resize_vm(vmid, cores=2)
            request.assert_not_called()
        with patch.object(tools, "_find_guest", return_value={"type": "qemu", "status": "stopped"}), \
                patch.object(tools, "_pve_request", return_value="UPID:x"):
            self.assertEqual(tools.oscar_delete_vm(105, confirm=True)["status"], "submitted")

    def test_critical_compose_projects_refuse_stop_and_down_but_allow_restart(self):
        with patch.object(tools, "_docker_operator_request", return_value={"status": "accepted"}) as request:
            for host, project in (("core", "cloudflared"), ("devops", "infisical"), ("automation", "n8n"),
                                  ("network", "cloudflared"), ("devops", "nexus"), ("devops", "forgejo")):
                for action in ("stop", "down"):
                    with self.assertRaisesRegex(ValueError, "critical"):
                        tools.oscar_docker_service_action(host, project, action)
            request.assert_not_called()
            tools.oscar_docker_service_action("devops", "infisical", "restart")
            tools.oscar_docker_service_action("core", "myspeed", "stop")
            self.assertEqual(request.call_count, 2)

    def test_chart_validates_input_before_rendering(self):
        good = dict(title="t", categories=["a", "b"], series=[{"name": "x", "values": [1, 2]}])
        for change in (dict(title=""), dict(title="x" * 121), dict(kind="pie"), dict(unit="pesos largos"),
                       dict(categories=[]), dict(categories=["a"] * 37),
                       dict(series=[]), dict(series=[{"name": "x", "values": [1]}]),
                       dict(series=[{"name": "x", "values": [1, float("inf")]}]),
                       dict(series=[{"name": "x", "values": [1, "2"]}]),
                       dict(series=[{"name": "x", "values": [None, None]}]),
                       dict(series=[{"name": str(i), "values": [1, 2]} for i in range(9)])):
            with self.assertRaises(ValueError, msg=str(change)):
                tools.oscar_chart(**{**good, **change})

    def test_chart_axis_helpers_use_round_ticks_and_spanish_numbers(self):
        ticks = tools._chart_ticks(0.0, 27_400_000.0)
        self.assertEqual(ticks[0], 0)
        self.assertGreaterEqual(ticks[-1], 27_400_000)
        self.assertLessEqual(len(ticks), 12)
        self.assertEqual(tools._chart_number(27_400_000, 1e6, " M", 1), "27,4 M")
        self.assertEqual(tools._chart_number(1234.5, 1.0, "", 1), "1.234,5")

    def test_chart_renders_png_in_the_media_cache_and_returns_deliver_line(self):
        import os
        import tempfile
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow is only available in the Hermes image")
        with tempfile.TemporaryDirectory() as out:
            with patch.object(tools, "CHART_DIR", out):
                for kind in ("bar", "line"):
                    result = tools.oscar_chart("Deuda", ["Feb", "Mar"], [
                        {"name": "2025", "values": [22_600_000, None]},
                        {"name": "2026", "values": [27_400_000, 26_800_000]}], kind, "$")
                    self.assertEqual(result["deliver"], "MEDIA:" + result["path"])
                    self.assertEqual(os.path.dirname(result["path"]), out)
                    with open(result["path"], "rb") as handle:
                        self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
