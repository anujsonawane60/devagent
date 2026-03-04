"""Safety checks, validation, and guardrails for code changes."""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Tuple

from code_engine.generator import CodeGenerator, GenerationPlan, GenerationResult
from integrations.git import GitManager


@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    name: str
    command: List[str]
    passed: bool = True
    output: str = ""


@dataclass
class ValidationResult:
    """Aggregate result of all validation checks."""
    checks: List[ValidationCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def summary(self) -> str:
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        failed = total - passed
        lines = [f"Validation: {passed}/{total} passed"]
        for c in self.checks:
            status = "PASS" if c.passed else "FAIL"
            lines.append(f"  [{status}] {c.name}")
        if failed:
            lines.append(f"\n{failed} check(s) failed.")
        return "\n".join(lines)


@dataclass
class Checkpoint:
    """A saved state for rollback."""
    branch: str
    sha: str
    timestamp: str = ""
    description: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ValidationRunner:
    """Runs validation checks (lint, type-check, build, test) via subprocess."""

    def __init__(self, project_path: str):
        self.project_path = project_path

    async def run_check(self, name: str, command: List[str]) -> ValidationCheck:
        """Run a single validation command and return the result."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_path,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=300)
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            passed = process.returncode == 0
            return ValidationCheck(name=name, command=command, passed=passed, output=output)
        except asyncio.TimeoutError:
            return ValidationCheck(
                name=name, command=command, passed=False, output="Timed out after 300s"
            )
        except Exception as e:
            return ValidationCheck(
                name=name, command=command, passed=False, output=str(e)
            )

    async def run_all(self, checks: List[Tuple[str, List[str]]]) -> ValidationResult:
        """Run multiple validation checks sequentially."""
        results = []
        for name, command in checks:
            result = await self.run_check(name, command)
            results.append(result)
        return ValidationResult(checks=results)

    def detect_checks(self) -> List[Tuple[str, List[str]]]:
        """Auto-detect available validation checks from project files."""
        checks: List[Tuple[str, List[str]]] = []

        # Check for package.json (Node.js project)
        pkg_json = os.path.join(self.project_path, "package.json")
        if os.path.isfile(pkg_json):
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                scripts = pkg.get("scripts", {})
                if "lint" in scripts:
                    checks.append(("lint", ["npm", "run", "lint"]))
                if "typecheck" in scripts:
                    checks.append(("typecheck", ["npm", "run", "typecheck"]))
                if "build" in scripts:
                    checks.append(("build", ["npm", "run", "build"]))
                if "test" in scripts:
                    checks.append(("test", ["npm", "run", "test"]))
            except (json.JSONDecodeError, OSError):
                pass

        # Check for pyproject.toml (Python project)
        pyproject = os.path.join(self.project_path, "pyproject.toml")
        if os.path.isfile(pyproject):
            checks.append(("lint", ["python", "-m", "ruff", "check", "."]))
            checks.append(("typecheck", ["python", "-m", "mypy", "."]))
            checks.append(("test", ["python", "-m", "pytest"]))

        # Check for setup.py (Python project, fallback)
        setup_py = os.path.join(self.project_path, "setup.py")
        if os.path.isfile(setup_py) and not os.path.isfile(pyproject):
            checks.append(("test", ["python", "-m", "pytest"]))

        return checks


class SafetyManager:
    """Orchestrates safe code changes: checkpoint, validate, rollback."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.git = GitManager(repo_path)
        self._checkpoints: List[Checkpoint] = []

    def create_checkpoint(self, description: str = "") -> Checkpoint:
        """Save current state as a checkpoint."""
        branch = self.git.get_current_branch()
        sha = self.git.repo.head.commit.hexsha
        cp = Checkpoint(branch=branch, sha=sha, description=description)
        self._checkpoints.append(cp)
        return cp

    def rollback(self, checkpoint: Checkpoint) -> None:
        """Restore repository to a checkpoint state."""
        self.git.repo.git.reset("--hard", checkpoint.sha)
        current = self.git.get_current_branch()
        if current != checkpoint.branch:
            self.git.checkout_branch(checkpoint.branch)

    def get_checkpoints(self) -> List[Checkpoint]:
        """Return all saved checkpoints."""
        return list(self._checkpoints)

    def ensure_feature_branch(self, branch_name: str) -> None:
        """Create/checkout a feature branch. Refuse to work on main/master."""
        current = self.git.get_current_branch()
        if current in ("main", "master"):
            if branch_name in ("main", "master"):
                raise ValueError("Refusing to work directly on main/master branch.")
            try:
                self.git.checkout_branch(branch_name)
            except (IndexError, Exception):
                self.git.create_branch(branch_name, checkout=True)
        elif current != branch_name:
            try:
                self.git.checkout_branch(branch_name)
            except (IndexError, Exception):
                self.git.create_branch(branch_name, checkout=True)

    async def safe_apply(
        self,
        generator: CodeGenerator,
        plan: GenerationPlan,
        base_path: str,
        validate: bool = True,
    ) -> GenerationResult:
        """Checkpoint -> apply -> validate -> rollback on failure."""
        cp = self.create_checkpoint(f"Before: {plan.task}")

        result = generator.apply_plan(plan, base_path)
        if not result.success:
            self.rollback(cp)
            return result

        if validate:
            runner = ValidationRunner(base_path)
            checks = runner.detect_checks()
            if checks:
                val_result = await runner.run_all(checks)
                if not val_result.all_passed:
                    self.rollback(cp)
                    return GenerationResult(
                        plan=plan,
                        success=False,
                        error=f"Validation failed:\n{val_result.summary}",
                    )

        return result
