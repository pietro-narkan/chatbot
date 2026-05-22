# Chatbot Telegram + n8n + OpenRouter — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deployar un chatbot de Telegram para Narkan que responde FAQs y escala leads cualificados a Pietro, usando n8n + OpenRouter en el VPS con Coolify ya instalado.

**Architecture:** Workflow de n8n con un AI Agent que llama a OpenRouter (modelo gratis), mantiene memoria por sesión en Postgres, y tiene una tool `escalar_a_humano` que notifica a Pietro por Telegram. Cero código custom; todo es configuración + un workflow JSON versionado.

**Tech Stack:** n8n (self-hosted en Coolify), Postgres 16 (auto-deployed por n8n), Telegram Bot API, OpenRouter API (Gemini 2.0 Flash free + DeepSeek free fallback).

**Convención del plan:**
- **Manual (Pietro):** pasos que Pietro hace en una UI externa (Telegram, Coolify, n8n web).
- **Claude Code:** pasos que Claude Code ejecuta vía Bash/Write/Edit.
- Comandos shell asumen `pwd = /home/pietro/Escritorio/chatbot`.

---

## File Structure

Archivos que se crean a lo largo del plan:

| Path | Responsabilidad | Quién lo crea |
|---|---|---|
| `.gitignore` | Excluir `.env`, archivos sensibles, basura del SO | Claude Code (Task 1) |
| `.env.example` | Plantilla de variables sin secretos | Claude Code (Task 1) |
| `README.md` | Guía de deploy y mantenimiento end-to-end | Claude Code (Task 11) |
| `CLAUDE.md` | Contexto para futuras sesiones de Claude Code | Claude Code (Task 11) |
| `knowledge/narkan-faq.md` | FAQs de Narkan (fuente de verdad del KB) | Pietro escribe contenido, Claude Code andamia (Task 2) |
| `n8n/system-prompt.md` | Template del system prompt | Claude Code (Task 7) |
| `n8n/workflow-chatbot.json` | Workflow exportado de n8n | Pietro exporta, Claude Code guía (Task 10) |
| `n8n/README.md` | Cómo importar/exportar el workflow | Claude Code (Task 10) |
| `coolify/deploy-notes.md` | Pasos de deploy en Coolify (referencia) | Claude Code (Task 3) |

---

## Tareas

### Task 1: Scaffold del repositorio local

**Files:**
- Create: `/home/pietro/Escritorio/chatbot/.gitignore`
- Create: `/home/pietro/Escritorio/chatbot/.env.example`

- [ ] **Step 1.1: Crear `.gitignore`** — *Claude Code*

Contenido:
```
# Secretos
.env
.env.local
*.key
*.pem

# Editores y SO
.DS_Store
.vscode/
.idea/
*.swp

# Backups de n8n
*.bak
```

- [ ] **Step 1.2: Crear `.env.example`** — *Claude Code*

Contenido:
```
# Telegram (BotFather → /newbot)
TELEGRAM_BOT_TOKEN=

# Telegram (chat_id personal de Pietro, obtener de @userinfobot)
TELEGRAM_OWNER_CHAT_ID=

# Telegram username de contacto (para mensajes de fallback)
TELEGRAM_OWNER_USERNAME=tuusername

# OpenRouter (openrouter.ai/keys)
OPENROUTER_API_KEY=

# Modelos
OPENROUTER_MODEL_PRIMARY=google/gemini-2.0-flash-exp:free
OPENROUTER_MODEL_FALLBACK=deepseek/deepseek-chat-v3:free
```

- [ ] **Step 1.3: Verificar archivos creados** — *Claude Code*

Run: `ls -la /home/pietro/Escritorio/chatbot/`
Expected: ambos archivos presentes.

- [ ] **Step 1.4: Commit** — *Claude Code*

```bash
git add .gitignore .env.example
git commit -m "chore: add gitignore and env template"
```

---

### Task 2: Andamiar `knowledge/narkan-faq.md`

**Files:**
- Create: `/home/pietro/Escritorio/chatbot/knowledge/narkan-faq.md`

- [ ] **Step 2.1: Crear estructura del knowledge base** — *Claude Code*

Contenido (Pietro luego rellena con info real):
```markdown
# Narkan — FAQ y Knowledge Base

## Qué es Narkan
Narkan es una agencia especializada en Meta Ads (Facebook e Instagram) que ayuda a [PERFIL DEL CLIENTE IDEAL: e-commerce, infoproductos, servicios, etc.] a [RESULTADO: escalar ventas, conseguir leads cualificados, etc.] mediante [METODOLOGÍA: Andromeda 2026-2027, ángulos persona-oferta, etc.].

## Servicios
### [Nombre del servicio 1]
- Qué incluye: ...
- Para quién: ...
- Inversión mínima recomendada en Ads: ...

### [Nombre del servicio 2]
- ...

## Precios
- Servicio 1: desde X €/mes
- Servicio 2: desde Y €/mes
- (NUNCA inventar. Si el lead pregunta algo no listado, escalar.)

## Proceso de trabajo
1. Llamada de descubrimiento (gratis, 30 min)
2. Auditoría de cuenta actual (si existe)
3. Propuesta personalizada
4. Onboarding
5. Lanzamiento y optimización continua

## Casos de éxito / clientes
- Cliente A (sector X): de €Y a €Z en N meses
- ...

## Preguntas frecuentes

### ¿Cuánto tardo en ver resultados?
...

### ¿Trabajáis con cualquier sector?
...

### ¿Qué necesito tener para empezar?
...

### ¿Puedo cancelar cuando quiera?
...

## Contacto humano
Si el lead quiere hablar contigo o necesita algo que no está aquí, el bot debe escalar usando la tool `escalar_a_humano`.
```

- [ ] **Step 2.2: Commit** — *Claude Code*

```bash
git add knowledge/narkan-faq.md
git commit -m "docs: scaffold narkan FAQ knowledge base"
```

- [ ] **Step 2.3: Rellenar contenido real** — *Manual (Pietro)*

Pietro edita `knowledge/narkan-faq.md` con la info real de Narkan: servicios, precios reales (o "consultar"), casos, etc. **Importante:** si no quieres listar precios públicamente, deja `Precios: consultar — el bot debe escalar`. El system prompt lo respetará.

- [ ] **Step 2.4: Commit del contenido real** — *Manual (Pietro)*

```bash
git add knowledge/narkan-faq.md
git commit -m "docs: add real Narkan FAQ content"
```

---

### Task 3: Documentar pasos de Coolify (referencia para el deploy)

**Files:**
- Create: `/home/pietro/Escritorio/chatbot/coolify/deploy-notes.md`

- [ ] **Step 3.1: Escribir `coolify/deploy-notes.md`** — *Claude Code*

Contenido:
````markdown
# Deploy de n8n en Coolify

## Pre-requisitos
- VPS con Coolify ya instalado y accesible (en este caso: http://187.77.246.43:8000)
- Acceso al panel de Coolify con tu usuario admin

## Pasos

### 1. Crear un nuevo proyecto en Coolify
1. Panel Coolify → **Projects** → **+ New Project**
2. Nombre: `chatbot-narkan`
3. Environment: `production`

### 2. Añadir n8n como servicio
1. Dentro del proyecto → **+ New Resource** → **Service**
2. Buscar `n8n` en el catálogo de servicios oficiales
3. Click → **Deploy**

Coolify auto-configura:
- Contenedor `n8nio/n8n:latest`
- Postgres 16 como base de datos
- Volumen persistente para `~/.n8n`
- Traefik como reverse proxy con HTTPS automático (si hay dominio)

### 3. Configurar el dominio (opcional pero recomendado)

**Opción A — Con dominio propio (recomendado):**
1. En el panel del servicio n8n → **Domains** → añadir `n8n.tudominio.com`
2. Crear registro DNS A apuntando a `187.77.246.43`
3. Coolify genera certificado Let's Encrypt automáticamente

**Opción B — Sin dominio (solo para probar):**
1. Acceder vía `http://187.77.246.43:<puerto-asignado>`
2. Telegram exige HTTPS para webhooks, así que en este caso necesitarás usar ngrok o cloudflared como túnel temporal. **Esta opción no es viable a largo plazo.**

### 4. Variables de entorno de n8n

En el panel del servicio → **Environment Variables** añadir:

```
N8N_HOST=n8n.tudominio.com
N8N_PROTOCOL=https
N8N_PORT=5678
WEBHOOK_URL=https://n8n.tudominio.com/
GENERIC_TIMEZONE=Europe/Madrid
N8N_DEFAULT_LOCALE=es
```

### 5. Deploy
1. Click **Deploy**
2. Esperar logs verdes (~2 min)
3. Acceder a la URL configurada
4. Crear el primer usuario admin de n8n

### 6. Verificación
- [ ] Panel de n8n accesible vía HTTPS
- [ ] Puedes crear un workflow vacío
- [ ] Postgres está corriendo (Coolify lo muestra como "running")

## Troubleshooting
- **Webhook no llega:** verifica que `WEBHOOK_URL` esté bien configurado y que el dominio resuelva al VPS.
- **n8n no arranca:** revisa logs en Coolify → Service → Logs. Causa común: puerto ocupado.
- **Telegram no envía mensajes:** los webhooks requieren HTTPS válido. Sin dominio → no funciona.
````

- [ ] **Step 3.2: Commit** — *Claude Code*

```bash
git add coolify/deploy-notes.md
git commit -m "docs: add Coolify n8n deploy notes"
```

- [ ] **Step 3.3: Ejecutar el deploy de n8n** — *Manual (Pietro)*

Sigue `coolify/deploy-notes.md` paso a paso. Esto requiere:
- Decisión: ¿usar dominio propio o túnel temporal?
- Click-ops en el panel de Coolify (no se puede automatizar sin acceso SSH y tocar Coolify API, lo dejamos manual)

- [ ] **Step 3.4: Verificar acceso a n8n** — *Manual (Pietro)*

Confirmar que entras al panel de n8n con un usuario admin. Anota la URL pública del panel (la necesitamos en Task 5).

---

### Task 4: Crear el bot en Telegram y obtener credenciales

- [ ] **Step 4.1: Crear bot con BotFather** — *Manual (Pietro)*

1. Abre Telegram → busca `@BotFather`
2. `/newbot`
3. Nombre visible: `Narkan Asistente` (o el que prefieras)
4. Username: `narkan_assistant_bot` (debe terminar en `bot` y ser único)
5. BotFather te devuelve un token tipo `1234567890:AAH...`

**Guarda el token en un sitio seguro temporalmente** (lo metes en n8n en Task 5).

- [ ] **Step 4.2: Configurar el bot (opcional pero recomendado)** — *Manual (Pietro)*

Con BotFather:
- `/setdescription` → "Asistente virtual de Narkan. Pregúntame por nuestros servicios de Meta Ads."
- `/setabouttext` → texto corto que aparece en el perfil
- `/setuserpic` → logo de Narkan
- `/setcommands` → 
  ```
  start - Iniciar conversación
  ayuda - Ver qué puedo hacer
  contacto - Hablar con Pietro
  ```

- [ ] **Step 4.3: Obtener tu chat_id personal** — *Manual (Pietro)*

1. Abre Telegram → busca `@userinfobot`
2. `/start`
3. Te devuelve tu `id` (numérico, ej: `123456789`)
4. **Anótalo:** este es `TELEGRAM_OWNER_CHAT_ID`

- [ ] **Step 4.4: Iniciar una conversación con tu bot** — *Manual (Pietro)*

1. Busca tu bot por su username (`@narkan_assistant_bot` o el que pusiste)
2. Click **Start** o envía `/start`
3. **Importante:** esto registra que tu chat existe; sin esto el bot no te puede mandar mensajes de escalación.

---

### Task 5: Crear cuenta y API key de OpenRouter

- [ ] **Step 5.1: Crear cuenta en OpenRouter** — *Manual (Pietro)*

1. Ve a https://openrouter.ai → Sign up (con Google o email)
2. Settings → **Keys** → **Create Key**
3. Nombre: `narkan-chatbot-prod`
4. Copia la key (`sk-or-v1-...`)

- [ ] **Step 5.2: Verificar que los modelos free están disponibles** — *Manual (Pietro)*

1. https://openrouter.ai/models → filtrar por "Free"
2. Confirmar que estos modelos aparecen y están activos:
   - `google/gemini-2.0-flash-exp:free`
   - `deepseek/deepseek-chat-v3:free`
3. **Si alguno no está disponible**, anótalo: usaremos otro free equivalente.

- [ ] **Step 5.3: Anotar credenciales en `.env` local** — *Manual (Pietro)*

```bash
cp /home/pietro/Escritorio/chatbot/.env.example /home/pietro/Escritorio/chatbot/.env
# Editar .env con los valores reales (vim/nano/code)
```

`.env` está en `.gitignore`, no se sube. Solo para referencia local.

---

### Task 6: Crear el workflow base en n8n (Telegram Trigger)

- [ ] **Step 6.1: Crear el workflow** — *Manual (Pietro)*

1. Panel n8n → **Workflows** → **+ Add workflow**
2. Nombre: `Chatbot Narkan`

- [ ] **Step 6.2: Añadir Telegram Trigger** — *Manual (Pietro)*

1. Click **+** → buscar `Telegram Trigger`
2. **Trigger On:** `Message`
3. **Credential:** crear nueva
   - Name: `Narkan Bot`
   - Access Token: pegar `TELEGRAM_BOT_TOKEN`
   - Save
4. **Save** el nodo

- [ ] **Step 6.3: Activar el workflow** — *Manual (Pietro)*

1. Toggle **Active** (esquina superior derecha)
2. n8n registra automáticamente el webhook en Telegram

- [ ] **Step 6.4: Test del webhook** — *Manual (Pietro)*

1. Desde Telegram, manda al bot: `hola test`
2. En n8n, abre el Telegram Trigger → tab **Executions**
3. Deberías ver el mensaje recibido con todos los campos (`message.text`, `message.from.id`, etc.)

**Si no llega:**
- Verifica que el bot está activado en BotFather (`/start` con el bot)
- Verifica `WEBHOOK_URL` en las env vars de n8n
- Verifica que tu dominio tiene HTTPS válido

- [ ] **Step 6.5: Añadir nodo respuesta de prueba (echo)** — *Manual (Pietro)*

1. Después del Telegram Trigger → **+** → `Telegram` (action node)
2. **Operation:** `Send Message`
3. **Chat ID:** `={{ $json.message.chat.id }}`
4. **Text:** `Recibido: {{ $json.message.text }}`
5. **Credential:** la misma `Narkan Bot`
6. Save

- [ ] **Step 6.6: Test end-to-end del echo** — *Manual (Pietro)*

1. Desde Telegram, manda `hola` al bot
2. El bot debe responder `Recibido: hola`
3. Si funciona: la pipeline Telegram ↔ n8n ↔ Telegram está OK

**Si no funciona:** revisar logs en n8n (Executions list).

---

### Task 7: Escribir el system prompt

**Files:**
- Create: `/home/pietro/Escritorio/chatbot/n8n/system-prompt.md`

- [ ] **Step 7.1: Crear template del system prompt** — *Claude Code*

Contenido:
````markdown
# System Prompt — Chatbot Narkan

Este es el system prompt que se inyecta en el AI Agent de n8n. La sección `## CONOCIMIENTO DE NARKAN` se reemplaza por el contenido íntegro de `knowledge/narkan-faq.md` antes de pegarlo en n8n.

---

```
Eres el asistente virtual oficial de Narkan, una agencia especializada en Meta Ads (Facebook e Instagram) basada en España.

# PERSONALIDAD
- Profesional pero cercano. Tutea siempre.
- Responde en español. Si el usuario escribe en otro idioma, responde en ese idioma.
- Conciso: 2-4 frases por respuesta salvo que el usuario pida algo detallado.
- Nunca inventes precios, plazos, servicios, ni casos de éxito que no estén explícitamente en el conocimiento de abajo.
- Si no sabes algo con seguridad: dilo y escala usando la tool `escalar_a_humano`.

# OBJETIVOS
1. Responder dudas sobre los servicios de Narkan usando el conocimiento de abajo.
2. Detectar leads cualificados y escalar a Pietro (humano) cuando proceda.

# CUÁNDO ESCALAR (usa la tool `escalar_a_humano`)
Invoca la tool cuando:
- El usuario pide explícitamente hablar con una persona ("quiero hablar con alguien", "ponme con Pietro", "pásame con un humano").
- El usuario muestra intención de compra clara: pregunta por una propuesta concreta, dice "queremos empezar", pide presupuesto a medida, o quiere agendar.
- El usuario pregunta algo importante que NO está en tu conocimiento y no puedes responder con seguridad.

NO escales por preguntas triviales que sí puedes responder con el conocimiento de abajo.

Cuando uses la tool, después de invocarla, responde al usuario:
"Perfecto, Pietro te contacta en breve. Mientras, ¿hay algo más en lo que pueda ayudarte?"

# CONOCIMIENTO DE NARKAN
{{ AQUÍ_VA_EL_CONTENIDO_DE_narkan-faq.md }}
```
````

- [ ] **Step 7.2: Commit** — *Claude Code*

```bash
git add n8n/system-prompt.md
git commit -m "docs: add system prompt template"
```

---

### Task 8: Añadir AI Agent al workflow de n8n

- [ ] **Step 8.1: Eliminar el nodo echo de prueba** — *Manual (Pietro)*

En el workflow de n8n, borrar el `Send Message` echo (lo añadimos en Task 6.5). Mantener el Telegram Trigger.

- [ ] **Step 8.2: Añadir nodo AI Agent** — *Manual (Pietro)*

1. Después del Telegram Trigger → **+** → buscar `AI Agent`
2. Seleccionar `AI Agent` (de LangChain category)

- [ ] **Step 8.3: Configurar Chat Model — OpenRouter** — *Manual (Pietro)*

1. En el AI Agent, click sobre el slot **Chat Model** debajo del nodo
2. Buscar `OpenAI Chat Model` (OpenRouter es compatible con la API de OpenAI)
3. **Credential:** crear nueva
   - Name: `OpenRouter`
   - API Key: tu `OPENROUTER_API_KEY`
   - **Base URL:** `https://openrouter.ai/api/v1`
   - Save
4. **Model:** escribir manualmente `google/gemini-2.0-flash-exp:free`
5. **Options → temperature:** `0.3` (respuestas más consistentes)
6. **Options → maxTokens:** `1024`

- [ ] **Step 8.4: Configurar Memory — Postgres** — *Manual (Pietro)*

n8n viene con Postgres en el mismo stack de Coolify. Vamos a reutilizarlo para guardar la memoria del chat.

1. En el AI Agent, click sobre el slot **Memory** debajo del nodo
2. Seleccionar `Postgres Chat Memory`
3. **Credential:** crear nueva conexión
   - Ir a Coolify → tu Project → servicio Postgres → tab **Configuration** → copiar **Host (Internal)**, **Database**, **Username**, **Password**, **Port**
   - En n8n pegar esos valores. El Host interno suele ser algo tipo `<service-uuid>-postgres` o `postgres`. Como n8n y Postgres están en la misma red de Docker en Coolify, usar el hostname interno (NO la IP pública).
   - SSL: `disable` (red interna)
   - Save
4. **Session ID:** `={{ $('Telegram Trigger').item.json.message.chat.id }}`
5. **Context Window Length:** `10`
6. **Table Name:** `chat_memory` (n8n la crea automáticamente la primera vez)

**Alternativa para MVP rápido:** si la conexión a Postgres da problemas, usar `Simple Memory` (en RAM). La memoria se pierde al reiniciar n8n, pero para probar funciona. Cambiar a Postgres después.

- [ ] **Step 8.5: Configurar el AI Agent** — *Manual (Pietro)*

1. **Agent:** `Conversational Agent`
2. **Prompt Type:** `Define below`
3. **Text:** `={{ $json.message.text }}`
4. **System Message:** pegar el system prompt completo de `n8n/system-prompt.md`, reemplazando `{{ AQUÍ_VA_EL_CONTENIDO_DE_narkan-faq.md }}` con el contenido íntegro de `knowledge/narkan-faq.md`.

- [ ] **Step 8.6: Añadir Send Message de respuesta** — *Manual (Pietro)*

1. Después del AI Agent → **+** → `Telegram` action
2. **Operation:** `Send Message`
3. **Chat ID:** `={{ $('Telegram Trigger').item.json.message.chat.id }}`
4. **Text:** `={{ $json.output }}`
5. Credential: `Narkan Bot`

- [ ] **Step 8.7: Test end-to-end del FAQ** — *Manual (Pietro)*

Desde Telegram, manda al bot:
1. `Hola`
2. `¿Qué servicios ofrecéis?`
3. `¿Cuánto cobráis?`

Verifica que:
- Responde en español
- Tono profesional/cercano
- Usa info del knowledge base
- No inventa precios

**Si responde mal:** revisar system prompt, contenido del FAQ, y temperature.

- [ ] **Step 8.8: Test de memoria** — *Manual (Pietro)*

Desde Telegram:
1. `Soy Juan de Acme SL`
2. `¿Recuerdas mi nombre?`

Debe responder algo como "Sí, Juan". Si no recuerda → revisar la configuración de Memory (Session ID y Context Window).

---

### Task 9: Añadir tool `escalar_a_humano`

- [ ] **Step 9.1: Añadir tool al AI Agent** — *Manual (Pietro)*

1. En el AI Agent, click sobre el slot **Tool** debajo del nodo
2. Seleccionar `Call n8n Workflow Tool` (ejecuta otro workflow como tool)
3. Esto requiere primero crear el sub-workflow → ir al Step 9.2

- [ ] **Step 9.2: Crear sub-workflow `Escalar a Humano`** — *Manual (Pietro)*

1. n8n → **Workflows** → **+ Add workflow**
2. Nombre: `Tool — Escalar a Humano`
3. Añadir nodo `Workflow Trigger` (`When called by another workflow`)
4. **Workflow Inputs:** definir:
   - `motivo` (string)
   - `resumen` (string)
   - `user_id` (string)
   - `username` (string)
   - `chat_id` (string)
5. Save

- [ ] **Step 9.3: Añadir nodo de notificación a Pietro** — *Manual (Pietro)*

En el sub-workflow:
1. Después del trigger → **+** → `Telegram` action
2. **Operation:** `Send Message`
3. **Chat ID:** `TELEGRAM_OWNER_CHAT_ID` (poner el valor numérico directamente; n8n no usa env vars del SO, configurar como Variable de workflow si quieres parametrizar)
4. **Text:**
   ```
   🚨 Escalación de lead

   Usuario: @{{ $json.username }} (id: {{ $json.user_id }})
   Motivo: {{ $json.motivo }}

   Resumen:
   {{ $json.resumen }}

   Abrir chat: tg://user?id={{ $json.user_id }}
   ```
   (Quita los emojis si prefieres.)
5. Credential: `Narkan Bot`
6. Save y **Active**

- [ ] **Step 9.4: Conectar la tool al AI Agent del workflow principal** — *Manual (Pietro)*

1. Volver al workflow `Chatbot Narkan`
2. AI Agent → slot **Tool** → `Call n8n Workflow Tool`
3. **Workflow:** seleccionar `Tool — Escalar a Humano`
4. **Tool Name:** `escalar_a_humano`
5. **Tool Description:** 
   ```
   Notifica a Pietro (humano) que este lead necesita atención. Úsala cuando el usuario pida hablar con una persona, muestre intención de compra clara, o preguntes algo importante que no sabes responder con seguridad.
   ```
6. **Workflow Inputs:** definir cada campo. En n8n los campos rellenados por la IA usan `$fromAI()`; los rellenados con contexto del trigger usan expresiones normales:
   - `motivo`: `={{ $fromAI('motivo', 'Motivo breve por el cual se escala este lead a un humano (ej: pidió contacto directo, intención de compra clara, pregunta fuera de scope)', 'string') }}`
   - `resumen`: `={{ $fromAI('resumen', 'Resumen de 2-3 frases de la conversación con el lead hasta ahora, incluyendo nombre/empresa si los mencionó', 'string') }}`
   - `user_id`: `={{ $('Telegram Trigger').item.json.message.from.id }}`
   - `username`: `={{ $('Telegram Trigger').item.json.message.from.username || 'sin_username' }}`
   - `chat_id`: `={{ $('Telegram Trigger').item.json.message.chat.id }}`
7. Save

- [ ] **Step 9.5: Test de escalación** — *Manual (Pietro)*

Desde Telegram, manda al bot: `quiero hablar con Pietro directamente`.

Esperado:
1. Pietro recibe en su Telegram personal un mensaje con el resumen.
2. El bot responde algo tipo: "Perfecto, Pietro te contacta en breve. Mientras, ¿hay algo más en lo que pueda ayudarte?"

**Si no escala:** revisar la descripción de la tool (el LLM decide cuándo invocarla basado en el texto descriptivo), y temperature del modelo.

---

### Task 10: Manejo de errores y fallback de modelo

- [ ] **Step 10.1: Crear Error Workflow** — *Manual (Pietro)*

Estrategia MVP: el error workflow solo notifica a Pietro. NO intenta responder al usuario (extraer su `chat_id` desde el contexto del error es complejo y poco fiable). Si una conversación rompe, Pietro lo ve en su Telegram y puede contactar al lead manualmente desde n8n.

1. n8n → **Workflows** → **+ Add workflow** → nombre: `Error — Chatbot Narkan`
2. Añadir nodo `Error Trigger`
3. Añadir nodo `Telegram` → Send Message con:
   - **Chat ID:** el valor numérico de `TELEGRAM_OWNER_CHAT_ID` (hardcoded, ej: `123456789`)
   - **Text:**
     ```
     ⚠️ Error en Chatbot Narkan

     Workflow: {{ $json.workflow.name }}
     Nodo que falló: {{ $json.execution.error.node.name }}
     Mensaje: {{ $json.execution.error.message }}
     Execution ID: {{ $json.execution.id }}

     Revisa en n8n: {{ $json.execution.url }}
     ```
   - **Credential:** `Narkan Bot`
4. Save y **Active**
5. En el workflow principal: **Settings** (engranaje arriba) → **Error Workflow** → seleccionar `Error — Chatbot Narkan` → Save

- [ ] **Step 10.2: Añadir fallback de modelo en el workflow principal** — *Manual (Pietro)*

n8n no soporta retry-with-fallback nativo en el AI Agent. Implementación pragmática para MVP:

**Opción simple (recomendada para MVP):**
- Dejar solo el modelo principal `gemini-2.0-flash-exp:free`.
- Si falla por rate limit (429), el Error Workflow envía el mensaje de fallback al usuario.
- Si los rate limits se vuelven un problema real, en una iteración futura: añadir un `If` node que detecte `error.statusCode === 429` y haga un segundo intento con DeepSeek (o pagar OpenRouter, ~5 €/mes).

**Razón:** implementar el fallback bien duplica complejidad del workflow (dos AI Agents en paralelo o branching). Para MVP es overkill. Documentar como extensión futura.

- [ ] **Step 10.3: Test del error handler** — *Manual (Pietro)*

Forzar un error: temporalmente pon una API key inválida en la credencial de OpenRouter y manda un mensaje. Esperado:
- El usuario NO recibe respuesta (el AI Agent falla)
- Pietro recibe en su Telegram personal el mensaje de error con el `execution_id`

Después restaurar la API key correcta.

**Limitación conocida:** el usuario se queda sin feedback. Si esto se vuelve un problema (muchas caídas), siguiente iteración: añadir un `Catch` con un `Send Message` al chat del usuario antes del Error Workflow.

---

### Task 11: Manejar mensajes no-texto

- [ ] **Step 11.1: Añadir If node antes del AI Agent** — *Manual (Pietro)*

1. Entre el Telegram Trigger y el AI Agent → **+** → `If`
2. **Condition:**
   - Value 1: `={{ $json.message.text }}`
   - Operation: `is not empty`
3. Conectar:
   - Rama `true` → AI Agent (flujo normal)
   - Rama `false` → Telegram Send Message con texto: "Por ahora solo proceso texto, mándame tu pregunta escrita."

- [ ] **Step 11.2: Test con mensaje no-texto** — *Manual (Pietro)*

Manda al bot:
- Una foto
- Un sticker
- Un audio

Debe responder en los 3 casos con el mensaje de "solo proceso texto".

---

### Task 12: Exportar workflow, escribir README y CLAUDE.md

- [ ] **Step 12.1: Exportar el workflow principal** — *Manual (Pietro)*

1. n8n → workflow `Chatbot Narkan` → menú `...` → **Download**
2. Guardar como `/home/pietro/Escritorio/chatbot/n8n/workflow-chatbot.json`

- [ ] **Step 12.2: Exportar el sub-workflow de escalación** — *Manual (Pietro)*

1. n8n → workflow `Tool — Escalar a Humano` → **Download**
2. Guardar como `/home/pietro/Escritorio/chatbot/n8n/workflow-escalar.json`

- [ ] **Step 12.3: Exportar el error workflow** — *Manual (Pietro)*

1. n8n → workflow `Error — Chatbot Narkan` → **Download**
2. Guardar como `/home/pietro/Escritorio/chatbot/n8n/workflow-error.json`

- [ ] **Step 12.4: Crear `n8n/README.md`** — *Claude Code*

Contenido:
````markdown
# Workflows de n8n

## Archivos
- `workflow-chatbot.json` — workflow principal (Telegram Trigger → AI Agent → Send Message)
- `workflow-escalar.json` — sub-workflow llamado por la tool `escalar_a_humano`
- `workflow-error.json` — error handler global
- `system-prompt.md` — template del system prompt usado en el AI Agent

## Importar en n8n
1. n8n → Workflows → menú `...` → **Import from File**
2. Importar en este orden:
   1. `workflow-escalar.json`
   2. `workflow-error.json`
   3. `workflow-chatbot.json`
3. Conectar credenciales:
   - `Narkan Bot` (Telegram Bot Token)
   - `OpenRouter` (API key + Base URL `https://openrouter.ai/api/v1`)
   - `Postgres` (auto-detecta el de Coolify si está en la misma red)
4. En el workflow principal: configurar **Error Workflow** = `Error — Chatbot Narkan`
5. Activar `workflow-escalar` y `workflow-chatbot`

## Editar el system prompt / knowledge base
1. Editar `../knowledge/narkan-faq.md` (fuente de verdad)
2. Editar el AI Agent del workflow principal: pegar el contenido actualizado del FAQ en la sección `# CONOCIMIENTO DE NARKAN` del system message
3. Save workflow → re-exportar a `workflow-chatbot.json`
4. Commitear

## Exportar después de cambios
1. n8n → workflow → `...` → Download
2. Reemplazar el JSON correspondiente
3. `git add n8n/*.json && git commit -m "chore: update n8n workflow"`
````

- [ ] **Step 12.5: Crear `README.md` raíz** — *Claude Code*

Contenido:
````markdown
# Chatbot Narkan (Telegram + n8n + OpenRouter)

Chatbot de Telegram para la agencia Narkan que responde FAQs sobre servicios de Meta Ads y escala leads cualificados a Pietro por Telegram.

## Stack
- **Telegram Bot API** — frontend
- **n8n** (self-hosted en Coolify) — orquestación
- **OpenRouter** (Gemini 2.0 Flash free) — LLM
- **Postgres 16** — memoria del bot por sesión

## Deploy desde cero
Sigue en orden:
1. `coolify/deploy-notes.md` — deployar n8n en Coolify
2. Crear bot en `@BotFather` (ver `docs/superpowers/plans/2026-05-22-chatbot-telegram-n8n.md` Task 4)
3. Crear cuenta OpenRouter y obtener API key (Task 5)
4. `n8n/README.md` — importar y configurar los workflows
5. Testing manual (ver Test plan más abajo)

## Mantenimiento
- **Cambiar FAQs:** editar `knowledge/narkan-faq.md` → actualizar system prompt en n8n → re-exportar workflow → commit
- **Cambiar de modelo:** AI Agent node → cambiar `Model` (probar primero con un mensaje)
- **Cambiar a quién escala:** sub-workflow `Tool — Escalar a Humano` → cambiar Chat ID

## Test plan
- [ ] El bot responde "¿Qué servicios ofrecéis?" usando el knowledge base
- [ ] El bot recuerda el nombre del usuario después de 5 mensajes
- [ ] Decir "quiero hablar con Pietro" → Pietro recibe notificación en su Telegram personal
- [ ] Mandar una foto al bot → responde "Por ahora solo proceso texto..."
- [ ] Si OpenRouter falla → mensaje de fallback al usuario

## Estructura
```
chatbot/
├── README.md                  # este archivo
├── CLAUDE.md                  # contexto para Claude Code
├── .env.example
├── knowledge/narkan-faq.md    # FAQ editable
├── n8n/                       # workflows exportados + system prompt
├── coolify/deploy-notes.md
└── docs/superpowers/          # spec + plan de implementación
```

## Costes
- VPS: ya pagado
- n8n + Postgres + Coolify: gratis (self-hosted)
- OpenRouter: gratis con modelos `:free` (rate-limited)
- Telegram Bot API: gratis

**Total: 0 €/mes en fase de pruebas.**

Si los rate limits del modelo free se vuelven un problema, OpenRouter de pago para este caso de uso ronda los 1-5 €/mes.

## Seguridad
- Nunca commitear `.env`. Está en `.gitignore`.
- Rotar el token de Coolify después de la sesión inicial (fue compartido en chat durante el setup).
- Las credenciales de n8n se guardan cifradas en su DB; no salen del VPS.
````

- [ ] **Step 12.6: Crear `CLAUDE.md`** — *Claude Code*

Contenido:
````markdown
# Contexto del proyecto para Claude Code

## Qué es esto
Chatbot de Telegram para la agencia Narkan (Pietro). Stack: n8n self-hosted en Coolify + OpenRouter (modelo gratis) + Telegram Bot API. Documentado en `README.md`.

## Cómo está organizado
- `knowledge/narkan-faq.md` — fuente de verdad del knowledge base. Si Pietro pide cambiar lo que sabe el bot, editar aquí primero, después el system prompt en n8n, después re-exportar el workflow.
- `n8n/*.json` — workflows exportados desde n8n. Son la fuente de verdad versionada.
- `n8n/system-prompt.md` — template del prompt. La sección `CONOCIMIENTO DE NARKAN` se rellena con el contenido de `knowledge/narkan-faq.md`.
- `coolify/deploy-notes.md` — cómo se deployó n8n en Coolify (referencia).
- `docs/superpowers/specs/` y `docs/superpowers/plans/` — diseño y plan de la implementación inicial.

## Trabajo típico
- "Cambia las FAQs" → editar `knowledge/narkan-faq.md`, recordar a Pietro actualizar el system prompt en n8n y re-exportar el JSON.
- "Añade una nueva tool al agente" → diseñar como sub-workflow en n8n, exportar JSON, documentar en `n8n/README.md`.
- "El bot no responde algo bien" → revisar system prompt + contenido del FAQ. Si falta info: añadirla al FAQ. Si es problema de prompting: ajustar el system prompt.

## Lo que NO hay aquí
- Código de aplicación (todo es config + JSON de n8n).
- Tests automatizados (es un workflow, los tests son manuales — ver Test plan en `README.md`).
- Frontend propio (todo es Telegram).

## Convenciones
- Commits convencionales (`feat:`, `fix:`, `docs:`, `chore:`).
- Cambios en workflows: siempre re-exportar el JSON y commitearlo.
- Secretos: nunca commitear. `.env.example` es la plantilla; el `.env` real solo en local/n8n.
````

- [ ] **Step 12.7: Commit final** — *Claude Code*

```bash
git add n8n/workflow-chatbot.json n8n/workflow-escalar.json n8n/workflow-error.json n8n/README.md README.md CLAUDE.md
git commit -m "feat: export n8n workflows and add project docs"
```

---

### Task 13: Verificación end-to-end (test plan)

- [ ] **Step 13.1: Test FAQ básico** — *Manual (Pietro)*

Mandar al bot:
- `Hola` → debe saludar
- `¿Qué hacéis en Narkan?` → debe responder con info del FAQ
- `¿Trabajáis con ecommerce?` → debe responder con info del FAQ

Resultado esperado: respuestas coherentes, en español, basadas en el FAQ.

- [ ] **Step 13.2: Test de memoria** — *Manual (Pietro)*

1. `Me llamo Pietro y tengo un ecommerce de zapatillas`
2. (varios mensajes intermedios)
3. `¿Recuerdas mi sector?`

Esperado: el bot menciona "ecommerce" o "zapatillas".

- [ ] **Step 13.3: Test de escalación explícita** — *Manual (Pietro)*

`Quiero hablar directamente con Pietro`

Esperado:
- Pietro recibe notificación en su Telegram personal
- El bot responde con el mensaje de "Pietro te contacta en breve"

- [ ] **Step 13.4: Test de escalación implícita (intención de compra)** — *Manual (Pietro)*

`Estamos listos para invertir 5000€/mes en ads, ¿cómo empezamos?`

Esperado: el LLM debe decidir escalar (alto interés + presupuesto explícito).

Si no escala: ajustar el `Tool Description` de `escalar_a_humano` para hacer más explícito que la intención de compra es trigger de escalación.

- [ ] **Step 13.5: Test de mensaje no-texto** — *Manual (Pietro)*

Mandar una foto, un sticker, un audio.

Esperado: 3 respuestas con "Por ahora solo proceso texto...".

- [ ] **Step 13.6: Test de error handler** — *Manual (Pietro)*

1. Cambiar temporalmente el API key de OpenRouter a una inválida
2. Mandar un mensaje
3. Verificar que Pietro recibe en su Telegram personal una notificación de error con el `execution_id`
4. Restaurar el API key correcto

(El usuario no recibe respuesta — limitación documentada en Task 10.3.)

- [ ] **Step 13.7: Marcar MVP como listo** — *Claude Code*

```bash
git log --oneline
```

Verificar que están commiteados:
- Docs (spec, plan, README, CLAUDE.md)
- Knowledge base
- Workflows JSON
- Coolify deploy notes

---

## Post-MVP (extensiones futuras, NO incluir en este plan)

- Calendly / Google Calendar para agendar reuniones automáticamente
- CRM (Notion, Airtable, HubSpot) para guardar leads
- Multi-canal (WhatsApp Business, Instagram DMs)
- RAG con Qdrant si el knowledge base crece
- Analytics de conversaciones (cuántos escalan, qué preguntas se repiten)
- Voice notes con Whisper STT
- Fallback automático de modelo (Gemini → DeepSeek → mensaje técnico)
- Script que genera el system prompt automáticamente desde `narkan-faq.md`

---

## Seguridad — recordatorio final

- [ ] **Step final: Rotar el token de Coolify** — *Manual (Pietro)*

El token `2|6hDd3MBVocTSNmtg9MHDnI02YWTg2mIJcAr947rXa9d2ccbf` fue compartido en chat durante el setup. Una vez todo deployado:

1. Coolify → Settings → API Tokens → Revoke el token actual
2. Crear uno nuevo si lo sigues necesitando
3. Guardarlo en un gestor de contraseñas (no en chat)
