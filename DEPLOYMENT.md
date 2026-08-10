# Deployment Evidence — Checkpoint 5

## Student

| Item | Value |
| --- | --- |
| Name | Nguyễn Văn Ninh |
| Mã học viên | 2A202601419 |
| Repository | https://github.com/ninhhh1011/DAY12-2A202601419-NguyenVanNinh |

## Deployment

| Item | Value |
| --- | --- |
| Service URL | http://127.0.0.1:8000 |
| Platform | Docker Compose local fallback; Railway was attempted first |
| Deployment date | 2026-08-10 |
| Redis source | Docker Compose `redis:7-alpine`, persistent `redis-data` volume |

Railway CLI 5.35.0 was installed. `railway whoami` returned exactly: `Unauthorized. Please login with railway login`. This required an interactive Railway account login, so no Railway project or deployment was created. `LOCAL_FALLBACK=true` is set only in ignored local `.env`.

## Environment variables

| Variable | Source |
| --- | --- |
| `PORT` | Docker container command / local port mapping |
| `AGENT_API_KEY` | ignored local `.env`; local value verified absent from tracked HEAD/history on 2026-08-10 |
| `REDIS_URL` | Compose service URL `redis://redis:6379/0` |
| `RATE_LIMIT_PER_MINUTE` | Compose value `10` |
| `MONTHLY_BUDGET_USD` | Compose value `10.0` |
| `LOG_LEVEL` | Compose value `INFO` |

## Sanitized verification

```text
gh repo rename DAY12-2A202601419-NguyenVanNinh --repo ninhhh1011/K3-Day12-2A202601419-NguyenVanNinh --yes
origin  https://github.com/ninhhh1011/DAY12-2A202601419-NguyenVanNinh (fetch)
origin  https://github.com/ninhhh1011/DAY12-2A202601419-NguyenVanNinh (push)

railway --version
railway 5.35.0
railway whoami
Unauthorized. Please login with `railway login`

docker compose up -d --build
docker compose ps
agent  Up (healthy)  0.0.0.0:8000->8000/tcp
redis  Up (healthy)  0.0.0.0:6379->6379/tcp

GET http://127.0.0.1:8000/health -> 200
{"status":"ok","service":"day12-agent","version":"1.0.0"}
GET http://127.0.0.1:8000/ready -> 200
{"status":"ready","redis":true}
POST http://127.0.0.1:8000/ask without X-API-Key -> 401
```

## CP5 test result

`pytest tests/test_cp5.py -v` completed with **8 passed, 5 skipped**. The four public HTTPS-path checks are expected skips in `LOCAL_FALLBACK=true` mode, and the real-key public `/ask` check is skipped because no `DEPLOY_API_KEY` is set. The local Docker fallback is therefore capped at **9/15** for CP5.

## Screenshots

- `screenshots/dashboard.png` shows the real Docker Compose `agent` and `redis` containers healthy.
- `screenshots/health.png` shows the actual local `/health` HTTP 200 response.
