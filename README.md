# Self-Healing Checkout System 🔄🛡️

An incident-driven autonomous development loop with deterministic production safety gates.

> **Core Philosophy:**
> **The AI controls the development loop, while deterministic CI/CD controls production safety.**

When a checkout failure occurs, the application captures the exception and emits a structured incident payload (stack trace, request context, deployment version). An orchestrator creates an isolated Git worktree and delegates the incident to a coding agent. The agent investigates the codebase, reproduces the failure, creates a regression test, implements the fix, and runs the test suite.

Crucially, **the agent is not trusted to decide whether the change is safe to deploy.** Once independent, deterministic verification gates pass (pytest exit code 0 and regression test checks), the change is committed, pushed, and handed off to CI/CD. The pipeline builds, deploys, executes health and smoke checks, and only then resolves the incident.

---

## Architecture Flow

```
                     ┌──────────────────────┐
                     │    Browser / User    │
                     └──────────┬───────────┘
                                │
                         Click "Buy Now"
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Checkout Frontend   │
                     └──────────┬───────────┘
                                │ POST /checkout
                                ▼
                     ┌──────────────────────┐
                     │   Python Backend    │
                     │                      │
                     │   ❌ Intentional Bug │
                     └──────────┬───────────┘
                                │
                           HTTP 500
                                │
                                ▼
                     ┌──────────────────────┐
                     │    Error Monitor     │
                     │ Sentry / Webhook     │
                     └──────────┬───────────┘
                                │
                         Incident event
                                │
                                ▼
                  ┌───────────────────────────┐
                  │     Agent Orchestrator    │
                  └────────────┬──────────────┘
                               │
                         Investigation
                               │
                               ▼
                  ┌───────────────────────────┐
                  │       Codex Agent         │
                  │                           │
                  │ Read logs                 │
                  │ Inspect repository       │
                  │ Reproduce bug             │
                  │ Write regression test     │
                  │ Fix code                  │
                  │ Run tests                 │
                  └────────────┬──────────────┘
                               │
                         Tests PASS
                               │
                               ▼
                     ┌───────────────────┐
                     │   Git commit      │
                     │   Git push        │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │   GitHub Actions  │
                     │                   │
                     │ test              │
                     │ build             │
                     │ deploy            │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │ New Deployment    │
                     │    v1.0.1         │
                     └─────────┬─────────┘
                               │
                         Health check
                               │
                         ┌─────┴─────┐
                         │           │
                       PASS         FAIL
                         │           │
                         ▼           ▼
                      SUCCESS     STOP/ROLLBACK
```

---

## Directory Structure

```
self-healing-checkout/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── Checkout.jsx
│   │   └── api.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── checkout.py
│   │   ├── tax.py
│   │   ├── models.py
│   │   └── incident.py
│   │
│   ├── tests/
│   │   └── test_checkout.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── agent/
│   ├── orchestrator.py
│   ├── codex_runner.py
│   └── incident_handler.py
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── docker-compose.yml
├── AGENTS.md
└── README.md
```

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- Git
- Node.js 18+ (for frontend)

### 2. Setup Python Backend & Agent
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run initial test suite
pytest backend/tests -v
```

### 3. Start Backend & Webhook Handler
```bash
# Terminal 1: Run Backend API (Port 8000)
python -m uvicorn app.main:app --app-dir backend --port 8000 --reload

# Terminal 2: Run Agent Incident Webhook Handler (Port 8001)
python agent/incident_handler.py --listen --port 8001
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Access http://localhost:5173
```

---

## Testing the Autonomous Healing Loop

1. Open the UI at `http://localhost:5173`.
2. Click **"❌ Trigger 500 Bug"** (selecting state `FL`).
3. Click **"⚡ Buy Now"**.
4. The backend raises `KeyError: 'FL'` in `backend/app/tax.py`, catches it, formats a structured incident payload, and dispatches it to the Agent Orchestrator.
5. The **Orchestrator**:
   - Provisions an isolated Git worktree: `fix/incident-<id>`.
   - Dispatches `CodexRunner`.
   - The agent creates a regression test in `test_checkout.py`.
   - The agent patches `tax.py` with fallback tax calculations.
   - The Orchestrator independently verifies `pytest backend/tests`.
   - Commits and merges to `main`.
   - Simulates CI/CD promotion to version `v1.0.1` and marks incident **RESOLVED**.
6. Retry the checkout for Florida (`FL`)—it now succeeds with 200 OK!

---

## Running via Docker Compose

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Agent Webhook: `http://localhost:8001`
- Healthcheck: `http://localhost:8000/health`
