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
2. Crear bot en `@BotFather` (ver Task 4 de `docs/superpowers/plans/2026-05-22-chatbot-telegram-n8n.md`)
3. Crear cuenta OpenRouter y obtener API key (Task 5)
4. `n8n/README.md` — importar y configurar los workflows
5. Testing manual (ver "Test plan" más abajo)

## Mantenimiento

- **Cambiar FAQs:** editar `knowledge/narkan-faq.md` → actualizar System Message del AI Agent en n8n → re-exportar workflow → commit
- **Cambiar de modelo:** AI Agent node → cambiar `Model` (probar primero con un mensaje)
- **Cambiar a quién escala:** sub-workflow `Tool — Escalar a Humano` → cambiar Chat ID

## Test plan

- [ ] El bot responde "¿Qué servicios ofrecéis?" usando el knowledge base
- [ ] El bot recuerda el nombre del usuario después de 5 mensajes
- [ ] Decir "quiero hablar con Pietro" → Pietro recibe notificación en su Telegram personal
- [ ] Mandar una foto al bot → responde "Por ahora solo proceso texto..."
- [ ] Si OpenRouter falla → Pietro recibe notificación de error con el `execution_id`

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
