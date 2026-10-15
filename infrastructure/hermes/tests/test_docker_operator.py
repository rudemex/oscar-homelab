import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

path = Path(__file__).parents[1] / "files/docker_operator.py"
spec = importlib.util.spec_from_file_location("docker_operator", path)
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


class DockerOperatorTests(unittest.TestCase):
    def setUp(self):
        self.projects = patch.object(operator, "PROJECTS", {"n8n": "/srv/n8n"})
        self.projects.start()
        self.addCleanup(self.projects.stop)

    def test_restart_calls_only_approved_compose_command(self):
        with patch.object(operator, "project_services", return_value=["n8n", "worker"]):
            with patch.object(operator, "compose", return_value="") as compose:
                result = operator.perform_action({"project": "n8n", "service": "worker", "action": "restart"})
        self.assertEqual(result["status"], "accepted")
        compose.assert_called_once_with("n8n", ["restart", "worker"])

    def test_unknown_project_service_and_destructive_actions_are_rejected(self):
        for request in (
            {"project": "../root", "service": None, "action": "restart"},
            {"project": "n8n", "service": "../secret", "action": "restart"},
            {"project": "n8n", "service": None, "action": "delete"},
        ):
            with patch.object(operator, "project_services", return_value=["n8n"]):
                with patch.object(operator, "compose") as compose:
                    with self.assertRaises(ValueError):
                        operator.perform_action(request)
                    compose.assert_not_called()

    def test_protected_projects_can_restart_but_never_stop_or_go_down(self):
        with patch.object(operator, "NO_STOP", {"n8n"}):
            with patch.object(operator, "compose", return_value="") as compose:
                for action in ("stop", "down"):
                    with self.assertRaisesRegex(ValueError, "protected"):
                        operator.perform_action({"project": "n8n", "service": None, "action": action})
                compose.assert_not_called()
                self.assertEqual(operator.perform_action({"project": "n8n", "service": None, "action": "restart"})["status"],
                                 "accepted")

    def test_down_is_allowed_and_never_passes_volume_removal_flags(self):
        with patch.object(operator, "compose", return_value="") as compose:
            result = operator.perform_action({"project": "n8n", "service": None, "action": "down"})
        self.assertEqual(result["status"], "accepted")
        compose.assert_called_once_with("n8n", ["down"])

    def test_logs_are_scoped_to_known_service_and_truncated(self):
        with patch.object(operator, "compose", return_value="x" * (operator.MAX_LOG_CHARS + 500)) as compose:
            result = operator.project_logs("n8n", "worker", 50)
        self.assertEqual(len(result), operator.MAX_LOG_CHARS)
        compose.assert_called_once_with("n8n", ["logs", "--no-color", "--tail", "50", "worker"])

    def test_status_parser_accepts_json_array(self):
        with patch.object(operator, "project_services", return_value=["n8n"]):
            with patch.object(operator, "compose", return_value='[{"Name":"n8n-1","Service":"n8n","State":"running"}]'):
                result = operator.project_status("n8n")
        self.assertEqual(result["services"], ["n8n"])
        self.assertEqual(result["containers"][0]["State"], "running")


if __name__ == "__main__":
    unittest.main()
