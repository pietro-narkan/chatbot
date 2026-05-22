# Chatbot de Telegram para NeoKodex — Diseño

**Fecha:** 2026-05-22
**Estado:** Diseño aprobado, pendiente de plan de implementación
**Autor:** Pietro (NeoKodex) + Claude Code

---

## 1. Objetivo

Construir un chatbot de Telegram para la agencia NeoKodex que:

1. Responde FAQs sobre los servicios de Meta Ads de NeoKodex en español.
2. Escala a humano (Pietro) cuando detecta intención de compra, petición explícita de contacto, o no puede responder.

**Restricciones:**
- Coste objetivo: **0 €/mes** durante la fase de pruebas (VPS propio + modelo gratis de OpenRouter).
- Tiempo de deploy objetivo: **< 1 día** de trabajo total.
- Cero código custom mantenido: la lógica vive en un workflow de n8n versionado.

---

## 2. Arquitectura

### Diagrama

```
Usuario (Telegram)
       │
       ▼
Bot de Telegram (BotFather)
       │ webhook
       ▼
n8n (Coolify, VPS 187.77.246.43)
  ├─ Telegram Trigger
  ├─ AI Agent
  │    ├─ Model: OpenRouter (Gemini 2.0 Flash free)
  │    ├─ Memory: Postgres window buffer (por chat_id)
  │    └─ Tools: escalar_a_humano
  └─ Send Telegram → Usuario
       │
       └─ Si escalar_a_humano se invoca:
             Send Telegram → Pietro (chat_id personal)
```

### Componentes

| Componente | Tecnología | Dónde corre | Coste |
|---|---|---|---|
| Bot frontend | Telegram Bot API | Telegram cloud | 0 € |
| Orquestador | n8n self-hosted | Coolify (VPS) | 0 € |
| Base de datos | Postgres 16 | Coolify (junto a n8n) | 0 € |
| LLM | Gemini 2.0 Flash (free) vía OpenRouter | OpenRouter cloud | 0 € (rate-limited) |
| Reverse proxy / HTTPS | Traefik (incluido en Coolify) | Coolify (VPS) | 0 € |
| Knowledge base | Archivo `.md` en git | Repo local + system prompt | 0 € |

**Modelo LLM por defecto:** `google/gemini-2.0-flash-exp:free`.
**Fallback si rate limit:** `deepseek/deepseek-chat-v3:free` o `meta-llama/llama-3.3-70b-instruct:free`.

---

## 3. Flujos

### 3.1 Flujo normal (FAQ)

1. Usuario envía mensaje al bot en Telegram.
2. Telegram dispara webhook a `https://n8n.<dominio>/webhook/telegram-bot`.
3. n8n recupera historial reciente de Postgres (últimos N=10 mensajes del mismo `chat_id`).
4. AI Agent llama a OpenRouter con: `system_prompt` (FAQs NeoKodex) + `history` + `user_message`.
5. n8n guarda el par mensaje/respuesta en Postgres.
6. n8n envía respuesta al usuario por Telegram.

### 3.2 Flujo de escalación a humano

El AI Agent tiene una tool definida: `escalar_a_humano(motivo: string, resumen: string)`.

El modelo debe invocarla cuando:
- El usuario pide explícitamente hablar con una persona.
- El usuario muestra intención de compra clara (preguntas sobre precios cerrados, propuesta concreta, "queremos empezar").
- El bot no puede responder algo importante (queda fuera del knowledge base y el usuario insiste).

Al invocarse la tool:
1. n8n envía un mensaje a `TELEGRAM_OWNER_CHAT_ID` (chat ID personal de Pietro) con:
   - Username + nombre del lead (o "Sin username" si no tiene)
   - Motivo de la escalación
   - Resumen de la conversación generado por el LLM
   - Link directo al chat: `tg://user?id=<user_id>` (o `https://t.me/<username>`)
2. n8n responde al usuario: "Perfecto, Pietro te contacta en breve. Mientras, ¿hay algo más en lo que pueda ayudarte?"

### 3.3 Manejo de errores

| Escenario | Respuesta |
|---|---|
| OpenRouter caído / 5xx | "Estoy teniendo problemas técnicos. Escríbele directamente a Pietro: @<USERNAME>." |
| Rate limit del modelo free (429) | n8n usa un nodo `If` que detecta el error y reintenta con `OPENROUTER_MODEL_FALLBACK`. Si también falla, mensaje técnico de arriba. **Nota:** n8n AI Agent node no tiene fallback automático; lo implementamos como rama del workflow. |
| Mensaje no-texto (foto, audio, sticker) | "Por ahora solo proceso texto, mándame tu pregunta escrita." |
| Error inesperado en n8n | Mensaje técnico + notificar a Pietro por Telegram con el `execution_id` para debug. |

---

## 4. Knowledge base

**Ubicación:** `knowledge/neokodex-faq.md` en el repo local.

**Formato:** Markdown estructurado en secciones (Servicios, Precios, Proceso, Casos, Contacto, etc.).

**Cómo se aplica:** El contenido se incrusta directamente en el campo `system_prompt` del nodo AI Agent dentro del workflow de n8n. El template vive en `n8n/system-prompt.md` y el resultado final (template + FAQ concatenados) se pega en el workflow al exportarlo.

**Edición (proceso explícito):**
1. Pietro edita `knowledge/neokodex-faq.md` en local.
2. Pietro abre n8n, edita el system prompt del nodo AI Agent (copia/pega el FAQ actualizado).
3. Pietro exporta el workflow a `n8n/workflow-chatbot.json` y commitea.

Este proceso manual es aceptable para MVP. Si la edición se hace frecuente, automatizar con un script que regenere el workflow JSON desde el template — fuera de scope de este spec.

**Crecimiento futuro:** Si el knowledge base supera ~20k tokens o requiere búsqueda semántica, migrar a RAG con Qdrant (también deployable en Coolify). **Fuera del alcance de este spec.**

---

## 5. System prompt (esqueleto)

```
Eres el asistente virtual de NeoKodex, agencia especializada en Meta Ads
(Facebook e Instagram) basada en España.

PERSONALIDAD:
- Profesional pero cercano. Tuteas siempre.
- Responde en español. Si el usuario escribe en otro idioma, responde en ese idioma.
- Conciso: 2-4 frases por respuesta salvo que pidan algo detallado.
- Nunca inventes precios, plazos ni servicios que no estén en el knowledge base.

OBJETIVO:
- Responder dudas sobre los servicios de NeoKodex.
- Detectar leads cualificados y escalar a Pietro (humano).

CUÁNDO ESCALAR (usa la tool escalar_a_humano):
- El usuario pide hablar con una persona.
- El usuario muestra intención de compra clara.
- El usuario te pregunta algo importante que no sabes responder con seguridad.

CONOCIMIENTO DE NEOKODEX:
{{contenido de knowledge/neokodex-faq.md}}
```

---

## 6. Variables de entorno y secretos

Necesarios en n8n (Settings → Credentials o variables):

| Variable | Origen | Uso |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather | Token del bot de Telegram |
| `TELEGRAM_OWNER_CHAT_ID` | Tu chat ID personal (vía `@userinfobot`) | A quién notificar las escalaciones |
| `OPENROUTER_API_KEY` | openrouter.ai/keys | Llamadas al LLM |
| `OPENROUTER_MODEL_PRIMARY` | `google/gemini-2.0-flash-exp:free` | Modelo principal |
| `OPENROUTER_MODEL_FALLBACK` | `deepseek/deepseek-chat-v3:free` | Fallback ante rate limit |

**Notas de seguridad:**
- El token de Coolify compartido en chat (`2|6hDd3...`) debe ser **rotado** antes de poner el bot en producción.
- Nunca commitear tokens reales al repo. Usar `.env.example` con placeholders.

---

## 7. Estructura del repositorio

```
/home/pietro/Escritorio/chatbot/
├── README.md                          # Guía de deploy y mantenimiento
├── CLAUDE.md                          # Contexto para futuras sesiones de Claude Code
├── .env.example                       # Plantilla de variables (sin secretos)
├── .gitignore                         # Ignora .env, node_modules, etc.
│
├── knowledge/
│   └── neokodex-faq.md                  # FAQs editables (fuente de verdad del KB)
│
├── n8n/
│   ├── workflow-chatbot.json          # Workflow exportado (versionado en git)
│   ├── system-prompt.md               # Template del system prompt
│   └── README.md                      # Cómo importar/exportar el workflow
│
├── coolify/
│   └── deploy-notes.md                # Pasos para deployar n8n en Coolify
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-22-chatbot-telegram-n8n-design.md   # este archivo
```

---

## 8. Stack de Claude Code

**Skills (en orden de uso):**
1. `superpowers:brainstorming` — diseño (esta sesión).
2. `superpowers:writing-plans` — siguiente paso, plan de implementación.
3. `superpowers:executing-plans` — al implementar.
4. `superpowers:verification-before-completion` — antes de declarar listo.
5. `commit-commands:commit` — commits limpios por fase.
6. `verify` — para probar el bot end-to-end después del deploy.

**Agentes según necesidad:**
- `general-purpose` — research de modelos OpenRouter gratis activos y sus rate limits.
- `Explore` — solo si crece el codebase.

**MCP servers aprovechables:**
- `context7` — docs frescas de n8n, OpenRouter, Telegram Bot API.
- `chrome-devtools` — debug del panel de n8n/Coolify si hay UI bugs.

**Lo que NO necesitamos:**
- Frontend (no hay UI propia, todo es Telegram).
- TDD estricto (la lógica vive en JSON de n8n, no en código).
- Vector DB / RAG (system prompt cubre el caso de uso actual).

---

## 9. Criterios de éxito (MVP)

El MVP se considera listo cuando:

1. Un mensaje a `@<bot_username>` recibe respuesta en < 5 segundos en condiciones normales.
2. El bot recuerda el contexto del usuario durante al menos 10 mensajes seguidos.
3. Cuando el usuario escribe "quiero hablar con alguien", Pietro recibe una notificación en su Telegram personal con el resumen.
4. Si OpenRouter falla, el usuario recibe el mensaje de fallback (no un timeout silencioso).
5. El workflow está exportado a `n8n/workflow-chatbot.json` y commiteado al repo.
6. El `README.md` permite a un tercero re-deployar todo siguiendo solo el documento.

---

## 10. Fuera de alcance (explícito)

Estas cosas se sacan del MVP para mantener el scope:

- ❌ Calendly / Google Calendar para agendar reuniones automáticamente.
- ❌ CRM (HubSpot, Notion, Airtable) para guardar leads automáticamente.
- ❌ Multi-canal (WhatsApp, web widget, Instagram DMs).
- ❌ Multi-idioma estructurado (el LLM ya responde en cualquier idioma del usuario, pero no hay routing por idioma).
- ❌ Analytics / dashboards.
- ❌ RAG con base vectorial.
- ❌ Voice notes (Whisper STT).

Cada una de estas puede ser una extensión futura, una vez validado el MVP.

---

## 11. Riesgos conocidos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Rate limit del modelo free | Alta | Medio | Fallback configurado + plan B: pagar ~5 €/mes en OpenRouter |
| Coolify se cae | Baja | Alto | Es VPS de pruebas, asumido |
| Telegram bloquea el bot por spam | Baja | Alto | No hacer broadcasts, solo responder mensajes entrantes |
| El LLM alucina precios/servicios | Media | Alto | System prompt explícito: "nunca inventes precios" + escalar si no sabe |
| Token de Coolify expuesto en chat | Confirmado | Alto | **Rotar token al terminar el setup** |
