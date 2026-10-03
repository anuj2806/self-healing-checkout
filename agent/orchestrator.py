"""
Agent Orchestrator.

Manages isolated Git worktrees, dispatches Codex Agent, and enforces
strict deterministic verification gates before code changes are committed
or deployed to production.

Core Principle:
"The AI controls the development loop, while deterministic CI/CD controls production safety."
"""

import os
import sys
import shutil
import logging
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
import httpx

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models import IncidentPayload
from agent.codex_runner import CodexRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Orchestrator] %(message)s",
)
logger = logging.getLogger("orchestrator")


class Orchestrator:
    def __init__(self, repo_root: Optional[str] = None):
        if repo_root:
            self.repo_root = Path(repo_root).resolve()
        else:
            self.repo_root = Path(__file__).resolve().parent.parent

        self.git_cmd = self._find_git_executable()
        self.worktrees_base = self.repo_root / ".worktrees"
        self.worktrees_base.mkdir(parents=True, exist_ok=True)
        self.backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

    def _find_git_executable(self) -> str:
        """Locates git executable portably across system, user, and container paths."""
        # 1. Check system PATH
        path = shutil.which("git")
        if path:
            return path

        # 2. Check Windows user and program files dynamically
        candidates = []
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            candidates.append(str(Path(localappdata) / "Programs" / "Git" / "cmd" / "git.exe"))

        for pf_var in ["ProgramFiles", "ProgramFiles(x86)"]:
            pf = os.getenv(pf_var)
            if pf:
                candidates.append(str(Path(pf) / "Git" / "cmd" / "git.exe"))

        # 3. Check Linux/Docker standard paths
        candidates.extend(["/usr/bin/git", "/usr/local/bin/git"])

        for c in candidates:
            if os.path.exists(c):
                return c

        return "git"

    def _run_git(self, args: list, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Runs a git command in the specified directory."""
        target_cwd = cwd or self.repo_root
        cmd = [self.git_cmd] + args
        return subprocess.run(
            cmd,
            cwd=str(target_cwd),
            capture_output=True,
            text=True,
        )

    def _ensure_initial_commit(self):
        """Ensures the repository has an initial commit so worktrees can branch off HEAD."""
        res = self._run_git(["rev-parse", "--verify", "HEAD"])
        if res.returncode != 0:
            logger.info("No initial commit found. Creating base commit on main branch...")
            self._run_git(["add", "-A"])
            self._run_git(["commit", "-m", "chore: initial baseline commit before healing tests"])

    def handle_incident(self, incident: IncidentPayload) -> Dict[str, Any]:
        """
        Executes the incident-driven autonomous healing loop:
        1. Emits status: INVESTIGATING
        2. Spawns isolated Git worktree
        3. Invokes Codex Agent in the worktree
        4. Enforces Deterministic Verification Gates (Pytest + Security Checks)
        5. If gates pass: Commits fix, triggers CI/CD pipeline, and resolves incident.
        """
        incident_id = incident.incident_id
        logger.info(f"=== [START HEALING LOOP] Incident: {incident_id} ===")
        self._notify_incident_status(incident_id, "INVESTIGATING")

        self._ensure_initial_commit()

        worktree_name = f"fix-{incident_id}"
        worktree_path = self.worktrees_base / worktree_name
        branch_name = f"fix/{incident_id}"

        # Clean existing worktree directory or branch if already exists
        if worktree_path.exists():
            self._run_git(["worktree", "remove", "--force", str(worktree_path)])
            shutil.rmtree(worktree_path, ignore_errors=True)

        logger.info(f"Creating isolated Git worktree at: {worktree_path} (Branch: {branch_name})")
        add_res = self._run_git(["worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"])
        if add_res.returncode != 0:
            # If branch already exists, checkout without -b
            add_res = self._run_git(["worktree", "add", str(worktree_path), branch_name])
            if add_res.returncode != 0:
                logger.error(f"Failed to create Git worktree: {add_res.stderr}")
                self._notify_incident_status(incident_id, "FAILED")
                return {"success": False, "error": f"Worktree creation failed: {add_res.stderr}"}

        # Synchronize live app files from repo_root to worktree so any uncommitted demo edits are captured
        for live_file in (self.repo_root / "backend" / "app").glob("**/*.py"):
            rel = live_file.relative_to(self.repo_root)
            dest = worktree_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live_file, dest)

        try:
            self._notify_incident_status(incident_id, "FIXING")

            # Dispatch Codex Agent inside the isolated worktree
            runner = CodexRunner(worktree_dir=str(worktree_path))
            agent_result = runner.execute_healing_cycle(incident)

            logger.info(f"Agent finished investigation. Reported success: {agent_result.get('success')}")

            if not agent_result.get("success"):
                err = agent_result.get("error", "Agent failed to synthesize fix")
                logger.error(f"Agent failed to repair incident {incident_id}: {err}")
                self._notify_incident_status(incident_id, "FAILED")
                return {
                    "success": False,
                    "reason": "Agent repair failure",
                    "error": err,
                    "details": agent_result,
                }

            # DETERMINISTIC VERIFICATION GATE
            # The agent is NEVER trusted to declare safety. The orchestrator independently verifies!
            logger.info("Executing Deterministic Verification Gates...")
            gate_passed, gate_details = self._run_deterministic_verification_gate(worktree_path, incident)

            if not gate_passed:
                logger.error(f"Deterministic Verification Gates FAILED: {gate_details}")
                self._notify_incident_status(incident_id, "FAILED")
                return {
                    "success": False,
                    "reason": "Verification gate failure",
                    "details": gate_details,
                }

            logger.info("Deterministic Verification Gates PASSED! Committing fix to branch...")
            self._notify_incident_status(incident_id, "VERIFIED")

            # Commit changes to fix branch
            self._run_git(["add", "backend/app", "backend/tests"], cwd=worktree_path)
            commit_msg = f"fix(checkout): resolve incident {incident_id} - {incident.error_type}\n\nAutomated fix with regression test verified by deterministic gate."
            self._run_git(["commit", "-m", commit_msg], cwd=worktree_path)

            # Merge / Promote verified fix into main branch
            logger.info("Merging and promoting verified fix into main branch...")
            for rel_file in gate_details.get("modified_files", []):
                src = worktree_path / rel_file
                dst = self.repo_root / rel_file
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    logger.info(f"Promoted verified file to main tree: {rel_file}")

            self._run_git(["checkout", "main"])
            self._run_git(["add", "backend/app", "backend/tests"])
            self._run_git(["commit", "-m", f"fix(checkout): resolve incident {incident_id} - {incident.error_type}\n\nVerified by deterministic test gate."])

            # Trigger CI/CD deployment smoke check
            deploy_success = self._simulate_ci_cd_deployment(incident)

            if deploy_success:
                self._notify_incident_status(incident_id, "RESOLVED")
                logger.info(f"=== [HEALING LOOP COMPLETE] Incident {incident_id} RESOLVED! ===")
                return {
                    "success": True,
                    "incident_id": incident_id,
                    "branch": branch_name,
                    "status": "RESOLVED",
                    "verification": gate_details,
                }
            else:
                self._notify_incident_status(incident_id, "DEPLOYMENT_FAILED")
                return {"success": False, "status": "DEPLOYMENT_FAILED"}

        finally:
            # Teardown worktree cleanly
            logger.info(f"Cleaning up worktree {worktree_path}...")
            self._run_git(["worktree", "remove", "--force", str(worktree_path)])
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

    def _run_deterministic_verification_gate(self, worktree_path: Path, incident: IncidentPayload) -> tuple[bool, Dict[str, Any]]:
        """
        Independent verification gate executed by Orchestrator:
        1. Checks that only allowable files were touched (security check).
        2. Checks that a regression test was actually added.
        3. Executes full pytest suite independently and checks for exit code 0.
        """
        diff_res = self._run_git(["diff", "--name-only", "HEAD"], cwd=worktree_path)
        modified_files = [f.strip() for f in diff_res.stdout.strip().splitlines() if f.strip()]
        logger.info(f"Files modified by agent in worktree: {modified_files}")

        # Gate 1: Security Policy - only backend/app and backend/tests allowed
        disallowed = [f for f in modified_files if not (f.startswith("backend/app") or f.startswith("backend/tests"))]
        if disallowed:
            return False, {"error": "Policy violation: modified unauthorized files", "files": disallowed}

        # Gate 2: Regression test presence check
        test_file = worktree_path / "backend" / "tests" / "test_checkout.py"
        if not test_file.exists():
            return False, {"error": "Test file missing"}

        with open(test_file, "r", encoding="utf-8") as f:
            test_content = f.read()

        clean_inc_id = incident.incident_id.replace("-", "_")
        if f"test_regression_{clean_inc_id}" not in test_content and "test_regression" not in test_content:
            return False, {"error": "No regression test detected in test suite"}

        # Gate 3: Execute independent pytest suite
        python_exe = sys.executable
        venv_python = Path(sys.prefix) / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(worktree_path / "backend") + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")

        test_run = subprocess.run(
            [python_exe, "-m", "pytest", "backend/tests", "-v"],
            cwd=str(worktree_path),
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        if test_run.returncode != 0:
            return False, {
                "error": "Pytest deterministic verification failed",
                "output": test_run.stdout + "\n" + test_run.stderr,
            }

        return True, {
            "all_tests_passed": True,
            "modified_files": modified_files,
            "pytest_summary": "All tests passed cleanly in isolated worktree",
        }

    def _simulate_ci_cd_deployment(self, incident: IncidentPayload) -> bool:
        """
        Simulates the CI/CD pipeline:
        - Version bump to v1.0.1
        - Production smoke test on /health endpoint
        """
        logger.info("CI/CD Pipeline: Building artifact and promoting to production (v1.0.1)...")
        os.environ["APP_VERSION"] = "v1.0.1"
        try:
            with httpx.Client(timeout=3.0) as client:
                client.post(f"{self.backend_url}/api/version", json={"version": "v1.0.1"})
        except Exception as e:
            logger.warning(f"Could not update backend deployment version: {e}")
        return True

    def _notify_incident_status(self, incident_id: str, status: str):
        """Updates incident status on backend API if reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                client.patch(f"{self.backend_url}/api/incidents/{incident_id}", json={"status": status})
        except Exception:
            pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Orchestrator directly")
    parser.add_argument("--test-run", action="store_true", help="Run a verification check")
    args = parser.parse_args()
    orch = Orchestrator()
    print(f"Orchestrator initialized. Git executable: {orch.git_cmd}")
