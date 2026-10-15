"""oscar-approvals: las acciones delicadas de O.S.C.A.R. esperan un botón en Discord.

Decisión del dueño (2026-10-15): todo lo que puede cortar un servicio, borrar algo, desplegar o
tocar la seguridad de la casa pide aprobación antes de ejecutarse. El hook devuelve "approve" y
Hermes muestra su tarjeta nativa con botones (Allow Once / Deny) solo a los usuarios autorizados;
si nadie responde dentro de approvals.timeout, la acción no se ejecuta.

Cada pedido lleva una clave única: "Allow Session" o "Always Allow" no dejan aprobadas acciones
futuras, cada una vuelve a preguntar. Con /yolo activo las acciones delicadas se bloquean en vez
de saltear la aprobación.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Callable, Dict, Optional

# Dominios de Home Assistant que no pueden abrir la casa, cortar la seguridad ni disparar
# automatizaciones arbitrarias: luces, escenas, multimedia y ventiladores van sin aprobación.
HA_FREE_DOMAINS = {"light", "scene", "media_player", "fan"}


def _text(value: Any, limit: int = 120) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _vm_power(a):
    if a.get("action") == "start":
        return None
    names = {"shutdown": "Apagar", "stop": "Forzar el apagado de", "reboot": "Reiniciar"}
    return f"{names.get(a.get('action'), _text(a.get('action')))} la VM {a.get('vmid')}"


def _scale(a):
    if a.get("replicas") != 0:
        return None
    return f"Escalar a 0 (apagar) {a.get('kind', 'deployment')} {a.get('namespace')}/{a.get('name')}"


def _docker(a):
    if a.get("action") not in {"stop", "down"}:
        return None
    target = a.get("project") + (f"/{a.get('service')}" if a.get("service") else "")
    verb = "Detener" if a.get("action") == "stop" else "Bajar (down)"
    return f"{verb} {target} en {a.get('host')}"


def _ha(a):
    if a.get("domain") in HA_FREE_DOMAINS:
        return None
    return (f"Home Assistant: {a.get('domain')}.{a.get('service')} "
            f"{_text(a.get('service_data') or {}, 100)}")


RULES: Dict[str, Callable[[dict], Optional[str]]] = {
    "oscar_create_vm": lambda a: f"Crear la VM {a.get('vmid')} ({a.get('name')})",
    "oscar_delete_vm": lambda a: f"BORRAR la VM {a.get('vmid')}",
    "oscar_resize_vm": lambda a: f"Cambiar recursos de la VM {a.get('vmid')} "
                                 f"(cores={a.get('cores')}, memoria={a.get('memory_mib')} MiB)",
    "oscar_vm_power": _vm_power,
    "oscar_delete_workload": lambda a: f"BORRAR {a.get('kind', 'deployment')} {a.get('namespace')}/{a.get('name')}",
    "oscar_rollback_workload": lambda a: f"Rollback de {a.get('namespace')}/{a.get('name')} "
                                         f"a la revisión {a.get('revision')}",
    "oscar_scale_workload": _scale,
    "oscar_docker_service_action": _docker,
    "oscar_forgejo_merge_pull_request": lambda a: f"Fusionar el PR #{a.get('number')} en {a.get('repo')}",
    "oscar_forgejo_delete_branch": lambda a: f"Borrar la rama {a.get('branch')} de {a.get('repo')}",
    "oscar_ha_call_service": _ha,
    "oscar_adguard_add_rewrite": lambda a: f"DNS: agregar {a.get('domain')} → {a.get('answer')}",
    "oscar_adguard_remove_rewrite": lambda a: f"DNS: quitar {a.get('domain')} → {a.get('answer')}",
    "oscar_n8n_set_workflow_active": lambda a: (f"{'Activar' if a.get('active') else 'Desactivar'} "
                                                f"el workflow de n8n {a.get('workflow_id')}"),
}


def _rule_for(tool_name: str):
    # Las herramientas MCP llegan con prefijo de servidor (mcp__oscar__oscar_x o similar).
    for name, rule in RULES.items():
        if tool_name == name or tool_name.endswith("_" + name):
            return name, rule
    return None, None


def describe(tool_name: str, args: Any) -> Optional[str]:
    """Texto de la acción si requiere aprobación; None si puede ejecutarse directo."""
    name, rule = _rule_for(tool_name or "")
    if not rule:
        return None
    args = args if isinstance(args, dict) else {}
    try:
        return rule(args)
    except Exception:  # ante la duda, se pregunta
        return f"{name} {_text(args)}"


def _yolo_active() -> bool:
    try:
        from tools.approval import _yolo_active as active
        return bool(active())
    except Exception:
        return False


def _on_pre_tool_call(tool_name: str = "", args: Any = None, **_: Any) -> Optional[Dict[str, str]]:
    description = describe(tool_name, args)
    if description is None:
        return None
    if _yolo_active():
        return {"action": "block",
                "message": "BLOCKED: con /yolo activo las acciones delicadas de O.S.C.A.R. no se ejecutan. "
                           "Pedile al usuario que lo desactive con /yolo y volvé a intentar."}
    return {"action": "approve", "message": description,
            "rule_key": f"oscar:{uuid.uuid4().hex}"}


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
