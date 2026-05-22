# Deploy de n8n en Coolify

## Pre-requisitos
- VPS con Coolify ya instalado y accesible (en este caso: `http://187.77.246.43:8000`)
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
- **Telegram no envía mensajes:** los webhooks requieren HTTPS válido. Sin dominio → no funciona (a menos que uses un túnel tipo ngrok).
- **Postgres no conecta desde n8n:** ambos están en la misma red Docker. Usar el hostname interno que muestra Coolify, no la IP pública.
