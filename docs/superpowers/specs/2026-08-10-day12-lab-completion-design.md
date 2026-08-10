# Day 12 Lab Completion Design

## Goal

Complete the existing Cloud & Deployment lab against the repository's tests, verify each checkpoint before moving forward, attempt a real Railway deployment, and use the documented local fallback only when Railway cannot be completed from the available environment.

## Source of truth

Priority is:

1. `tests/test_cp*.py` and `tests/test_bonus_cicd.py` for exact observable behavior.
2. Existing source signatures, dependency injection, constants, and file structure.
3. `README.md`, `LAB_GUIDE.md`, and file docstrings for constraints not encoded by tests.
4. Attached prompt snippets only as hints; conflicting snippets are discarded.

This avoids known prompt conflicts such as nonexistent `lifecycle.router`, incompatible constructor signatures, missing `X-User-Id`, different Redis key formats, and bypassing FastAPI dependency overrides used by the tests.

## Considered approaches

### 1. Incremental test-authoritative completion — selected

Run each checkpoint to establish RED, implement the smallest code matching the existing API, and rerun the checkpoint to GREEN before continuing. This preserves the starter architecture and gives the clearest evidence for every score block.

### 2. Copy the attached code samples

Rejected because several samples do not match the repository's functions, decorators, constructors, or tests and would introduce new failures.

### 3. Rewrite the service from scratch

Rejected because it would replace working starter code, bypass supplied dependency injection, enlarge the diff, and make checkpoint isolation harder.

## Architecture

- `app/config.py`: Pydantic settings read environment variables; the API key remains required.
- `app/logging_utils.py`: one-line UTF-8 JSON events on stdout.
- `app/main.py`: retain the supplied FastAPI app, providers, dependency overrides, request model, and endpoint signatures.
- `app/auth.py`: constant-time API-key validation and user identity extraction.
- `app/rate_limiter.py`: Redis sorted-set sliding window using the supplied `now` seam for deterministic tests.
- `app/cost_guard.py`: per-user, per-UTC-month Redis counters using the existing constructor and optional month seam.
- `app/store.py`: shared Redis conversation history with size and TTL limits.
- `app/lifecycle.py`: install SIGTERM/SIGINT handlers while preserving and invoking prior handlers.
- Docker files: minimal multi-stage, slim, non-root image plus Compose agent/Redis services.
- Deployment: Railway first; local Compose fallback only if authentication or platform state prevents deployment.
- CI bonus: one GitHub Actions workflow for test, image build, guarded deployment, smoke test, and badge.

No new application abstractions or dependencies are introduced.

## Execution order

1. Prepare `.venv`/`.env`; confirm baseline failures.
2. CP1: config, logging, health; require all CP1 tests passing.
3. CP2: Dockerfile, ignore rules, Compose; require structural tests, then real build when Docker is available.
4. CP3: auth, rate limiter, cost guard, ask flow; require all CP3 tests passing.
5. CP4: Redis store, readiness, lifecycle; require all CP4 tests passing.
6. Run all local non-deployment tests to catch regressions.
7. Attempt Railway deployment and complete `DEPLOYMENT.md`/screenshots; if impossible, activate fallback and record the real reason.
8. Complete exercises only with observations produced during the run.
9. Add and verify bonus workflow where external GitHub/Railway state permits.
10. Run the complete suite and `grade.py`; scan secrets, `.env` tracking, and remaining `NotImplementedError`.

## Error handling and security

- Authentication fails with 401 before consuming rate quota or cost budget.
- Rate-limit failures include 429 and `Retry-After`.
- Budget failures return 402 before the mock LLM call.
- Readiness converts Redis failures to 503 rather than leaking exceptions.
- Liveness never depends on Redis.
- Signal handlers do minimal work and delegate to the previous server handler.
- Secrets stay only in local `.env`, Railway variables, or GitHub Secrets.
- No real key or token is written to tracked files, command output, deployment documentation, or screenshots.

## Verification

Every code phase follows RED → minimal implementation → GREEN using the supplied checkpoint test. Configuration-only changes use their existing structural tests. Completion requires:

- CP1, CP3, and CP4 fully passing.
- CP2 structural tests passing and Docker tests passing when the daemon is available.
- CP5 public tests passing after Railway deployment, or documented fallback tests passing with the 9/15 cap.
- No regression in the full local suite.
- `grade.py` output captured and reported accurately.
- `git status` proves `.env` is untracked/ignored and existing user files are preserved.

## External-state limits

Railway login, account eligibility, project creation, DNS issuance, GitHub repository rename, Actions secrets, and screenshots depend on authenticated external state. The implementation will exhaust available CLI/browser paths without exposing credentials. If any external prerequisite cannot be completed, the exact blocker is reported and the documented fallback is used where applicable.
