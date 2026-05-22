# Workflows de n8n

## Archivos

- `workflow-chatbot.json` — workflow principal (Telegram Trigger → AI Agent → Send Message). *Se genera cuando exportes el workflow desde n8n por primera vez.*
- `workflow-escalar.json` — sub-workflow llamado por la tool `escalar_a_humano`. *Idem.*
- `workflow-error.json` — error handler global. *Idem.*
- `system-prompt.md` — template del system prompt usado en el AI Agent.

## Importar en n8n (deploy en VPS nuevo)

1. n8n → **Workflows** → menú `...` → **Import from File**
2. Importar en este orden:
   1. `workflow-escalar.json`
   2. `workflow-error.json`
   3. `workflow-chatbot.json`
3. Conectar credenciales (todas se crean al importar):
   - `Narkan Bot` — Telegram Bot Token
   - `OpenRouter` — API key + Base URL `https://openrouter.ai/api/v1`
   - `Postgres` — auto-detecta el de Coolify si está en la misma red
4. En el workflow principal: **Settings** → **Error Workflow** = `Error — Chatbot Narkan`
5. Activar `workflow-escalar` y `workflow-chatbot`

## Editar el system prompt / knowledge base

1. Editar `../knowledge/narkan-faq.md` (fuente de verdad)
2. Abrir el AI Agent del workflow principal en n8n → pegar el contenido actualizado del FAQ en la sección `# CONOCIMIENTO DE NARKAN` del System Message
3. Save workflow → re-exportar a `workflow-chatbot.json`
4. Commitear

## Exportar después de cambios

1. n8n → workflow → `...` → **Download**
2. Reemplazar el JSON correspondiente en este directorio
3. Commit:
   ```bash
   git add n8n/*.json
   git commit -m "chore: update n8n workflow"
   ```
