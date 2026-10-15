import subprocess
import unittest
from pathlib import Path


CHART = Path(__file__).resolve().parents[1]


def render(discord_enabled, proxmox_enabled=False, docker_operator_enabled=False):
    result = subprocess.run(
        [
            "helm",
            "template",
            "hermes",
            str(CHART),
            "--set",
            f"discord.enabled={'true' if discord_enabled else 'false'}",
            "--set",
            f"proxmox.enabled={'true' if proxmox_enabled else 'false'}",
            "--set",
            f"dockerOperator.enabled={'true' if docker_operator_enabled else 'false'}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


class DiscordChartTest(unittest.TestCase):
    def test_disabled_does_not_mount_discord_credentials_or_adapter_settings(self):
        manifest = render(False)
        self.assertNotIn("DISCORD_BOT_TOKEN", manifest)
        self.assertNotIn("DISCORD_ALLOWED_USERS", manifest)
        self.assertNotIn("DISCORD_REQUIRE_MENTION", manifest)

    def test_enabled_reads_allowlisted_discord_credentials_from_infisical(self):
        manifest = render(True)
        self.assertIn("DISCORD_BOT_TOKEN", manifest)
        self.assertIn("DISCORD_ALLOWED_USERS", manifest)
        self.assertIn("DISCORD_REQUIRE_MENTION", manifest)
        self.assertIn("DISCORD_ALLOW_MENTION_EVERYONE", manifest)
        self.assertIn("DISCORD_ALLOW_MENTION_ROLES", manifest)
        self.assertNotIn("DISCORD_ALLOW_ALL_USERS", manifest)

    def test_operator_permissions_are_bounded_and_proxmox_is_opt_in(self):
        manifest = render(True)
        self.assertIn("name: hermes-agent-operator", manifest)
        self.assertIn("resources: [deployments, statefulsets]", manifest)
        self.assertIn("verbs: [get, list, patch]", manifest)
        self.assertIn("name: hermes-argocd-operator", manifest)
        self.assertIn("resources: [applications]", manifest)
        self.assertNotIn('OSCAR_PROXMOX_TOKEN_SECRET: "{{ .OSCAR_PROXMOX_TOKEN_SECRET.Value }}"', manifest)

    def test_proxmox_credentials_and_tools_are_opt_in(self):
        manifest = render(True, True)
        self.assertIn('OSCAR_PROXMOX_TOKEN_SECRET: "{{ .OSCAR_PROXMOX_TOKEN_SECRET.Value }}"', manifest)
        self.assertIn('OSCAR_PROXMOX_TOKEN_SECRET: "${OSCAR_PROXMOX_TOKEN_SECRET}"', manifest)
        self.assertIn("oscar_vm_power", manifest)

    def test_home_assistant_credentials_tools_and_network_are_enabled(self):
        manifest = render(True)
        self.assertIn('OSCAR_HOME_ASSISTANT_TOKEN: "{{ .OSCAR_HOME_ASSISTANT_TOKEN.Value }}"', manifest)
        self.assertIn('OSCAR_HOME_ASSISTANT_TOKEN: "${OSCAR_HOME_ASSISTANT_TOKEN}"', manifest)
        self.assertIn("oscar_ha_list_entities", manifest)
        self.assertIn("oscar_ha_call_service", manifest)
        self.assertIn("192.168.0.195/32", manifest)

    def test_forgejo_token_is_mounted_and_network_is_limited_to_local_instance(self):
        manifest = render(True)
        self.assertIn('HERMES_FORGEJO_TOKEN: "{{ .HERMES_FORGEJO_TOKEN.Value }}"', manifest)
        self.assertIn('HERMES_FORGEJO_TOKEN: "${HERMES_FORGEJO_TOKEN}"', manifest)
        self.assertIn("192.168.0.151/32", manifest)
        self.assertIn("port: 3000", manifest)

    def test_kubernetes_api_egress_is_limited_to_control_plane(self):
        manifest = render(True)
        self.assertIn("192.168.0.150/32", manifest)
        self.assertIn('KUBERNETES_SERVICE_HOST: "192.168.0.150"', manifest)
        self.assertIn('KUBERNETES_SERVICE_PORT_HTTPS: "6443"', manifest)

    def test_docker_operator_is_opt_in_and_egress_is_fixed(self):
        disabled = render(True)
        self.assertNotIn('OSCAR_DOCKER_OPERATOR_TOKEN_CORE: "${OSCAR_DOCKER_OPERATOR_TOKEN_CORE}"', disabled)
        self.assertNotIn("            - oscar_docker_service_action", disabled)
        manifest = render(True, docker_operator_enabled=True)
        for host in ("CORE", "DEVOPS", "AUTOMATION", "MONITOR", "NETWORK"):
            self.assertIn(f'OSCAR_DOCKER_OPERATOR_TOKEN_{host}: "${{OSCAR_DOCKER_OPERATOR_TOKEN_{host}}}"', manifest)
            self.assertIn(f'OSCAR_DOCKER_OPERATOR_TOKEN_{host}: "{{{{ .OSCAR_DOCKER_OPERATOR_TOKEN_{host}.Value }}}}"', manifest)
        self.assertIn("OSCAR_DOCKER_OPERATOR_CA:", manifest)
        self.assertIn("192.168.0.153/32", manifest)
        self.assertIn("port: 9443", manifest)
        self.assertIn("oscar_docker_list_services", manifest)
        self.assertIn("oscar_docker_service_action", manifest)

    def test_all_default_operator_tools_are_configured(self):
        manifest = render(True, True)
        for name in ("oscar_restart_workload", "oscar_list_workloads", "oscar_scale_workload",
                     "oscar_argocd_list_applications", "oscar_argocd_sync_application",
                     "oscar_list_vms", "oscar_vm_power", "oscar_create_vm",
                     "oscar_ha_get_state", "oscar_ha_list_entities", "oscar_ha_call_service",
                     "oscar_led_get_state", "oscar_led_set_state", "oscar_led_power",
                     "oscar_forgejo_list_repositories", "oscar_forgejo_list_pull_requests",
                     "oscar_forgejo_read_file", "oscar_forgejo_create_branch",
                     "oscar_forgejo_write_file", "oscar_forgejo_create_pull_request"):
            self.assertIn(name, manifest)


if __name__ == "__main__":
    unittest.main()
