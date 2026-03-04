"""Tests for SafetyManager and Checkpoint."""

from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from agent.safety import Checkpoint, SafetyManager, ValidationResult, ValidationCheck
from code_engine.generator import GenerationPlan, GenerationResult, FileChange, CodeGenerator


class TestCheckpoint:
    def test_fields(self):
        cp = Checkpoint(branch="main", sha="abc123", description="test")
        assert cp.branch == "main"
        assert cp.sha == "abc123"
        assert cp.description == "test"
        assert cp.timestamp != ""

    def test_auto_timestamp(self):
        cp = Checkpoint(branch="main", sha="abc123")
        assert cp.timestamp  # auto-filled


class TestSafetyManager:
    def test_init_creates_git_manager(self, safety_manager):
        assert safety_manager.git is not None
        assert safety_manager.repo_path is not None

    def test_create_checkpoint(self, safety_manager):
        cp = safety_manager.create_checkpoint("test checkpoint")
        assert cp.branch is not None
        assert len(cp.sha) == 40  # full hex sha
        assert cp.description == "test checkpoint"
        assert cp.timestamp != ""

    def test_get_checkpoints(self, safety_manager):
        assert safety_manager.get_checkpoints() == []
        safety_manager.create_checkpoint("cp1")
        safety_manager.create_checkpoint("cp2")
        cps = safety_manager.get_checkpoints()
        assert len(cps) == 2
        assert cps[0].description == "cp1"
        assert cps[1].description == "cp2"

    def test_rollback_restores_state(self, safety_manager):
        import os
        # Create checkpoint
        cp = safety_manager.create_checkpoint("before change")

        # Make a change and commit
        test_file = os.path.join(safety_manager.repo_path, "new_file.txt")
        with open(test_file, "w") as f:
            f.write("new content")
        safety_manager.git.stage_all()
        safety_manager.git.commit("add file")

        assert os.path.exists(test_file)

        # Rollback
        safety_manager.rollback(cp)
        assert not os.path.exists(test_file)

    def test_ensure_feature_branch_creates_branch(self, safety_manager):
        current = safety_manager.git.get_current_branch()
        # We're on master/main from init — create feature branch
        safety_manager.ensure_feature_branch("feature-test")
        assert safety_manager.git.get_current_branch() == "feature-test"

    def test_ensure_feature_branch_refuses_main(self, safety_manager):
        with pytest.raises(ValueError, match="Refusing"):
            safety_manager.ensure_feature_branch("main")

    def test_ensure_feature_branch_refuses_master(self, safety_manager):
        # Rename to master to test
        safety_manager.git.repo.git.branch("-m", "master")
        with pytest.raises(ValueError, match="Refusing"):
            safety_manager.ensure_feature_branch("master")

    @pytest.mark.asyncio
    async def test_safe_apply_success(self, safety_manager):
        plan = GenerationPlan(task="test task", changes=[], summary="no changes")
        generator = MagicMock(spec=CodeGenerator)
        generator.apply_plan.return_value = GenerationResult(plan=plan, success=True)

        result = await safety_manager.safe_apply(
            generator, plan, safety_manager.repo_path, validate=False
        )
        assert result.success is True
        generator.apply_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_apply_rollback_on_apply_failure(self, safety_manager):
        plan = GenerationPlan(task="bad task", changes=[], summary="fail")
        generator = MagicMock(spec=CodeGenerator)
        generator.apply_plan.return_value = GenerationResult(
            plan=plan, success=False, error="Write error"
        )

        initial_sha = safety_manager.git.repo.head.commit.hexsha
        result = await safety_manager.safe_apply(
            generator, plan, safety_manager.repo_path, validate=False
        )
        assert result.success is False
        assert "Write error" in result.error
        # Should have rolled back
        assert safety_manager.git.repo.head.commit.hexsha == initial_sha

    @pytest.mark.asyncio
    async def test_safe_apply_rollback_on_validation_failure(self, safety_manager):
        import os

        # Create a pyproject.toml so detect_checks finds something
        pyproject = os.path.join(safety_manager.repo_path, "pyproject.toml")
        with open(pyproject, "w") as f:
            f.write("[tool.pytest]\n")
        safety_manager.git.stage_all()
        safety_manager.git.commit("add pyproject")

        plan = GenerationPlan(
            task="add feature",
            changes=[FileChange(file_path="feat.py", action="create", content="x=1")],
            summary="add feat",
        )
        generator = MagicMock(spec=CodeGenerator)
        generator.apply_plan.return_value = GenerationResult(plan=plan, success=True)

        # Mock validation to fail
        mock_val_result = ValidationResult(checks=[
            ValidationCheck(name="test", command=["pytest"], passed=False, output="FAILED")
        ])
        with patch("agent.safety.ValidationRunner.run_all", return_value=mock_val_result):
            with patch("agent.safety.ValidationRunner.detect_checks", return_value=[("test", ["pytest"])]):
                result = await safety_manager.safe_apply(
                    generator, plan, safety_manager.repo_path, validate=True
                )

        assert result.success is False
        assert "Validation failed" in result.error
