# Stack n8n para Chatbot NeoKodex

Stack de Docker Compose para n8n + Postgres, deployado **fuera** del UI de Coolify pero **enchufado** a la red Docker `coolify` para reusar el Traefik existente con Let's Encrypt automático.

## Ubicación en el VPS

`/opt/chatbot-neokodex/` (en 187.77.246.43)

## Estructura

```
n8n-stack/
├── docker-compose.yml   # Stack n8n + Postgres
├── .env.example         # Plantilla de variables
└── README.md            # Este archivo
```

El `.env` real (con secretos) **NO** se versiona. Vive solo en el VPS.

## Cómo se deployó (referencia)

1. **Generar secretos:**
   ```bash
   openssl rand -base64 32 | tr -d '/=+' | cut -c1-30   # POSTGRES_PASSWORD
   openssl rand -base64 48 | tr -d '/=+' | cut -c1-40   # N8N_ENCRYPTION_KEY
   ```

2. **Copiar archivos al VPS:**
   ```bash
   ssh -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43 'mkdir -p /opt/chatbot-neokodex'
   scp -i ~/.ssh/claude-code-nk-deploy-session docker-compose.yml root@187.77.246.43:/opt/chatbot-neokodex/
   # crear .env con los secretos directamente en el VPS
   ```

3. **Arrancar el stack:**
   ```bash
   ssh -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43 'cd /opt/chatbot-neokodex && docker compose up -d'
   ```

4. **Verificar:**
   ```bash
   curl -I https://n8n-187-77-246-43.sslip.io
   # Debe responder 200 o 401 (auth requerida)
   ```

## Por qué sslip.io

`n8n-187-77-246-43.sslip.io` es un DNS público gratuito que resuelve automáticamente al IP `187.77.246.43`. Permite tener HTTPS válido (Let's Encrypt) sin necesidad de comprar dominio. Apto para pruebas; en producción usa un dominio real.

## Por qué fuera del UI de Coolify

- Coolify gestiona sus servicios con un sistema propio (UUIDs, environments, etc.)
- Para evitar conflictos y mantener el chatbot como un stack independiente y portable, lo gestionamos directo con docker compose
- Reutilizamos solo la red `coolify` para enchufarnos al Traefik existente (HTTPS, routing por dominio)
- Ventaja: este stack se puede migrar a otro VPS con solo `git clone` + secretos + `docker compose up -d`

## Operaciones comunes

**Ver logs:**
```bash
ssh -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43 'cd /opt/chatbot-neokodex && docker compose logs -f n8n'
```

**Reiniciar n8n:**
```bash
ssh -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43 'cd /opt/chatbot-neokodex && docker compose restart n8n'
```

**Actualizar n8n a última versión:**
```bash
ssh -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43 'cd /opt/chatbot-neokodex && docker compose pull n8n && docker compose up -d n8n'
```

**Backup del Postgres:**
```bash
ssh -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43 'docker exec chatbot-n8n-postgres pg_dump -U n8n n8n | gzip > /tmp/n8n-backup-$(date +%Y%m%d).sql.gz'
scp -i ~/.ssh/claude-code-nk-deploy-session root@187.77.246.43:/tmp/n8n-backup-*.sql.gz ./backups/
```

**Backup del estado de n8n (workflows, credenciales):**
Las credenciales viven en Postgres. Backup del Postgres = backup completo. El volumen `n8n-data` solo guarda configuración temporal.
