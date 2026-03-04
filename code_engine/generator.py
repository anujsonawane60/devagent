"""LLM-powered code generation engine."""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from config.llm import LLMMessage, LLMProvider


@dataclass
class FileChange:
    """A single file change in a generation plan."""
    file_path: str
    action: str  # "create", "modify", "delete"
    content: str = ""
    description: str = ""


@dataclass
class GenerationPlan:
    """A plan of file changes to apply."""
    task: str
    changes: List[FileChange] = field(default_factory=list)
    summary: str = ""


@dataclass
class GenerationResult:
    """Result of applying a generation plan."""
    plan: GenerationPlan
    success: bool = True
    error: Optional[str] = None


class CodeGenerator:
    """Generates code changes using an LLM."""

    def __init__(self, llm: LLMProvider, context_builder=None):
        self.llm = llm
        self.context_builder = context_builder

    async def generate_plan(self, task: str, project_path: str) -> GenerationPlan:
        """Generate a plan of file changes for a task.

        1. Use ContextBuilder to get relevant files
        2. Build prompts with project context
        3. Call LLM to produce structured file changes
        4. Parse response into GenerationPlan
        """
        context_str = ""
        if self.context_builder:
            context_result = await self.context_builder.get_context(
                task, project_path, max_files=10, token_budget=3000
            )
            context_str = self.context_builder.format_context(context_result)

        system_prompt = self._build_system_prompt(project_path, context_str)
        generation_prompt = self._build_generation_prompt(task, context_str)

        messages = [
            LLMMessage(role="user", content=f"{system_prompt}\n\n{generation_prompt}"),
        ]

        response = await self.llm.generate(messages)
        changes = self._parse_llm_response(response.content)

        return GenerationPlan(
            task=task,
            changes=changes,
            summary=f"Generated {len(changes)} file change(s) for: {task}",
        )

    def apply_plan(self, plan: GenerationPlan, base_path: str) -> GenerationResult:
        """Apply a generation plan by creating/modifying/deleting files."""
        try:
            for change in plan.changes:
                full_path = os.path.join(base_path, change.file_path)

                if change.action == "create":
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(change.content)

                elif change.action == "modify":
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(change.content)

                elif change.action == "delete":
                    if os.path.exists(full_path):
                        os.remove(full_path)

            return GenerationResult(plan=plan, success=True)
        except Exception as e:
            return GenerationResult(plan=plan, success=False, error=str(e))

    def _build_system_prompt(self, project_path: str, context: str) -> str:
        """Build the system prompt with project info and context."""
        project_name = Path(project_path).name if project_path else "unknown"
        prompt = (
            "You are a senior developer. Given the project context and task, "
            "generate file changes as JSON.\n\n"
            f"Project: {project_name}\n"
            f"Project path: {project_path}\n"
        )
        if context:
            prompt += f"\nRelevant code:\n{context}\n"
        return prompt

    def _build_generation_prompt(self, task: str, context_str: str) -> str:
        """Build the generation prompt with the task description."""
        return (
            f"Task: {task}\n\n"
            "Respond ONLY with JSON in this exact format:\n"
            '{"changes": [{"file_path": "...", "action": "create|modify|delete", '
            '"content": "...", "description": "..."}], "summary": "..."}'
        )

    def _parse_llm_response(self, response: str) -> List[FileChange]:
        """Parse JSON from LLM output into FileChange objects."""
        # Strip markdown code fences if present
        cleaned = response.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return []

        changes = []
        raw_changes = data.get("changes", [])
        if not isinstance(raw_changes, list):
            return []

        for item in raw_changes:
            if not isinstance(item, dict):
                continue
            if "file_path" not in item or "action" not in item:
                continue
            changes.append(FileChange(
                file_path=item["file_path"],
                action=item["action"],
                content=item.get("content", ""),
                description=item.get("description", ""),
            ))

        return changes
