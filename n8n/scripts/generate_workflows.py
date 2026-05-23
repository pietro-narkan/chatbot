#!/usr/bin/env python3
"""
Genera los workflows de n8n para el chatbot de NeoKodex.

Lee:
  - ../system-prompt.md (template del system message)
  - ../../knowledge/neokodex-faq.md (FAQ que se incrusta en el prompt)

Escribe:
  - ../workflow-chatbot.json    (workflow principal)
  - ../workflow-escalar.json    (sub-workflow llamado por la tool)
  - ../workflow-error.json      (error handler global)

Uso:
    python3 n8n/scripts/generate_workflows.py
"""

import json
import os
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
N8N_DIR = ROOT / "n8n"
KNOWLEDGE = ROOT / "knowledge" / "neokodex-faq.md"
PROMPT_TEMPLATE = N8N_DIR / "system-prompt.md"

# El chat_id de Pietro (donde llegan las escalaciones y errores).
# Se hardcodea en el sub-workflow porque n8n no tiene .env per-workflow.
PIETRO_CHAT_ID = "8216883671"
PIETRO_USERNAME = "pietromrx"  # placeholder, se puede editar en el JSON


def build_system_message() -> str:
    """Lee el template del system prompt y lo rellena con el FAQ."""
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    faq = KNOWLEDGE.read_text(encoding="utf-8")

    # El template tiene este formato:
    #   # System Prompt — Chatbot NeoKodex
    #   ...explicación markdown...
    #   ```
    #   Eres el asistente virtual...
    #   {{ AQUÍ_VA_EL_CONTENIDO_DE_neokodex-faq.md }}
    #   ```
    # Extraemos lo que está dentro de los triple-backticks.
    parts = template.split("```")
    if len(parts) < 3:
        raise SystemExit(
            "system-prompt.md no tiene un bloque de código con el prompt. Revisa el formato."
        )
    prompt_body = parts[1].strip()
    if "{{ AQUÍ_VA_EL_CONTENIDO_DE_neokodex-faq.md }}" not in prompt_body:
        raise SystemExit(
            "system-prompt.md no contiene el placeholder {{ AQUÍ_VA_EL_CONTENIDO_DE_neokodex-faq.md }}"
        )
    return prompt_body.replace(
        "{{ AQUÍ_VA_EL_CONTENIDO_DE_neokodex-faq.md }}",
        faq.strip(),
    )


def new_id() -> str:
    return str(uuid.uuid4())


def build_escalar_workflow() -> dict:
    """Sub-workflow: recibe los params de la tool y notifica a Pietro."""
    trigger_id = new_id()
    notify_id = new_id()

    return {
        "name": "Tool - Escalar a Humano",
        "nodes": [
            {
                "parameters": {
                    "workflowInputs": {
                        "values": [
                            {"name": "motivo", "type": "string"},
                            {"name": "resumen", "type": "string"},
                            {"name": "user_id", "type": "string"},
                            {"name": "username", "type": "string"},
                            {"name": "chat_id", "type": "string"},
                        ]
                    }
                },
                "id": trigger_id,
                "name": "When Executed by Another Workflow",
                "type": "n8n-nodes-base.executeWorkflowTrigger",
                "typeVersion": 1.1,
                "position": [240, 300],
            },
            {
                "parameters": {
                    "chatId": PIETRO_CHAT_ID,
                    "text": (
                        "=🚨 Escalación de lead en NeoKodexBot\n\n"
                        "Usuario: @{{ $json.username }} (id: {{ $json.user_id }})\n"
                        "Motivo: {{ $json.motivo }}\n\n"
                        "Resumen:\n{{ $json.resumen }}\n\n"
                        "Abrir chat: tg://user?id={{ $json.user_id }}"
                    ),
                    "additionalFields": {},
                },
                "id": notify_id,
                "name": "Notify Pietro",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [560, 300],
                "credentials": {
                    "telegramApi": {
                        "id": "PASTE_TELEGRAM_CRED_ID_HERE",
                        "name": "NeoKodex Bot",
                    }
                },
            },
        ],
        "connections": {
            "When Executed by Another Workflow": {
                "main": [
                    [{"node": "Notify Pietro", "type": "main", "index": 0}]
                ]
            }
        },
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "meta": {"instanceId": "neokodex-chatbot"},
    }


def build_main_workflow(system_message: str) -> dict:
    """Workflow principal: Telegram → AI Agent → respuesta."""
    trigger_id = new_id()
    agent_id = new_id()
    model_id = new_id()
    memory_id = new_id()
    tool_id = new_id()
    send_id = new_id()

    return {
        "name": "Chatbot NeoKodex",
        "nodes": [
            {
                "parameters": {
                    "updates": ["message"],
                    "additionalFields": {},
                },
                "id": trigger_id,
                "name": "Telegram Trigger",
                "type": "n8n-nodes-base.telegramTrigger",
                "typeVersion": 1.1,
                "position": [240, 400],
                "webhookId": new_id(),
                "credentials": {
                    "telegramApi": {
                        "id": "PASTE_TELEGRAM_CRED_ID_HERE",
                        "name": "NeoKodex Bot",
                    }
                },
            },
            {
                "parameters": {
                    "promptType": "define",
                    "text": "={{ $json.message.text || '(mensaje sin texto)' }}",
                    "options": {
                        "systemMessage": system_message,
                    },
                },
                "id": agent_id,
                "name": "AI Agent",
                "type": "@n8n/n8n-nodes-langchain.agent",
                "typeVersion": 1.7,
                "position": [560, 400],
            },
            {
                "parameters": {
                    "model": {
                        "__rl": True,
                        "value": "openai/gpt-oss-120b:free",
                        "mode": "list",
                        "cachedResultName": "openai/gpt-oss-120b:free",
                    },
                    "options": {
                        "temperature": 0.3,
                        "maxTokens": 1024,
                    },
                },
                "id": model_id,
                "name": "OpenRouter Chat Model",
                "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                "typeVersion": 1.2,
                "position": [460, 620],
                "credentials": {
                    "openAiApi": {
                        "id": "PASTE_OPENROUTER_CRED_ID_HERE",
                        "name": "OpenRouter",
                    }
                },
            },
            {
                "parameters": {
                    "sessionIdType": "customKey",
                    "sessionKey": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
                    "contextWindowLength": 10,
                    "tableName": "n8n_chat_histories",
                },
                "id": memory_id,
                "name": "Postgres Chat Memory",
                "type": "@n8n/n8n-nodes-langchain.memoryPostgresChat",
                "typeVersion": 1.3,
                "position": [600, 620],
                "credentials": {
                    "postgres": {
                        "id": "PASTE_POSTGRES_CRED_ID_HERE",
                        "name": "n8n Postgres",
                    }
                },
            },
            {
                "parameters": {
                    "name": "escalar_a_humano",
                    "description": (
                        "Notifica a Pietro (humano) que este lead necesita atención personal. "
                        "Úsala cuando el usuario: (a) pida explícitamente hablar con una persona, "
                        "(b) muestre intención de compra clara (pide presupuesto cerrado, quiere "
                        "empezar, pide la sesión gratuita), o (c) pregunte algo importante que no "
                        "sabes responder con seguridad usando tu conocimiento."
                    ),
                    "workflowId": {
                        "__rl": True,
                        "value": "PASTE_ESCALAR_WORKFLOW_ID_HERE",
                        "mode": "id",
                    },
                    "workflowInputs": {
                        "mappingMode": "defineBelow",
                        "value": {
                            "motivo": "={{ $fromAI('motivo', 'Motivo breve por el que escalas este lead', 'string') }}",
                            "resumen": "={{ $fromAI('resumen', 'Resumen de 2-3 frases de la conversación, incluyendo nombre y empresa si los mencionó', 'string') }}",
                            "user_id": "={{ $('Telegram Trigger').item.json.message.from.id }}",
                            "username": "={{ $('Telegram Trigger').item.json.message.from.username || 'sin_username' }}",
                            "chat_id": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
                        },
                        "matchingColumns": [],
                        "schema": [
                            {"id": "motivo", "displayName": "motivo", "required": False, "type": "string", "removed": False},
                            {"id": "resumen", "displayName": "resumen", "required": False, "type": "string", "removed": False},
                            {"id": "user_id", "displayName": "user_id", "required": False, "type": "string", "removed": False},
                            {"id": "username", "displayName": "username", "required": False, "type": "string", "removed": False},
                            {"id": "chat_id", "displayName": "chat_id", "required": False, "type": "string", "removed": False},
                        ],
                        "attemptToConvertTypes": False,
                        "convertFieldsToString": True,
                    },
                },
                "id": tool_id,
                "name": "Call escalar_a_humano",
                "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
                "typeVersion": 2.2,
                "position": [760, 620],
            },
            {
                "parameters": {
                    "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
                    "text": "={{ $json.output }}",
                    "additionalFields": {
                        "appendAttribution": False,
                    },
                },
                "id": send_id,
                "name": "Reply to User",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [880, 400],
                "credentials": {
                    "telegramApi": {
                        "id": "PASTE_TELEGRAM_CRED_ID_HERE",
                        "name": "NeoKodex Bot",
                    }
                },
            },
        ],
        "connections": {
            "Telegram Trigger": {
                "main": [[{"node": "AI Agent", "type": "main", "index": 0}]]
            },
            "AI Agent": {
                "main": [[{"node": "Reply to User", "type": "main", "index": 0}]]
            },
            "OpenRouter Chat Model": {
                "ai_languageModel": [
                    [{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]
                ]
            },
            "Postgres Chat Memory": {
                "ai_memory": [
                    [{"node": "AI Agent", "type": "ai_memory", "index": 0}]
                ]
            },
            "Call escalar_a_humano": {
                "ai_tool": [
                    [{"node": "AI Agent", "type": "ai_tool", "index": 0}]
                ]
            },
        },
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "meta": {"instanceId": "neokodex-chatbot"},
    }


def build_error_workflow() -> dict:
    """Error handler global: notifica a Pietro cuando algo falla."""
    trigger_id = new_id()
    notify_id = new_id()

    return {
        "name": "Error - Chatbot NeoKodex",
        "nodes": [
            {
                "parameters": {},
                "id": trigger_id,
                "name": "Error Trigger",
                "type": "n8n-nodes-base.errorTrigger",
                "typeVersion": 1,
                "position": [240, 300],
            },
            {
                "parameters": {
                    "chatId": PIETRO_CHAT_ID,
                    "text": (
                        "=⚠️ Error en Chatbot NeoKodex\n\n"
                        "Workflow: {{ $json.workflow.name }}\n"
                        "Nodo que falló: {{ $json.execution.error.node.name || 'desconocido' }}\n"
                        "Mensaje: {{ $json.execution.error.message }}\n"
                        "Execution ID: {{ $json.execution.id }}\n\n"
                        "Revisa en n8n: {{ $json.execution.url }}"
                    ),
                    "additionalFields": {},
                },
                "id": notify_id,
                "name": "Notify Pietro of Error",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [560, 300],
                "credentials": {
                    "telegramApi": {
                        "id": "PASTE_TELEGRAM_CRED_ID_HERE",
                        "name": "NeoKodex Bot",
                    }
                },
            },
        ],
        "connections": {
            "Error Trigger": {
                "main": [[{"node": "Notify Pietro of Error", "type": "main", "index": 0}]]
            }
        },
        "active": False,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "meta": {"instanceId": "neokodex-chatbot"},
    }


def main():
    system_message = build_system_message()
    print(f"System message: {len(system_message)} caracteres")

    workflows = {
        "workflow-escalar.json": build_escalar_workflow(),
        "workflow-chatbot.json": build_main_workflow(system_message),
        "workflow-error.json": build_error_workflow(),
    }

    for filename, content in workflows.items():
        path = N8N_DIR / filename
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        print(f"  → {path.relative_to(ROOT)} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
