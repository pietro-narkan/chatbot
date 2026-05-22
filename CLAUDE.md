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

- "Cambia las FAQs" → editar `knowledge/narkan-faq.md`, recordar a Pietro actualizar el System Message en n8n y re-exportar el JSON.
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
