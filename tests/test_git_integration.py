"""Tests for integrations/git.py"""

import pytest

from integrations.git import GitManager, GitStatus, CommitResult


class TestGitStatus:
    def test_init_repo_status(self, git_repo):
        tmp_path, repo = git_repo
        gm = GitManager(str(tmp_path))
        status = gm.get_status()
        assert isinstance(status, GitStatus)
        assert status.is_clean
        assert status.changed_files == []
        assert status.untracked_files == []

    def test_get_current_branch(self, git_repo):
        tmp_path, repo = git_repo
        # Need at least one commit for active_branch to work
        (tmp_path / "init.txt").write_text("init")
        repo.index.add(["init.txt"])
        repo.index.commit("initial")
        gm = GitManager(str(tmp_path))
        assert gm.get_current_branch() == "master"


class TestBranching:
    def test_create_and_checkout_branch(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "init.txt").write_text("init")
        repo.index.add(["init.txt"])
        repo.index.commit("initial")
        gm = GitManager(str(tmp_path))
        gm.create_branch("feature-x")
        assert gm.get_current_branch() == "feature-x"

    def test_checkout_branch(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "init.txt").write_text("init")
        repo.index.add(["init.txt"])
        repo.index.commit("initial")
        gm = GitManager(str(tmp_path))
        gm.create_branch("dev", checkout=True)
        assert gm.get_current_branch() == "dev"
        gm.checkout_branch("master")
        assert gm.get_current_branch() == "master"


class TestStagingAndCommit:
    def test_stage_and_commit(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "file.txt").write_text("hello")
        gm = GitManager(str(tmp_path))
        gm.stage_files(["file.txt"])
        result = gm.commit("Add file")
        assert isinstance(result, CommitResult)
        assert result.message == "Add file"
        assert len(result.sha) == 40

    def test_commit_result_branch(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "file.txt").write_text("hello")
        gm = GitManager(str(tmp_path))
        gm.stage_files(["file.txt"])
        result = gm.commit("init")
        gm.create_branch("feature")
        (tmp_path / "new.txt").write_text("new")
        gm.stage_files(["new.txt"])
        result = gm.commit("feature commit")
        assert result.branch == "feature"

    def test_stage_all(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        gm = GitManager(str(tmp_path))
        gm.stage_all()
        result = gm.commit("add all")
        assert result.sha


class TestDiff:
    def test_diff_unstaged(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "file.txt").write_text("line1")
        gm = GitManager(str(tmp_path))
        gm.stage_files(["file.txt"])
        gm.commit("init")
        (tmp_path / "file.txt").write_text("line1\nline2")
        diff = gm.get_diff()
        assert "line2" in diff

    def test_diff_staged(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "file.txt").write_text("v1")
        gm = GitManager(str(tmp_path))
        gm.stage_files(["file.txt"])
        gm.commit("init")
        (tmp_path / "file.txt").write_text("v2")
        gm.stage_files(["file.txt"])
        diff = gm.get_diff(staged=True)
        assert "v2" in diff


class TestRemote:
    def test_no_remote(self, git_repo):
        tmp_path, repo = git_repo
        gm = GitManager(str(tmp_path))
        assert gm.has_remote() is False

    def test_push_skips_no_remote(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "file.txt").write_text("hello")
        gm = GitManager(str(tmp_path))
        gm.stage_files(["file.txt"])
        gm.commit("init")
        # Should not raise when no remote
        gm.push()


class TestDirtyTree:
    def test_dirty_working_tree(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "file.txt").write_text("hello")
        gm = GitManager(str(tmp_path))
        gm.stage_files(["file.txt"])
        gm.commit("init")
        (tmp_path / "file.txt").write_text("modified")
        status = gm.get_status()
        assert not status.is_clean
        assert "file.txt" in status.changed_files
