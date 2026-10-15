import subprocess
import unittest
from pathlib import Path


CHART = Path(__file__).resolve().parents[1]


def render(discord_enabled, proxmox_enabled=False):
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
        self.assertNotIn('OSCAR_PROXMOX_TOKEN_SECRET: "{{ .OSCAR_PROXMOX_TOKEN_SECRET.Value }}"', manifest)

    def test_proxmox_credentials_and_tools_are_opt_in(self):
        manifest = render(True, True)
        self.assertIn('OSCAR_PROXMOX_TOKEN_SECRET: "{{ .OSCAR_PROXMOX_TOKEN_SECRET.Value }}"', manifest)
        self.assertIn("oscar_vm_power", manifest)

    def test_home_assistant_credentials_tools_and_network_are_enabled(self):
        manifest = render(True)
        self.assertIn('OSCAR_HOME_ASSISTANT_TOKEN: "{{ .OSCAR_HOME_ASSISTANT_TOKEN.Value }}"', manifest)
        self.assertIn("oscar_ha_list_entities", manifest)
        self.assertIn("oscar_ha_call_service", manifest)
        self.assertIn("192.168.0.195/32", manifest)

    def test_all_default_operator_tools_are_configured(self):
        manifest = render(True, True)
        for name in ("oscar_restart_workload", "oscar_list_vms", "oscar_vm_power", "oscar_create_vm",
                     "oscar_ha_get_state", "oscar_ha_list_entities", "oscar_ha_call_service",
                     "oscar_led_get_state", "oscar_led_set_state", "oscar_led_power"):
            self.assertIn(name, manifest)


if __name__ == "__main__":
    unittest.main()
