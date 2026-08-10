# Day 12 Lab Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete and verify the Day 12 Cloud & Deployment lab against its supplied tests, then deploy to Railway when authenticated platform access is available.

**Architecture:** Preserve the starter FastAPI dependency-injection structure. Add only the missing implementations in the supplied modules, use Redis for shared limits/cost/history, package the app with the supplied Docker/Compose layout, and verify one checkpoint completely before advancing.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic Settings, Redis/fakeredis, pytest, Docker, Docker Compose, Railway, GitHub Actions.

---

## File map

- `app/config.py`: environment-backed settings.
- `app/logging_utils.py`: one-line JSON logging.
- `app/main.py`: `/health`, `/ready`, and `/ask` orchestration.
- `app/auth.py`: API-key verification and user identity.
- `app/rate_limiter.py`: Redis sorted-set sliding window.
- `app/cost_guard.py`: monthly Redis cost counter.
- `app/store.py`: Redis conversation history.
- `app/lifecycle.py`: SIGTERM/SIGINT shutdown state.
- `Dockerfile`, `.dockerignore`, `docker-compose.yml`: image and local stack.
- `DEPLOYMENT.md`, `screenshots/`: deployment evidence.
- `exercises.md`: observations from the completed implementation.
- `.github/workflows/ci.yml`, `README.md`: optional CI/CD bonus.

### Task 1: Isolated workspace and baseline

**Files:**
- Preserve: `LAB_REVIEW.md`
- Create locally, never track: `.env`, `.venv/`
- Test: `tests/test_cp1.py`, `tests/test_cp2.py`, `tests/test_cp3.py`, `tests/test_cp4.py`

- [ ] **Step 1: Detect or create an isolated worktree**

Use `superpowers:using-git-worktrees`. Do not add the existing untracked `LAB_REVIEW.md` to an implementation commit.

- [ ] **Step 2: Create the Python environment**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

If `py -3.11` is unavailable, use the installed Python version after confirming `pip install -r requirements.txt` succeeds.

- [ ] **Step 3: Create local configuration without exposing the key**

```powershell
Copy-Item .env.example .env
$key = .venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(32))"
(Get-Content .env) -replace '^AGENT_API_KEY=.*$', "AGENT_API_KEY=$key" | Set-Content -Encoding UTF8 .env
```

Do not print `$key` or the resulting `.env` contents.

- [ ] **Step 4: Verify baseline RED**

```powershell
.venv\Scripts\python -m pytest tests/test_cp1.py -v
.venv\Scripts\python -m pytest tests/test_cp3.py -v
.venv\Scripts\python -m pytest tests/test_cp4.py -v
```

Expected: failures caused by missing fields and `NotImplementedError`, not import errors.

### Task 2: CP1 — Settings, logging, and liveness

**Files:**
- Modify: `app/config.py:43-45`
- Modify: `app/logging_utils.py:20-37`
- Modify: `app/main.py:76-90`
- Test: `tests/test_cp1.py`

- [ ] **Step 1: Run CP1 to confirm RED**

```powershell
.venv\Scripts\python -m pytest tests/test_cp1.py -v
```

Expected: settings fields are missing and logging/health reach `NotImplementedError`.

- [ ] **Step 2: Add the six existing `Settings` fields**

Add inside `Settings`, preserving the existing `SettingsConfigDict`:

```python
    port: int = 8000
    agent_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0
    log_level: str = "INFO"
```

- [ ] **Step 3: Verify settings tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp1.py::TestConfig -v
```

Expected: 5 passed.

- [ ] **Step 4: Implement one-line JSON logging**

Replace the `NotImplementedError` in `log_event` with:

```python
    payload = {
        "event": event,
        "level": level.lower(),
        "timestamp": utc_now_iso(),
        **fields,
    }
    line = json.dumps(payload, ensure_ascii=False)
    print(line, file=sys.stdout)
    return line
```

- [ ] **Step 5: Verify logging tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp1.py::TestStructuredLogging -v
```

Expected: 5 passed.

- [ ] **Step 6: Implement `/health` on the existing FastAPI app**

Replace the `NotImplementedError` in `health` with:

```python
    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }
```

- [ ] **Step 7: Verify all CP1 tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp1.py -v
```

Expected: 13 passed, 0 failed.

- [ ] **Step 8: Commit CP1**

```powershell
git add app/config.py app/logging_utils.py app/main.py
git commit -m "feat: complete CP1 config health and logging"
```

### Task 3: CP2 — Docker image and Compose

**Files:**
- Modify: `Dockerfile`
- Modify: `.dockerignore`
- Modify: `docker-compose.yml`
- Test: `tests/test_cp2.py`

- [ ] **Step 1: Run structural CP2 tests to confirm RED**

```powershell
.venv\Scripts\python -m pytest tests/test_cp2.py -v -m "not docker"
```

Expected: failures for multi-stage, slim runtime, non-root user, healthcheck, ignore entries, and missing agent service.

- [ ] **Step 2: Replace `Dockerfile` with the minimal tested image**

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
COPY utils ./utils

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

- [ ] **Step 3: Replace `.dockerignore` with required exclusions**

```text
.env
.git
.gitignore
.venv
__pycache__
*.py[cod]
.pytest_cache
```

- [ ] **Step 4: Add the agent service while preserving the supplied Redis service**

Add under `services`:

```yaml
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      AGENT_API_KEY: ${AGENT_API_KEY}
      REDIS_URL: redis://redis:6379/0
      RATE_LIMIT_PER_MINUTE: 10
      MONTHLY_BUDGET_USD: 10.0
      LOG_LEVEL: INFO
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"]
      interval: 30s
      timeout: 5s
      retries: 3
```

- [ ] **Step 5: Verify structural CP2 tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp2.py -v -m "not docker"
```

Expected: all non-Docker tests passed.

- [ ] **Step 6: Build and verify the real image**

```powershell
docker build -t day12-agent:prod .
docker images day12-agent:prod --format "{{.Size}}"
.venv\Scripts\python -m pytest tests/test_cp2.py -v
```

Expected: build succeeds, reported size is below 500MB, all CP2 tests pass.

- [ ] **Step 7: Commit CP2**

```powershell
git add Dockerfile .dockerignore docker-compose.yml
git commit -m "feat: complete CP2 container stack"
```

### Task 4: CP3 — Authentication, rate limiting, cost guard, and ask flow

**Files:**
- Modify: `app/auth.py:18-37`
- Modify: `app/rate_limiter.py:30-59`
- Modify: `app/cost_guard.py:32-63`
- Modify: `app/main.py:111-148`
- Test: `tests/test_cp3.py`

- [ ] **Step 1: Run CP3 to confirm RED**

```powershell
.venv\Scripts\python -m pytest tests/test_cp3.py -v
```

Expected: failures caused by the four unimplemented code paths.

- [ ] **Step 2: Implement API-key verification using the existing signature**

Replace the `NotImplementedError` in `verify_api_key` with:

```python
    expected = get_settings().agent_api_key
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
    return x_user_id or ANONYMOUS_USER
```

- [ ] **Step 3: Verify authentication tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp3.py::TestAuthentication -v
```

Expected: 6 passed.

- [ ] **Step 4: Implement `RateLimiter.hit_count`**

```python
        now = now if now is not None else time.time()
        key = self._key(user_id)
        self.client.zremrangebyscore(key, 0, now - WINDOW_SECONDS)
        return int(self.client.zcard(key))
```

- [ ] **Step 5: Implement `RateLimiter.check`**

```python
        now = now if now is not None else time.time()
        if self.hit_count(user_id, now) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )
        key = self._key(user_id)
        self.client.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})
        self.client.expire(key, WINDOW_SECONDS)
```

- [ ] **Step 6: Verify direct rate-limit behaviors**

```powershell
.venv\Scripts\python -m pytest tests/test_cp3.py::TestRateLimiter -v
```

Expected while `/ask` remains unimplemented: direct limiter tests pass; HTTP limiter tests still fail through `/ask`.

- [ ] **Step 7: Implement `CostGuard.spent`, `check`, and `record`**

```python
    def spent(self, user_id: str, month: str | None = None) -> float:
        value = self.client.get(self._key(user_id, month))
        return float(value) if value is not None else 0.0

    def check(
        self,
        user_id: str,
        estimated_cost: float = 0.0,
        month: str | None = None,
    ) -> None:
        if self.spent(user_id, month) + estimated_cost > self.budget:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="monthly budget exceeded",
            )

    def record(self, user_id: str, cost: float, month: str | None = None) -> float:
        key = self._key(user_id, month)
        total = self.client.incrbyfloat(key, cost)
        self.client.expire(key, KEY_TTL_SECONDS)
        return float(total)
```

- [ ] **Step 8: Verify direct cost-guard behaviors**

```powershell
.venv\Scripts\python -m pytest tests/test_cp3.py::TestCostGuard -v
```

Expected while `/ask` remains unimplemented: direct guard tests pass; HTTP/record-through-ask tests still fail.

- [ ] **Step 9: Implement `/ask` in the supplied dependency-injected endpoint**

Replace the `NotImplementedError` in `ask` with:

```python
    limiter.check(user_id)
    guard.check(user_id)
    history = store.get_history(user_id)
    result = ask_llm(payload.question, history)
    store.append(user_id, "user", payload.question)
    store.append(user_id, "assistant", result["answer"])
    guard.record(user_id, result["cost_usd"])
    log_event(
        "ask_completed",
        user_id=user_id,
        tokens_in=result["tokens_in"],
        tokens_out=result["tokens_out"],
        cost_usd=result["cost_usd"],
    )
    return {
        "answer": result["answer"],
        "user_id": user_id,
        "history_length": len(history),
        "cost_usd": result["cost_usd"],
        "tokens": {
            "in": result["tokens_in"],
            "out": result["tokens_out"],
        },
    }
```

- [ ] **Step 10: Verify all CP3 tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp3.py -v
```

Expected: 22 passed, 0 failed.

- [ ] **Step 11: Commit CP3**

```powershell
git add app/auth.py app/rate_limiter.py app/cost_guard.py app/main.py
git commit -m "feat: complete CP3 API security"
```

### Task 5: CP4 — Shared history, readiness, and graceful shutdown

**Files:**
- Modify: `app/store.py:47-76`
- Modify: `app/lifecycle.py:25-59`
- Modify: `app/main.py:76-105`
- Test: `tests/test_cp4.py`

- [ ] **Step 1: Run CP4 to confirm RED**

```powershell
.venv\Scripts\python -m pytest tests/test_cp4.py -v
```

Expected: failures from unimplemented store, readiness, and lifecycle methods.

- [ ] **Step 2: Implement Redis store methods**

```python
    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def append(self, user_id: str, role: str, content: str) -> None:
        key = self._key(user_id)
        value = json.dumps(
            {"role": role, "content": content},
            ensure_ascii=False,
        )
        self.client.rpush(key, value)
        self.client.ltrim(key, -HISTORY_MAX_MESSAGES, -1)
        self.client.expire(key, HISTORY_TTL_SECONDS)

    def get_history(self, user_id: str) -> list[dict]:
        return [
            json.loads(value)
            for value in self.client.lrange(self._key(user_id), 0, -1)
        ]
```

- [ ] **Step 3: Verify store and stateless tests as far as `/ask` permits**

```powershell
.venv\Scripts\python -m pytest tests/test_cp4.py::TestConversationStore tests/test_cp4.py::TestStateless -v
```

Expected: store tests pass; history reuse passes because CP3 `/ask` now calls the store.

- [ ] **Step 4: Implement `/ready` using its existing dependency**

```python
    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )
    if not store.ping():
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "redis": False},
        )
    return {"status": "ready", "redis": True}
```

- [ ] **Step 5: Verify readiness tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp4.py::TestReadiness -v
```

Expected: 3 passed.

- [ ] **Step 6: Implement lifecycle handler and installation**

Replace both `NotImplementedError` statements with:

```python
    def request_shutdown(self, signum=None, frame=None) -> None:
        self.shutting_down = True
        previous = self._previous.get(signum)
        if callable(previous):
            previous(signum, frame)

    def install(self) -> None:
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._previous[sig] = signal.getsignal(sig)
            signal.signal(sig, self.request_shutdown)
```

- [ ] **Step 7: Verify all CP4 tests GREEN**

```powershell
.venv\Scripts\python -m pytest tests/test_cp4.py -v
```

Expected: 19 passed, 0 failed.

- [ ] **Step 8: Commit CP4**

```powershell
git add app/store.py app/lifecycle.py app/main.py
git commit -m "feat: complete CP4 scaling and reliability"
```

### Task 6: Local regression and stack verification

**Files:**
- Test: `tests/test_cp1.py`, `tests/test_cp2.py`, `tests/test_cp3.py`, `tests/test_cp4.py`

- [ ] **Step 1: Run every local checkpoint**

```powershell
.venv\Scripts\python -m pytest tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py -v
```

Expected: all tests pass, including Docker tests when the daemon is available.

- [ ] **Step 2: Start the Compose stack**

```powershell
docker compose up -d --build
docker compose ps
```

Expected: Redis and agent are running/healthy.

- [ ] **Step 3: Verify endpoints without exposing the API key**

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
try { Invoke-WebRequest -Method Post -Uri http://localhost:8000/ask -ContentType 'application/json' -Body '{"question":"Hello"}' } catch { $_.Exception.Response.StatusCode.value__ }
```

Expected: health `ok`, ready `ready`, unauthenticated ask `401`.

### Task 7: CP5 — Railway deployment or documented fallback

**Files:**
- Modify: `DEPLOYMENT.md`
- Create: `screenshots/dashboard.png`
- Create: `screenshots/health.png`
- Test: `tests/test_cp5.py`

- [ ] **Step 1: Rename the GitHub repository to the required submission name**

Before deployment, rename the GitHub repository to the required submission name and update the remote:

```powershell
gh repo rename DAY12-2A202601419-NguyenVanNinh --repo ninhhh1011/K3-Day12-2A202601419-NguyenVanNinh --yes
git remote set-url origin https://github.com/ninhhh1011/DAY12-2A202601419-NguyenVanNinh
git remote -v
```

Expected: fetch and push URLs use `DAY12-2A202601419-NguyenVanNinh`. If `gh` is unavailable, perform the same rename through the authenticated GitHub connector or browser before continuing.

- [ ] **Step 2: Install and inspect Railway CLI state**

```powershell
npm install -g @railway/cli
railway --version
railway whoami
```

Expected: CLI installed. If `whoami` reports no authenticated user, run `railway login` using the supported browser flow.

- [ ] **Step 3: Create/link project, add Redis, and set non-secret values**

```powershell
railway init
railway add --database redis
railway variables --set RATE_LIMIT_PER_MINUTE=10 --set MONTHLY_BUDGET_USD=10.0 --set LOG_LEVEL=INFO
```

Set `AGENT_API_KEY` from the local `.env` through the CLI or dashboard without echoing it in logs.

- [ ] **Step 4: Deploy and obtain the public domain**

```powershell
railway up
railway domain
railway logs
```

Expected: build succeeds and a public HTTPS domain is returned.

- [ ] **Step 5: Verify the public service**

```powershell
$publicUrl = (railway domain).TrimEnd('/')
Invoke-RestMethod "$publicUrl/health"
Invoke-RestMethod "$publicUrl/ready"
try { Invoke-WebRequest -Method Post -Uri "$publicUrl/ask" -ContentType 'application/json' -Body '{"question":"Hello"}' } catch { $_.Exception.Response.StatusCode.value__ }
```

Expected: health `ok`, ready `ready`, unauthenticated ask `401`.

- [ ] **Step 6: Complete deployment evidence**

Fill `DEPLOYMENT.md` with student name Nguyễn Văn Ninh, student ID `2A202601419`, repository URL, returned public URL, Railway, deployment date, Redis source, and actual sanitized command outputs. Capture the Railway dashboard as `screenshots/dashboard.png` and a successful `/health` result as `screenshots/health.png`.

- [ ] **Step 7: Verify CP5 public path**

```powershell
.venv\Scripts\python -m pytest tests/test_cp5.py -v
```

Expected: all non-optional public tests pass; the authenticated ask test may skip until `DEPLOY_API_KEY` is set locally.

- [ ] **Step 8: Use fallback only if Railway is blocked**

If Railway login, account eligibility, or project creation cannot succeed, set `LOCAL_FALLBACK=true` in `.env`, keep the Compose stack running, record the real blocker in `DEPLOYMENT.md`, capture both screenshots, and run:

```powershell
.venv\Scripts\python -m pytest tests/test_cp5.py -v
```

Expected: fallback tests pass; `grade.py` caps CP5 at 9/15.

- [ ] **Step 9: Commit CP5 evidence**

```powershell
git add DEPLOYMENT.md screenshots/dashboard.png screenshots/health.png
git commit -m "docs: add CP5 deployment evidence"
```

### Task 8: Exercises from actual observations

**Files:**
- Modify: `exercises.md`

- [ ] **Step 1: Gather objective evidence**

Record one real JSON log line, single-stage and multi-stage image sizes, Docker cache output after a one-character source change, scaled-stack history lengths, and one real deployment error from Task 7.

- [ ] **Step 2: Answer all ten prompts in Vietnamese**

Each answer must address every clause in its question and use the recorded evidence. Do not copy generic answers or invent a deployment failure.

- [ ] **Step 3: Verify no answer placeholders remain**

```powershell
rg -n "Câu trả lời của bạn" exercises.md
```

Expected: no matches.

- [ ] **Step 4: Commit exercises**

```powershell
git add exercises.md
git commit -m "docs: complete Day 12 reflections"
```

### Task 9: Bonus GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md:1`
- Test: `tests/test_bonus_cicd.py`

- [ ] **Step 1: Run the bonus test to confirm RED**

```powershell
.venv\Scripts\python -m pytest tests/test_bonus_cicd.py -v
```

Expected: failure because `.github/workflows/` has no workflow.

- [ ] **Step 2: Create the workflow**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --ignore=tests/test_cp5.py --ignore=tests/test_bonus_cicd.py -m "not docker"
        env:
          AGENT_API_KEY: ci-dummy
          REDIS_URL: fake://

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t day12-agent:test .

  deploy:
    runs-on: ubuntu-latest
    needs: [test, build]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g @railway/cli
      - run: railway up --service "${{ vars.RAILWAY_SERVICE }}" --detach
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      - name: Smoke test
        run: |
          sleep 45
          curl -fsS "${{ vars.PUBLIC_URL }}/health"
```

- [ ] **Step 3: Add the real badge URL to `README.md`**

Add as the first line:

```markdown
![CI](https://github.com/ninhhh1011/DAY12-2A202601419-NguyenVanNinh/actions/workflows/ci.yml/badge.svg)
```

- [ ] **Step 4: Verify local bonus structure**

```powershell
.venv\Scripts\python -m pytest tests/test_bonus_cicd.py -v
```

Expected before push: all structural tests pass; `test_badge_bao_passing` can fail until GitHub has run the workflow.

- [ ] **Step 5: Commit bonus files**

```powershell
git add .github/workflows/ci.yml README.md
git commit -m "ci: add tested build and deployment workflow"
```

- [ ] **Step 6: Configure external Actions state and push**

Configure `RAILWAY_TOKEN` as a GitHub Actions secret and `PUBLIC_URL` plus `RAILWAY_SERVICE` as repository variables, then push. Never store their values in tracked files.

- [ ] **Step 7: Verify badge passing**

After the GitHub workflow completes:

```powershell
.venv\Scripts\python -m pytest tests/test_bonus_cicd.py -v
```

Expected: 13 passed, 0 failed.

### Task 10: Final verification and publication

**Files:**
- Verify all tracked changes and local secret exclusions.

- [ ] **Step 1: Run the complete test suite**

```powershell
.venv\Scripts\python -m pytest tests/ -v
```

Expected: all locally applicable tests pass; any skips are explained by their explicit pytest reason.

- [ ] **Step 2: Run the grader**

```powershell
.venv\Scripts\python grade.py
```

Expected: score reported from fresh test results; Railway path targets 100/100 after exercises, with bonus compensating only up to the 100-point cap.

- [ ] **Step 3: Verify security and completeness**

```powershell
git ls-files .env
rg -n "NotImplementedError" app
git diff --check
git status --short
```

Expected: `.env` is not listed, no `NotImplementedError` remains in `app`, no whitespace errors, and only intended user files remain untracked.

- [ ] **Step 4: Review commit history**

```powershell
git log --oneline --decorate -12
```

Expected: separate design, plan, CP1, CP2, CP3, CP4, deployment, exercises, and bonus commits where those phases were completed.

- [ ] **Step 5: Push the verified branch**

```powershell
git push origin HEAD:main
```

Expected: push succeeds. If the GitHub repository is renamed to the required `DAY12-2A202601419-NguyenVanNinh`, update `origin` and badge URL first.
