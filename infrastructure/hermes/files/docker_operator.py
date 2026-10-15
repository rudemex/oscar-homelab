"""Small, allowlisted HTTPS API for safe Docker Compose lifecycle operations."""
import hmac
import json
import os
import socket
import ssl
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

TOKEN = os.environ.get("HERMES_DOCKER_OPERATOR_TOKEN", "")
PROJECTS_FILE = os.environ.get("HERMES_DOCKER_OPERATOR_PROJECTS_FILE", "")
PROJECTS = json.loads(Path(PROJECTS_FILE).read_text()) if PROJECTS_FILE else json.loads(
    os.environ.get("HERMES_DOCKER_PROJECTS", "{}"))
PORT = int(os.environ.get("HERMES_DOCKER_OPERATOR_PORT", "9443"))
CERT = os.environ.get("HERMES_DOCKER_OPERATOR_CERT", "/etc/hermes-docker-operator/tls.crt")
KEY = os.environ.get("HERMES_DOCKER_OPERATOR_KEY", "/etc/hermes-docker-operator/tls.key")
MAX_BODY = 8192
MAX_LOG_CHARS = 200_000
ALLOWED_ACTIONS = {"start", "stop", "restart", "up", "down"}
# Proyectos críticos (cloudflared, Infisical, Forgejo, Nexus, n8n): se pueden reiniciar pero nunca
# detener ni bajar desde Hermes, aunque el pedido venga aprobado.
NO_STOP_FILE = os.environ.get("HERMES_DOCKER_OPERATOR_NO_STOP_FILE", "/etc/hermes-docker-operator/no-stop.json")
NO_STOP = set(json.loads(Path(NO_STOP_FILE).read_text())) if Path(NO_STOP_FILE).is_file() else set()


def compose(project, args):
    if project not in PROJECTS:
        raise ValueError("unknown Compose project")
    root = Path(PROJECTS[project]).resolve(strict=True)
    compose_file = root / "compose.yaml"
    if not compose_file.is_file():
        compose_file = root / "docker-compose.yml"
    if not compose_file.is_file() or not compose_file.resolve().is_relative_to(root):
        raise ValueError("project has no approved Compose file")
    result = subprocess.run(["docker", "compose", "-p", project, "-f", str(compose_file), *args],
        cwd=root, capture_output=True, text=True, timeout=45, check=False)
    if result.returncode:
        raise RuntimeError("Docker Compose operation failed")
    return result.stdout


def project_services(project):
    output = compose(project, ["config", "--services"])
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def project_logs(project, service, lines):
    args = ["logs", "--no-color", "--tail", str(lines)]
    if service is not None:
        args.append(service)
    output = compose(project, args)
    return output[-MAX_LOG_CHARS:]


def project_status(project):
    services = project_services(project)
    output = compose(project, ["ps", "--format", "json"])
    try:
        decoded = json.loads(output)
        rows = decoded if isinstance(decoded, list) else [decoded]
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in output.splitlines() if line.strip()]
    return {"project": project, "services": services,
        "containers": [{k: row.get(k) for k in ("Name", "Service", "State", "Health", "Publishers")}
                       for row in rows if isinstance(row, dict)]}


def perform_action(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    project = request.get("project")
    service = request.get("service")
    action = request.get("action")
    if project not in PROJECTS:
        raise ValueError("unknown Compose project")
    if action not in ALLOWED_ACTIONS:
        raise ValueError("action must be start, stop, restart or up")
    if action in {"stop", "down"} and project in NO_STOP:
        raise ValueError("protected project: stop/down are not allowed")
    args = ["up", "-d"] if action == "up" else [action]
    if service is not None:
        if not isinstance(service, str) or service not in project_services(project):
            raise ValueError("unknown service for project")
        args.append(service)
    compose(project, args)
    return {"status": "accepted", "host": socket.gethostname(),
        "project": project, "service": service, "action": action}


class Handler(BaseHTTPRequestHandler):
    server_version = "OSCARComposeOperator/1.0"

    def log_message(self, fmt, *args):
        return

    def _authorized(self):
        supplied = self.headers.get("Authorization", "")
        expected = "Bearer " + TOKEN
        return bool(TOKEN) and hmac.compare_digest(supplied.encode(), expected.encode())

    def _reply(self, status, data):
        body = json.dumps(data, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > MAX_BODY:
            raise ValueError("invalid request size")
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        if not self._authorized():
            return self._reply(401, {"error": "unauthorized"})
        parsed = urlparse(self.path)
        if parsed.path == "/v1/projects":
            try:
                result = [project_status(name) for name in sorted(PROJECTS)]
                return self._reply(200, {"host": socket.gethostname(), "projects": result})
            except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired):
                return self._reply(502, {"error": "could not query Docker Compose"})
        if parsed.path == "/v1/logs":
            from urllib.parse import parse_qs
            query = parse_qs(parsed.query)
            project = (query.get("project") or [""])[0]
            service = (query.get("service") or [""])[0] or None
            try:
                lines = min(max(int((query.get("lines") or ["200"])[0]), 1), 1000)
            except ValueError:
                return self._reply(400, {"error": "lines must be an integer"})
            if project not in PROJECTS:
                return self._reply(400, {"error": "unknown Compose project"})
            if service is not None and service not in project_services(project):
                return self._reply(400, {"error": "unknown service for project"})
            try:
                output = project_logs(project, service, lines)
                return self._reply(200, {"project": project, "service": service, "logs": output})
            except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired):
                return self._reply(502, {"error": "could not fetch logs"})
        return self._reply(404, {"error": "not found"})

    def do_POST(self):
        if not self._authorized():
            return self._reply(401, {"error": "unauthorized"})
        if urlparse(self.path).path != "/v1/action":
            return self._reply(404, {"error": "not found"})
        try:
            self._reply(200, perform_action(self._body()))
        except (ValueError, TypeError, json.JSONDecodeError):
            self._reply(400, {"error": "invalid project, service, action or JSON"})
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            self._reply(502, {"error": "Docker Compose operation failed"})


def main():
    if not TOKEN or not PROJECTS:
        raise SystemExit("operator token and project allowlist are required")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(CERT, KEY)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
