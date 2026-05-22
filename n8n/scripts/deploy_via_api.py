#!/usr/bin/env python3
"""
Deploya los workflows del chatbot NeoKodex en n8n via la API REST.

Borra y recrea las credenciales de Postgres y OpenAI (para garantizar
config correcta y base URL de OpenRouter), crea los 3 workflows en orden
de dependencia, los wirea (sub-workflow ID, error workflow), y los activa.

Lee los JSONs generados por generate_workflows.py y los muta para inyectar
los IDs reales antes de POSTearlos.

Requiere variables de entorno:
  N8N_API_KEY    - JWT del usuario admin de n8n

Pasa las credenciales como argumentos o las lee del entorno:
  TELEGRAM_BOT_TOKEN
  OPENROUTER_API_KEY
  POSTGRES_PASSWORD
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib import request, error

N8N_BASE = "https://n8n-187-77-246-43.sslip.io/api/v1"
N8N_KEY = os.environ["N8N_API_KEY"]

ROOT = Path(__file__).resolve().parent.parent.parent
N8N_DIR = ROOT / "n8n"

CREDS = {
    "telegram_token": os.environ["TELEGRAM_BOT_TOKEN"],
    "openrouter_key": os.environ["OPENROUTER_API_KEY"],
    "postgres_password": os.environ["POSTGRES_PASSWORD"],
}


def api(method: str, path: str, body: dict | None = None) -> dict | list | None:
    url = f"{N8N_BASE}{path}"
    headers = {
        "X-N8N-API-KEY": N8N_KEY,
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except error.HTTPError as e:
        body_txt = e.read().decode("utf-8")
        print(f"  ! {method} {path} → HTTP {e.code}: {body_txt}", file=sys.stderr)
        raise


def list_credentials() -> list[dict]:
    res = api("GET", "/credentials")
    return res.get("data", []) if res else []


def list_workflows() -> list[dict]:
    res = api("GET", "/workflows")
    return res.get("data", []) if res else []


def delete_credentials_by_type(creds: list[dict], type_: str) -> None:
    for c in creds:
        if c["type"] == type_:
            print(f"  - Borrando credencial {c['id']} ({c['name']}, {c['type']})")
            api("DELETE", f"/credentials/{c['id']}")


def create_credential(name: str, type_: str, data: dict) -> str:
    res = api("POST", "/credentials", {"name": name, "type": type_, "data": data})
    print(f"  + Creada credencial {res['id']} ({name}, {type_})")
    return res["id"]


def delete_workflow_by_name(workflows: list[dict], name: str) -> None:
    for w in workflows:
        if w["name"] == name:
            print(f"  - Borrando workflow {w['id']} ({w['name']})")
            api("DELETE", f"/workflows/{w['id']}")


def patch_node_credentials(workflow: dict, mapping: dict[str, dict[str, str]]) -> None:
    """Reemplaza los IDs placeholder en los nodos por los IDs reales."""
    for node in workflow["nodes"]:
        if "credentials" not in node:
            continue
        for cred_type, cred_ref in node["credentials"].items():
            key = f"{node['name']}::{cred_type}"
            new = mapping.get(cred_type)
            if not new:
                continue
            cred_ref["id"] = new["id"]
            cred_ref["name"] = new["name"]


def patch_tool_workflow_id(workflow: dict, tool_node_name: str, sub_id: str) -> None:
    for node in workflow["nodes"]:
        if node["name"] == tool_node_name:
            node["parameters"]["workflowId"]["value"] = sub_id
            return


def load_workflow(filename: str) -> dict:
    """Carga el JSON y borra campos que la API rechaza al crear."""
    raw = json.loads((N8N_DIR / filename).read_text(encoding="utf-8"))
    for key in ("active", "tags", "pinData", "versionId", "id", "meta"):
        raw.pop(key, None)
    return raw


def create_workflow(workflow: dict) -> str:
    res = api("POST", "/workflows", workflow)
    print(f"  + Creado workflow {res['id']} ({res['name']})")
    return res["id"]


def activate_workflow(wid: str, name: str) -> None:
    api("POST", f"/workflows/{wid}/activate")
    print(f"  ✓ Activado {name} ({wid})")


def set_error_workflow(wid: str, error_id: str) -> None:
    """Asigna errorWorkflow al workflow. PUT solo acepta {name, nodes,
    connections, settings, staticData}."""
    wf = api("GET", f"/workflows/{wid}")
    wf.setdefault("settings", {})["errorWorkflow"] = error_id
    body = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
        "settings": wf["settings"],
    }
    api("PUT", f"/workflows/{wid}", body)
    print(f"  ✓ Error workflow asignado en {wid} → {error_id}")


def main():
    print("\n[1/6] Inventario de credenciales y workflows existentes...")
    creds = list_credentials()
    for c in creds:
        print(f"      cred  {c['id']}  type={c['type']}  name={c['name']!r}")
    wfs = list_workflows()
    for w in wfs:
        print(f"      wf    {w['id']}  active={w['active']}  name={w['name']!r}")

    print("\n[2/6] Limpiando credenciales viejas (Postgres y OpenAI) y workflows previos...")
    delete_credentials_by_type(creds, "postgres")
    delete_credentials_by_type(creds, "openAiApi")
    # Mantenemos la de Telegram si existe (Pietro la creó bien).
    delete_workflow_by_name(wfs, "Chatbot NeoKodex")
    delete_workflow_by_name(wfs, "Tool - Escalar a Humano")
    delete_workflow_by_name(wfs, "Error - Chatbot NeoKodex")

    # Telegram: reusamos la existente si la hay; si no, la creamos
    tg_existing = [c for c in creds if c["type"] == "telegramApi"]
    if tg_existing:
        tg_id = tg_existing[0]["id"]
        tg_name = tg_existing[0]["name"]
        print(f"      = Reusando Telegram credencial {tg_id} ({tg_name})")
    else:
        tg_id = create_credential(
            "NeoKodex Bot",
            "telegramApi",
            {"accessToken": CREDS["telegram_token"]},
        )
        tg_name = "NeoKodex Bot"

    print("\n[3/6] Creando credenciales nuevas (Postgres + OpenRouter)...")
    pg_id = create_credential(
        "n8n Postgres",
        "postgres",
        {
            "host": "n8n-postgres",
            "database": "n8n",
            "user": "n8n",
            "password": CREDS["postgres_password"],
            "port": 5432,
            "ssl": "disable",
            "allowUnauthorizedCerts": False,
            "sshTunnel": False,
        },
    )
    or_id = create_credential(
        "OpenRouter",
        "openAiApi",
        {
            "apiKey": CREDS["openrouter_key"],
            "url": "https://openrouter.ai/api/v1",
            "header": False,
            "allowedHttpRequestDomains": "all",
        },
    )

    cred_map = {
        "telegramApi": {"id": tg_id, "name": tg_name},
        "postgres": {"id": pg_id, "name": "n8n Postgres"},
        "openAiApi": {"id": or_id, "name": "OpenRouter"},
    }

    print("\n[4/6] Creando sub-workflow 'Tool - Escalar a Humano'...")
    escalar_wf = load_workflow("workflow-escalar.json")
    patch_node_credentials(escalar_wf, cred_map)
    escalar_id = create_workflow(escalar_wf)

    print("\n[5/6] Creando workflow de error y workflow principal...")
    error_wf = load_workflow("workflow-error.json")
    patch_node_credentials(error_wf, cred_map)
    error_id = create_workflow(error_wf)

    main_wf = load_workflow("workflow-chatbot.json")
    patch_node_credentials(main_wf, cred_map)
    patch_tool_workflow_id(main_wf, "Call escalar_a_humano", escalar_id)
    main_id = create_workflow(main_wf)

    print("\n[6/6] Activando workflows y wireando error handler...")
    activate_workflow(escalar_id, "Tool - Escalar a Humano")
    activate_workflow(error_id, "Error - Chatbot NeoKodex")
    set_error_workflow(main_id, error_id)
    # Re-cargar y activar el main (algunas versiones requieren activar después del PUT)
    activate_workflow(main_id, "Chatbot NeoKodex")

    print("\n✅ Deploy completo.")
    print(f"   Sub-workflow (escalar): {escalar_id}")
    print(f"   Error handler:          {error_id}")
    print(f"   Main workflow:          {main_id}")
    print(f"\n   Prueba el bot en Telegram: @NeokodexBot")


if __name__ == "__main__":
    main()
