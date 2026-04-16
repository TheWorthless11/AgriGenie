# AgriGenie Zero-Cost Deployment (Windows)

This setup runs **all features** locally and exposes your app publicly over HTTPS using a **Cloudflare Quick Tunnel**.

## What This Uses

- Docker Compose services already in this repo:
  - PostgreSQL
  - Redis
  - Django (Daphne/ASGI)
  - Celery Worker
  - Celery Beat
- Cloudflared quick tunnel for public URL (`*.trycloudflare.com`)

## Requirements

1. Docker Desktop installed and running
2. Cloudflared installed
3. Stable internet connection
4. Computer stays on while app is public

## One-Time Setup

1. Install Cloudflared (no payment required):

```powershell
winget install --id Cloudflare.cloudflared -e
```

2. Ensure Docker Desktop is running.

3. Confirm your local environment file exists:
- `.env` (already present in this repo)

## Start Everything

From repository root:

```powershell
.\start_zero_cost.bat
```

## Stable URL Mode (Recommended For Google Login)

Quick tunnels change URL on restart, which causes Google OAuth `redirect_uri_mismatch`.
Use a named tunnel with a stable hostname under your Cloudflare-managed domain.
The hostname must be a full domain name like `app.yourdomain.com`.

1. Configure named tunnel (one-time):

```powershell
.\setup_named_tunnel.bat app.yourdomain.com
```

2. Register this exact callback in Google Cloud Console:

```text
https://app.yourdomain.com/accounts/google/login/callback/
```

3. Restart stack:

```powershell
.\stop_zero_cost.bat
.\start_zero_cost.bat
```

If DNS already exists and you want to replace it, re-run setup with `-OverwriteDns`.

What it does:
1. Starts Docker services (`db`, `redis`, `web`, `celery_worker`, `celery_beat`)
  - Builds the local app image on startup so your current code is always used.
2. Starts Cloudflare tunnel in background
3. Prints:
- Local URL (`http://localhost:8000`)
- Public URL (`https://<random>.trycloudflare.com`)

## Stop Everything

```powershell
.\stop_zero_cost.bat
```

Optional full cleanup (also removes Docker volumes):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop_zero_cost.ps1 -RemoveVolumes
```

## Logs and Runtime Files

Runtime files are stored in `.runtime/`:
- `cloudflared.log` - tunnel logs
- `cloudflared.pid` - tunnel process id
- `public_url.txt` - latest detected public URL
- `google_redirect_uri.txt` - exact Google OAuth callback URI for current public URL

## Verification Checklist

1. Web app loads locally: `http://localhost:8000`
2. Admin works: `<public_url>/admin`
3. Celery worker running:

```powershell
docker compose logs celery_worker --tail 100
```

4. Celery beat running:

```powershell
docker compose logs celery_beat --tail 100
```

5. Redis healthy:

```powershell
docker compose exec redis redis-cli ping
```

6. PostgreSQL healthy:

```powershell
docker compose exec db pg_isready -U postgres -d agrigenie_db
```

## Notes

- Quick tunnel URL changes when restarted.
- For a fixed custom domain, switch to a named Cloudflare tunnel later.
- Keep Docker Desktop and your internet running to keep the app online.
