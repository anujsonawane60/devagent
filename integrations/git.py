"""Git integration for branch, commit, push, and diff operations."""

from dataclasses import dataclass, field
from typing import List, Optional

import git


@dataclass
class GitStatus:
    """Current state of a git repository."""
    branch: str
    changed_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    is_clean: bool = True


@dataclass
class CommitResult:
    """Result of a git commit operation."""
    sha: str
    message: str
    branch: str


class GitManager:
    """Manages git operations for a repository."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_status(self) -> GitStatus:
        """Get the current repository status."""
        changed = [item.a_path for item in self.repo.index.diff(None)]
        try:
            staged = [item.a_path for item in self.repo.index.diff("HEAD")]
        except git.BadName:
            # No commits yet — everything staged is new
            staged = []
        all_changed = list(set(changed + staged))
        untracked = self.repo.untracked_files
        is_clean = len(all_changed) == 0 and len(untracked) == 0
        try:
            branch = self.get_current_branch()
        except TypeError:
            branch = "HEAD"
        return GitStatus(
            branch=branch,
            changed_files=all_changed,
            untracked_files=list(untracked),
            is_clean=is_clean,
        )

    def create_branch(self, name: str, checkout: bool = True):
        """Create a new branch, optionally checking it out."""
        new_branch = self.repo.create_head(name)
        if checkout:
            new_branch.checkout()

    def checkout_branch(self, name: str):
        """Checkout an existing branch."""
        self.repo.heads[name].checkout()

    def stage_files(self, paths: List[str]):
        """Stage specific files for commit."""
        self.repo.index.add(paths)

    def stage_all(self):
        """Stage all changes (git add -A)."""
        self.repo.git.add(A=True)

    def commit(self, message: str) -> CommitResult:
        """Create a commit with the given message."""
        commit = self.repo.index.commit(message)
        return CommitResult(
            sha=commit.hexsha,
            message=message,
            branch=self.get_current_branch(),
        )

    def get_diff(self, staged: bool = False) -> str:
        """Get diff output. If staged=True, show staged changes."""
        if staged:
            return self.repo.git.diff("--cached")
        return self.repo.git.diff()

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        return self.repo.active_branch.name

    def has_remote(self) -> bool:
        """Check if the repo has any remotes configured."""
        return len(self.repo.remotes) > 0

    def push(self, branch: Optional[str] = None):
        """Push to remote. Skips if no remote is configured."""
        if not self.has_remote():
            return
        target = branch or self.get_current_branch()
        self.repo.remotes.origin.push(target)
