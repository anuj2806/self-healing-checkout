"""
Codex & Claude Code Autonomous CLI Runner.

Strict CLI Agent Runner:
- Invokes **Codex CLI** (`codex exec ...`) when OPENAI_API_KEY is configured.
- Invokes **Claude Code CLI** (`claude -p ...`) when ANTHROPIC_API_KEY is configured.

All repairs, code investigations, and regression tests are executed directly through the CLI tool.
"""

import os
import sys
import json
import logging
import subprocess
import shutil
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.models import IncidentPayload

logger = logging.getLogger("codex_runner")


class CodexRunner:
    def __init__(self, worktree_dir: str):
        self.worktree_dir = Path(worktree_dir).resolve()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.codex_cmd = self._find_codex_cli()
        self.claude_cmd = self._find_claude_cli()

    def _find_codex_cli(self) -> Optional[str]:
        """Locates the codex CLI binary across system, npm, and user paths."""
        for name in ["codex", "codex.exe", "codex.cmd"]:
            path = shutil.which(name)
            if path:
                return path

        appdata = os.getenv("APPDATA")
        if appdata:
            npm_codex = Path(appdata) / "npm" / "codex.cmd"
            if npm_codex.exists():
                return str(npm_codex)

        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            local_codex = Path(localappdata) / "Programs" / "Codex" / "codex.exe"
            if local_codex.exists():
                return str(local_codex)

        for linux_path in ["/usr/local/bin/codex", "/usr/bin/codex"]:
            if os.path.exists(linux_path):
                return linux_path

        return None

    def _find_claude_cli(self) -> Optional[str]:
        """Locates the claude CLI binary across system and npm paths."""
        for name in ["claude", "claude.cmd"]:
            path = shutil.which(name)
            if path:
                return path

        appdata = os.getenv("APPDATA")
        if appdata:
            npm_claude = Path(appdata) / "npm" / "claude.cmd"
            if npm_claude.exists():
                return str(npm_claude)

        for linux_path in ["/usr/local/bin/claude", "/usr/bin/claude"]:
            if os.path.exists(linux_path):
                return linux_path

        return None

    def execute_healing_cycle(self, incident: IncidentPayload) -> Dict[str, Any]:
        """
        Executes the autonomous agent repair loop inside the isolated worktree
        using Codex CLI or Claude Code CLI.
        """
        logger.info(f"Agent starting investigation for Incident {incident.incident_id}...")
        logger.info(f"Root Cause Error: {incident.error_type} - {incident.error_message}")

        # Check API key configuration
        if not self.openai_key and not self.anthropic_key:
            err_msg = (
                "No AI API key found! Please set OPENAI_API_KEY (to use Codex CLI) "
                "or ANTHROPIC_API_KEY (to use Claude Code CLI) in your environment or .env file."
            )
            logger.error(err_msg)
            return {
                "success": False,
                "error": err_msg,
                "incident_id": incident.incident_id,
            }

        fault_info = self._analyze_incident(incident)
        logger.info(f"Fault located in: {fault_info['target_file']} around line {fault_info['line_number']}")

        cli_succeeded = False
        agent_type = "unknown"

        # 1. If OpenAI key is set: Run Codex CLI
        if self.openai_key:
            agent_type = "codex-cli"
            if not self.codex_cmd:
                err_msg = "OPENAI_API_KEY is present, but codex CLI executable was not found in PATH or npm."
                logger.error(err_msg)
                return {"success": False, "error": err_msg, "incident_id": incident.incident_id}

            logger.info("OPENAI_API_KEY detected. Dispatched to Codex CLI...")
            cli_succeeded = self._run_with_codex_cli(incident, fault_info)

        # 2. If Anthropic key is set: Run Claude Code CLI
        elif self.anthropic_key:
            agent_type = "claude-code"
            if not self.claude_cmd:
                err_msg = "ANTHROPIC_API_KEY is present, but claude CLI executable was not found in PATH or npm."
                logger.error(err_msg)
                return {"success": False, "error": err_msg, "incident_id": incident.incident_id}

            logger.info("ANTHROPIC_API_KEY detected. Dispatched to Claude Code CLI...")
            cli_succeeded = self._run_with_claude_code(incident, fault_info)

        if not cli_succeeded:
            logger.error(f"{agent_type} was unable to synthesize and apply a fix.")
            return {
                "success": False,
                "error": f"{agent_type} execution failed.",
                "incident_id": incident.incident_id,
                "agent_type": agent_type,
            }

        # Step 3: Run independent test suite in worktree to verify CLI's work
        test_success, test_output = self._run_tests()
        logger.info(f"Post-fix test execution result: {'PASS' if test_success else 'FAIL'}")

        return {
            "success": test_success,
            "target_file": fault_info["target_file"],
            "test_output": test_output,
            "error_type": incident.error_type,
            "incident_id": incident.incident_id,
            "agent_type": agent_type,
        }

    def _run_with_codex_cli(self, incident: IncidentPayload, fault_info: Dict[str, Any]) -> bool:
        """Invokes Codex CLI non-interactively inside the isolated worktree."""
        prompt = (
            f"Fix production incident {incident.incident_id}:\n"
            f"Error: {incident.error_type} - {incident.error_message}\n"
            f"Failing File: {fault_info['target_file']}\n"
            f"Stack Trace:\n{incident.stack_trace}\n\n"
            f"Request Payload:\n{json.dumps(incident.request_payload, indent=2)}\n\n"
            "Required Actions:\n"
            "1. In backend/tests/test_checkout.py, add a regression test for this incident.\n"
            "2. In backend/app/tax.py, fix the tax calculation so unlisted states and missing variables are safely handled.\n"
            "3. Run pytest backend/tests and ensure all tests pass."
        )

        try:
            logger.info(f"Executing: {self.codex_cmd} exec ...")
            cmd = [self.codex_cmd, "exec", prompt, "--dangerously-bypass-approvals-and-sandbox"]
            res = subprocess.run(
                cmd,
                cwd=str(self.worktree_dir),
                capture_output=True,
                text=True,
                timeout=180,
                env=os.environ.copy(),
            )
            logger.info(f"Codex CLI completed with return code {res.returncode}")
            if res.returncode == 0:
                return True
            else:
                logger.warning(f"Codex CLI stderr: {res.stderr[:300]}")
        except Exception as e:
            logger.error(f"Codex CLI process execution error: {e}")
        return False

    def _run_with_claude_code(self, incident: IncidentPayload, fault_info: Dict[str, Any]) -> bool:
        """Invokes Claude Code CLI inside the isolated worktree in headless mode."""
        prompt = (
            f"Fix production incident {incident.incident_id}:\n"
            f"Error: {incident.error_type} - {incident.error_message}\n"
            f"Failing File: {fault_info['target_file']}\n"
            f"Stack Trace:\n{incident.stack_trace}\n\n"
            f"Request Payload:\n{json.dumps(incident.request_payload, indent=2)}\n\n"
            "Required Actions:\n"
            "1. In backend/tests/test_checkout.py, add a regression test for this incident.\n"
            "2. In backend/app/tax.py, fix the tax calculation so unlisted states and missing variables are safely handled.\n"
            "3. Run pytest backend/tests and verify all tests pass."
        )

        try:
            logger.info(f"Executing: {self.claude_cmd} -p ...")
            cmd = [self.claude_cmd, "-p", prompt, "--dangerously-skip-permissions"]
            res = subprocess.run(
                cmd,
                cwd=str(self.worktree_dir),
                capture_output=True,
                text=True,
                timeout=180,
                env=os.environ.copy(),
            )
            logger.info(f"Claude Code CLI completed with return code {res.returncode}")
            if res.returncode == 0:
                return True
            else:
                logger.warning(f"Claude Code stderr: {res.stderr[:300]}")
        except Exception as e:
            logger.error(f"Claude Code CLI process execution error: {e}")
        return False

    def _analyze_incident(self, incident: IncidentPayload) -> Dict[str, Any]:
        """Parses the stack trace and request payload to identify failing file and parameters."""
        target_file = "backend/app/tax.py"
        line_number = 36

        tb = incident.stack_trace
        matches = re.findall(r'File "([^"]+)", line (\d+), in (\w+)', tb)
        for filepath, line, func in matches:
            if "tax.py" in filepath or "checkout.py" in filepath:
                if "tax.py" in filepath:
                    target_file = "backend/app/tax.py"
                elif "checkout.py" in filepath:
                    target_file = "backend/app/checkout.py"
                line_number = int(line)

        shipping = incident.request_payload.get("shipping_address", {})
        failed_state = shipping.get("state", "FL")
        failed_country = shipping.get("country", "US")

        return {
            "target_file": target_file,
            "line_number": line_number,
            "failed_state": failed_state,
            "failed_country": failed_country,
            "request_payload": incident.request_payload,
        }

    def _run_tests(self) -> Tuple[bool, str]:
        """Runs pytest inside the isolated worktree directory."""
        python_exe = sys.executable
        venv_python = Path(sys.prefix) / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)

        cmd = [python_exe, "-m", "pytest", "backend/tests", "-v"]

        # Ensure PYTHONPATH includes backend
        env = os.environ.copy()
        backend_path = str(self.worktree_dir / "backend")
        env["PYTHONPATH"] = backend_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")

        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.worktree_dir),
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            return (res.returncode == 0, res.stdout + "\n" + res.stderr)
        except Exception as e:
            return (False, f"Test execution failed with error: {str(e)}")
