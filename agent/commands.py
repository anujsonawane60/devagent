"""Business logic for bot commands."""

import os

from agent.safety import SafetyManager, ValidationRunner
from code_engine.analyzer import ProjectAnalyzer
from code_engine.generator import CodeGenerator
from code_engine.parser import CodeParser
from code_engine.search import CodeSearchEngine
from config.llm import LLMProvider
from integrations.git import GitManager
from integrations.github import GitHubManager
from integrations.sentry import SentryClient
from integrations.vercel import VercelClient
from storage.db import Database


class CommandHandler:
    def __init__(
        self,
        analyzer: ProjectAnalyzer | None = None,
        db: Database | None = None,
        llm: LLMProvider | None = None,
        github: GitHubManager | None = None,
        sentry: SentryClient | None = None,
        vercel: VercelClient | None = None,
    ):
        self.analyzer = analyzer or ProjectAnalyzer()
        self.db = db
        self.llm = llm
        self.github = github
        self.sentry = sentry
        self.vercel = vercel
        self._search_engine: CodeSearchEngine | None = None
        self._parser: CodeParser | None = None

    @property
    def search_engine(self) -> CodeSearchEngine | None:
        if self._search_engine is None and self.db is not None:
            self._search_engine = CodeSearchEngine(self.db)
        return self._search_engine

    @property
    def parser(self) -> CodeParser:
        if self._parser is None:
            self._parser = CodeParser()
        return self._parser

    def help(self) -> str:
        return (
            "DevAgent Commands:\n"
            "/help - Show this message\n"
            "/status - Show bot status\n"
            "/analyze <path> - Analyze a project directory\n"
            "/index <path> - Index a project for code search\n"
            "/search <query> - Search indexed code\n"
            "/find <name> - Find a definition by name\n"
            "/generate <task> - Generate code changes for a task\n"
            "/diff <path> - Show current git diff\n"
            "/validate <path> - Run project validation checks\n"
            "/undo <path> - Rollback last change\n"
            "/add <feature description> - Build a feature on a new branch\n"
            "/fix [issue_id] - Auto-fix a Sentry error\n"
            "/deploy <staging|production> - Deploy via Vercel\n"
            "/errors - Show recent Sentry errors\n"
            "/pr <title> - Create a GitHub pull request\n"
            "/setup <path> - Initialize DevAgent for a project"
        )

    def status(self) -> str:
        integrations = []
        if self.llm:
            integrations.append("LLM")
        if self.github:
            integrations.append("GitHub")
        if self.sentry:
            integrations.append("Sentry")
        if self.vercel:
            integrations.append("Vercel")
        if self.db:
            integrations.append("DB")
        status_parts = ["DevAgent is running. Ready to assist."]
        if integrations:
            status_parts.append(f"Active: {', '.join(integrations)}")
        return "\n".join(status_parts)

    def analyze(self, project_path: str) -> str:
        if not project_path:
            return "Usage: /analyze <path>"
        manifest = self.analyzer.analyze(project_path)
        if manifest.language == "unknown":
            return f"Could not detect project at: {project_path}"
        return (
            f"Project Analysis:\n"
            f"Path: {manifest.path}\n"
            f"{manifest.summary()}\n"
            f"Config files: {', '.join(manifest.config_files)}\n"
            f"Entry points: {', '.join(manifest.entry_points)}"
        )

    async def index(self, project_path: str) -> str:
        """Index a project for code search."""
        if not project_path:
            return "Usage: /index <path>"
        if self.search_engine is None:
            return "Database not available."
        count = await self.search_engine.index_project(project_path, self.parser)
        return f"Indexed {count} entities from: {project_path}"

    async def search(self, query: str, project_path: str = "") -> str:
        """Search indexed code entities."""
        if not query:
            return "Usage: /search <query>"
        if self.search_engine is None:
            return "Database not available."
        results = await self.search_engine.search(query, project_path=project_path or None, limit=10)
        if not results:
            return f"No results found for: {query}"
        lines = [f"Search results for '{query}':"]
        for r in results:
            lines.append(f"  {r.entity_type} {r.entity_name} — {r.file_path}:{r.line}")
        return "\n".join(lines)

    async def find(self, name: str, project_path: str = "") -> str:
        """Find a definition by exact name."""
        if not name:
            return "Usage: /find <name>"
        if self.search_engine is None:
            return "Database not available."
        result = await self.search_engine.find_definition(name, project_path=project_path or None)
        if not result:
            return f"Definition not found: {name}"
        return (
            f"Found: {result['entity_type']} {result['name']}\n"
            f"File: {result['file_path']}:{result['line_start']}\n"
            f"Signature: {result.get('signature', 'N/A')}"
        )

    async def generate(self, task: str, project_path: str) -> str:
        """Generate code changes for a task using the LLM."""
        if not task:
            return "Usage: /generate <task description>"
        if self.llm is None:
            return "LLM provider not configured."
        context_builder = None
        if self.search_engine is not None:
            from agent.context import ContextBuilder
            context_builder = ContextBuilder(self.search_engine)
        generator = CodeGenerator(self.llm, context_builder=context_builder)
        plan = await generator.generate_plan(task, project_path)
        if not plan.changes:
            return "No changes generated for the given task."
        result = generator.apply_plan(plan, project_path)
        if result.success:
            lines = [f"Generated {len(plan.changes)} change(s):"]
            for c in plan.changes:
                lines.append(f"  [{c.action}] {c.file_path} — {c.description}")
            return "\n".join(lines)
        return f"Generation failed: {result.error}"

    async def validate(self, project_path: str) -> str:
        """Run validation checks on a project."""
        if not project_path:
            return "Usage: /validate <path>"
        runner = ValidationRunner(project_path)
        checks = runner.detect_checks()
        if not checks:
            return "No validation checks detected for this project."
        result = await runner.run_all(checks)
        return result.summary

    def undo(self, project_path: str) -> str:
        """Rollback to the last checkpoint."""
        if not project_path:
            return "Usage: /undo <path>"
        try:
            sm = SafetyManager(project_path)
            checkpoints = sm.get_checkpoints()
            if not checkpoints:
                return "No checkpoints available to rollback to."
            cp = checkpoints[-1]
            sm.rollback(cp)
            return f"Rolled back to checkpoint: {cp.description or cp.sha[:8]}"
        except Exception as e:
            return f"Undo error: {e}"

    def diff(self, project_path: str) -> str:
        """Show the current git diff for a project."""
        if not project_path:
            return "Usage: /diff <path>"
        try:
            gm = GitManager(project_path)
            diff_output = gm.get_diff()
            if not diff_output:
                return "No unstaged changes."
            return f"Git diff:\n{diff_output}"
        except Exception as e:
            return f"Git error: {e}"

    async def add_feature(self, description: str, project_path: str) -> str:
        """Build a feature: create branch, generate code, validate, commit."""
        if not description:
            return "Usage: /add <feature description>"
        if self.llm is None:
            return "LLM provider not configured."
        if not project_path:
            return "Usage: /add <feature description> (set project path first)"

        try:
            # Set up safety manager and feature branch
            sm = SafetyManager(project_path)
            branch_name = "feature/" + description.lower().replace(" ", "-")[:40]
            sm.ensure_feature_branch(branch_name)

            # Generate code
            context_builder = None
            if self.search_engine is not None:
                from agent.context import ContextBuilder
                context_builder = ContextBuilder(self.search_engine)
            generator = CodeGenerator(self.llm, context_builder=context_builder)
            plan = await generator.generate_plan(description, project_path)

            if not plan.changes:
                return "No changes generated for the given feature."

            # Safe apply: checkpoint -> apply -> validate -> rollback on fail
            result = await sm.safe_apply(generator, plan, project_path, validate=True)

            if not result.success:
                return f"Feature generation failed: {result.error}"

            # Stage and commit
            sm.git.stage_all()
            commit_result = sm.git.commit(f"feat: {description}")

            lines = [
                f"Feature built on branch '{branch_name}':",
                f"Commit: {commit_result.sha[:8]} — {commit_result.message}",
                f"Files changed: {len(plan.changes)}",
            ]
            for c in plan.changes:
                lines.append(f"  [{c.action}] {c.file_path}")
            lines.append("\nUse /pr to create a pull request.")
            return "\n".join(lines)

        except Exception as e:
            return f"Feature error: {e}"

    async def fix_error(self, issue_id: str, project_path: str) -> str:
        """Auto-fix a Sentry error: fetch details, generate fix, validate, commit."""
        if self.sentry is None:
            return "Sentry not configured. Set SENTRY_AUTH_TOKEN, SENTRY_ORG, SENTRY_PROJECT."
        if self.llm is None:
            return "LLM provider not configured."

        try:
            # If no issue_id, get the latest unresolved issue
            if not issue_id:
                issues = await self.sentry.get_issues(limit=1)
                if not issues:
                    return "No unresolved Sentry errors found."
                issue_id = issues[0].issue_id

            # Get full error details
            error = await self.sentry.get_issue_details(issue_id)

            # Generate fix using error context
            fix_prompt = (
                f"Fix this error in the codebase:\n\n{error.fix_context}\n\n"
                "Generate the minimal code changes needed to fix this error."
            )

            context_builder = None
            if self.search_engine is not None:
                from agent.context import ContextBuilder
                context_builder = ContextBuilder(self.search_engine)
            generator = CodeGenerator(self.llm, context_builder=context_builder)

            if project_path:
                sm = SafetyManager(project_path)
                branch_name = f"fix/sentry-{issue_id}"
                sm.ensure_feature_branch(branch_name)

                plan = await generator.generate_plan(fix_prompt, project_path)
                if not plan.changes:
                    return f"Could not generate fix for: {error.title}"

                result = await sm.safe_apply(generator, plan, project_path, validate=True)
                if not result.success:
                    return f"Fix failed validation: {result.error}"

                sm.git.stage_all()
                sm.git.commit(f"fix: {error.title}")

                return (
                    f"Fixed: {error.title}\n"
                    f"Branch: {branch_name}\n"
                    f"Changes: {len(plan.changes)} file(s)\n"
                    "Use /pr to create a pull request."
                )
            else:
                plan = await generator.generate_plan(fix_prompt, "")
                if not plan.changes:
                    return f"Could not generate fix for: {error.title}"
                lines = [f"Suggested fix for: {error.title}"]
                for c in plan.changes:
                    lines.append(f"  [{c.action}] {c.file_path} — {c.description}")
                return "\n".join(lines)

        except Exception as e:
            return f"Fix error: {e}"

    async def deploy(self, environment: str, project_path: str) -> str:
        """Deploy via Vercel to staging or production."""
        if self.vercel is None:
            return "Vercel not configured. Set VERCEL_TOKEN and VERCEL_PROJECT_ID."
        if not environment:
            return "Usage: /deploy <staging|production>"

        env = environment.lower().strip()
        if env not in ("staging", "production", "preview"):
            return "Environment must be 'staging' or 'production'."

        try:
            # Get current branch for deployment
            target = "production" if env == "production" else "preview"
            branch = "main"
            if project_path:
                try:
                    gm = GitManager(project_path)
                    branch = gm.get_current_branch()
                    # Push before deploying
                    if gm.has_remote():
                        gm.push(branch)
                except Exception:
                    pass

            deployment = await self.vercel.create_deployment(
                git_ref=branch,
                target=target,
            )

            return (
                f"Deployment triggered!\n"
                f"Environment: {target}\n"
                f"Branch: {branch}\n"
                f"URL: {deployment.url}\n"
                f"State: {deployment.state}\n"
                f"ID: {deployment.id}"
            )
        except Exception as e:
            return f"Deploy error: {e}"

    async def errors(self) -> str:
        """Show recent Sentry errors."""
        if self.sentry is None:
            return "Sentry not configured. Set SENTRY_AUTH_TOKEN, SENTRY_ORG, SENTRY_PROJECT."
        try:
            issues = await self.sentry.get_issues(limit=5)
            if not issues:
                return "No unresolved errors found."
            lines = [f"Recent errors ({len(issues)}):"]
            for issue in issues:
                lines.append(issue.summary)
                lines.append("")
            return "\n".join(lines)
        except Exception as e:
            return f"Sentry error: {e}"

    async def create_pr(self, title: str, project_path: str) -> str:
        """Create a GitHub pull request for the current branch."""
        if self.github is None:
            return "GitHub not configured. Set GITHUB_TOKEN."
        if not title:
            return "Usage: /pr <title>"

        try:
            # Detect repo from git remote
            if project_path:
                gm = GitManager(project_path)
                branch = gm.get_current_branch()
                if gm.has_remote():
                    remote_url = gm.repo.remotes.origin.url
                    self.github.detect_repo_from_remote(remote_url)
                    gm.push(branch)
            else:
                branch = "main"

            pr = await self.github.create_pull_request(
                title=title,
                head=branch,
                base="main",
                body=f"Auto-generated by DevAgent\n\nBranch: {branch}",
            )
            return f"PR created: {pr.url}\n#{pr.number}: {pr.title}"

        except Exception as e:
            return f"PR error: {e}"

    async def setup_project(self, project_path: str) -> str:
        """Initialize DevAgent for a project: analyze, index, detect checks."""
        if not project_path:
            return "Usage: /setup <path>"
        if not os.path.isdir(project_path):
            return f"Directory not found: {project_path}"

        lines = ["Setting up DevAgent...\n"]

        # 1. Analyze project
        manifest = self.analyzer.analyze(project_path)
        lines.append(f"Project: {manifest.language}/{manifest.framework}")
        lines.append(f"Dependencies: {len(manifest.dependencies)}")

        # 2. Index code
        if self.search_engine is not None:
            count = await self.search_engine.index_project(project_path, self.parser)
            lines.append(f"Indexed: {count} code entities")
        else:
            lines.append("Indexing: skipped (no database)")

        # 3. Detect validation checks
        runner = ValidationRunner(project_path)
        checks = runner.detect_checks()
        if checks:
            lines.append(f"Validation: {len(checks)} check(s) detected")
            for name, cmd in checks:
                lines.append(f"  - {name}: {' '.join(cmd)}")
        else:
            lines.append("Validation: no checks detected")

        # 4. Check git
        try:
            gm = GitManager(project_path)
            status = gm.get_status()
            lines.append(f"Git: branch '{status.branch}', {'clean' if status.is_clean else 'dirty'}")
            if gm.has_remote():
                lines.append(f"Remote: {gm.repo.remotes.origin.url}")
        except Exception:
            lines.append("Git: not a git repository")

        lines.append("\nReady! Use /help to see available commands.")
        return "\n".join(lines)
