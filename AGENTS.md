# AGENTS.md: Autonomous Engineering Governance & Safety Contract

## 1. Architectural Philosophy

> **"The AI controls the development loop, while deterministic CI/CD controls production safety."**

In this architecture, autonomous AI agents are treated as high-velocity software engineers, **not** production operators. The AI has full autonomy to investigate, reproduce, generate regression tests, and propose code fixes—but has **zero authority** to decide whether code is safe to deploy.

```
       ┌────────────────────────────────────────────────────────┐
       │              AUTONOMOUS DEVELOPMENT LOOP               │
       │                                                        │
       │  [Incident] ──► [Worktree] ──► [Agent] ──► [Pytest]   │
       │                                                        │
       └───────────────────────────┬────────────────────────────┘
                                   │ Deterministic Verification Gate
                                   ▼ (exit code 0 + regression test)
       ┌────────────────────────────────────────────────────────┐
       │               DETERMINISTIC CI/CD GATES                │
       │                                                        │
       │  [Git Push] ──► [GitHub Actions] ──► [Smoke Tests]     │
       │                                                        │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Security Boundaries & Isolation Policy

### 2.1 Git Worktree Isolation
The Codex Agent is **never** executed directly in the main working tree or production branch.
For every incident, the `Orchestrator` invokes:
```bash
git worktree add -b fix/incident-<id> .worktrees/fix-<id> HEAD
```
- **Blast Radius Containment:** Any syntax error, destructive command, or malformed code remains quarantined inside the isolated worktree directory.
- **Atomic Rollback:** If the agent fails, the orchestrator issues `git worktree remove --force` without leaving corrupted intermediate states.

### 2.2 File Modification Whitelist
The Deterministic Verification Gate enforces that the AI only touches whitelisted paths:
- ✅ `backend/app/**` (Application code)
- ✅ `backend/tests/**` (Unit and regression tests)
- ❌ `.github/**` (CI/CD workflows strictly immutable by AI)
- ❌ `docker-compose.yml`, `Dockerfile` (Infrastructure immutable by AI)
- ❌ Root configuration or credential files

---

## 3. The Mandatory Regression Test Standard

The agent is **strictly prohibited** from applying fixes without first providing a regression test:
1. **Reproduction Proof:** A test reproducing the exact failure scenario from the incident's request context must be generated in `backend/tests/test_checkout.py`.
2. **Deterministic Verification:** The orchestrator independently verifies that this new test passes along with 100% of all existing unit tests.

---

## 4. Incident Lifecycle States

Every incident transitions through a deterministic state machine:

| State | Responsible Actor | Meaning |
|---|---|---|
| `TRIGGERED` | Backend Application | Unhandled exception caught; structured payload emitted. |
| `INVESTIGATING` | Orchestrator | Webhook received; isolated worktree created. |
| `FIXING` | Codex Agent | Inspecting stack trace, writing regression test, applying patch. |
| `VERIFIED` | Deterministic Verification Gate | Pytest passed with exit code 0; regression test verified. |
| `RESOLVED` | CI/CD Pipeline | Code merged, deployed to v1.0.1, health & smoke checks passed. |
| `FAILED` | Orchestrator / CI | Verification gate failed; worktree pruned; engineer alerted. |

---

## 5. Structured Incident Schema

Incidents emitted by `backend/app/incident.py` adhere to this structured format:

```json
{
  "incident_id": "inc-a1b2c3d4",
  "timestamp": "2026-10-01T17:30:00Z",
  "service": "checkout-backend",
  "deployment_version": "v1.0.0",
  "environment": "production",
  "error_type": "KeyError",
  "error_message": "'FL'",
  "stack_trace": "Traceback (most recent call last):\n  File \"backend/app/tax.py\", line 36, in calculate_tax\n    tax_rate = US_STATE_TAX_RATES[state]\nKeyError: 'FL'",
  "endpoint": "/api/checkout",
  "request_payload": {
    "cart_items": [{"id": "item-101", "name": "Keyboard", "price": 120.0, "quantity": 1}],
    "shipping_address": {"street": "742 Evergreen", "city": "Orlando", "state": "FL", "postal_code": "32801", "country": "US"}
  },
  "status": "TRIGGERED"
}
```

---

## 6. The Production Safety Gate Contract

1. **AI Output Is Untrusted Input:** The orchestrator treats all agent-generated code as untrusted source code.
2. **Zero-Exception Policy:** The deterministic test runner (`pytest`) must exit with code `0`. Any warning or collection error fails the gate.
3. **Post-Deployment Smoke Test:** The deployment pipeline runs an active HTTP request against the new deployment (`/health` and live checkout smoke test) before marking the incident `RESOLVED`.
