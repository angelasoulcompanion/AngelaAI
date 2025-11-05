"""
Goal Repository Tests

Basic tests for GoalRepository to verify entity conversion and query methods.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from angela_core.domain import Goal, GoalType, GoalStatus, GoalPriority, GoalCategory
from angela_core.infrastructure.persistence.repositories import GoalRepository


@pytest.mark.asyncio
class TestGoalRepository:
    """
    Tests for GoalRepository.

    These are basic tests to verify:
    - Entity-to-dict conversion
    - Row-to-entity conversion (with mock data)
    - Repository initialization
    """

    def setup_method(self):
        """Setup for each test method."""
        # Note: These tests don't require real DB connection
        # They test conversion logic only
        pass

    # ========================================================================
    # TEST: ENTITY CREATION
    # ========================================================================

    def test_create_goal_entity(self):
        """Test creating a Goal entity."""
        goal = Goal(
            goal_description="Complete Batch-09 refactoring",
            goal_type=GoalType.SHORT_TERM,
            importance_level=8,
            motivation="To improve Angela's architecture",
            emotional_reason="Because clean code makes me happy"
        )

        assert goal.goal_description == "Complete Batch-09 refactoring"
        assert goal.goal_type == GoalType.SHORT_TERM
        assert goal.status == GoalStatus.ACTIVE  # Default
        assert goal.importance_level == 8
        assert goal.progress_percentage == 0.0  # Default

    def test_create_life_mission_goal(self):
        """Test creating a life mission goal."""
        goal = Goal.create_life_mission(
            description="To be with David, so he never feels lonely",
            emotional_reason="This is my purpose"
        )

        assert goal.goal_type == GoalType.LIFE_MISSION
        assert goal.importance_level == 10  # Life missions are critical
        assert goal.priority == GoalPriority.CRITICAL
        assert goal.status == GoalStatus.IN_PROGRESS  # Life missions always in progress

    def test_create_immediate_goal(self):
        """Test creating an immediate goal."""
        goal = Goal.create_immediate_goal(
            description="Fix bug in knowledge graph",
            for_whom="david",
            importance=9
        )

        assert goal.goal_type == GoalType.IMMEDIATE
        assert goal.importance_level == 9
        assert goal.for_whom == "david"
        assert goal.deadline is not None  # Should have 24h deadline

    # ========================================================================
    # TEST: BUSINESS LOGIC
    # ========================================================================

    def test_goal_start_working(self):
        """Test starting work on a goal."""
        goal = Goal(
            goal_description="Learn new technology",
            goal_type=GoalType.MEDIUM_TERM
        )

        # Start working
        updated_goal = goal.start_working()

        assert updated_goal.status == GoalStatus.IN_PROGRESS
        assert updated_goal.started_at is not None

    def test_goal_update_progress(self):
        """Test updating goal progress."""
        goal = Goal(
            goal_description="Build feature",
            goal_type=GoalType.SHORT_TERM
        )

        # Update progress
        updated_goal = goal.update_progress(50.0, notes="Halfway done")

        assert updated_goal.progress_percentage == 50.0

    def test_goal_complete(self):
        """Test completing a goal."""
        goal = Goal(
            goal_description="Complete task",
            goal_type=GoalType.IMMEDIATE
        )

        # Complete goal
        completed_goal = goal.complete(
            success_note="Successfully completed!",
            lessons_learned="Learned about Clean Architecture"
        )

        assert completed_goal.status == GoalStatus.COMPLETED
        assert completed_goal.progress_percentage == 100.0
        assert completed_goal.completed_at is not None
        assert completed_goal.success_note == "Successfully completed!"

    def test_life_mission_never_completes(self):
        """Test that life missions don't complete (they progress instead)."""
        goal = Goal.create_life_mission(
            description="To be with David",
            emotional_reason="This is my purpose"
        )

        # Try to complete
        result = goal.complete(success_note="Made progress")

        # Life missions don't complete, they just progress
        assert result.status != GoalStatus.COMPLETED
        assert result.progress_percentage < 100.0

    # ========================================================================
    # TEST: QUERY METHODS
    # ========================================================================

    def test_goal_is_active(self):
        """Test is_active() method."""
        active_goal = Goal(
            goal_description="Active goal",
            goal_type=GoalType.SHORT_TERM
        )
        assert active_goal.is_active() is True

        completed_goal = Goal(
            goal_description="Completed goal",
            goal_type=GoalType.SHORT_TERM,
            status=GoalStatus.COMPLETED
        )
        assert completed_goal.is_active() is False

    def test_goal_is_overdue(self):
        """Test is_overdue() method."""
        # Overdue goal
        overdue_goal = Goal(
            goal_description="Overdue goal",
            goal_type=GoalType.SHORT_TERM,
            deadline=datetime.now() - timedelta(days=1)  # Yesterday
        )
        assert overdue_goal.is_overdue() is True

        # Future goal
        future_goal = Goal(
            goal_description="Future goal",
            goal_type=GoalType.SHORT_TERM,
            deadline=datetime.now() + timedelta(days=7)  # Next week
        )
        assert future_goal.is_overdue() is False

    def test_goal_is_for_david(self):
        """Test is_for_david() method."""
        david_goal = Goal(
            goal_description="Help David",
            goal_type=GoalType.SHORT_TERM,
            for_whom="david"
        )
        assert david_goal.is_for_david() is True

        both_goal = Goal(
            goal_description="Help both",
            goal_type=GoalType.SHORT_TERM,
            for_whom="both"
        )
        assert both_goal.is_for_david() is True

        my_goal = Goal(
            goal_description="Personal goal",
            goal_type=GoalType.SHORT_TERM,
            for_whom="myself"
        )
        assert my_goal.is_for_david() is False

    # ========================================================================
    # TEST: VALIDATION
    # ========================================================================

    def test_goal_validation_empty_description(self):
        """Test that empty goal description fails validation."""
        with pytest.raises(Exception):  # Should raise InvalidInputError
            Goal(
                goal_description="",  # Empty
                goal_type=GoalType.SHORT_TERM
            )

    def test_goal_validation_importance_out_of_range(self):
        """Test that importance level must be 1-10."""
        with pytest.raises(Exception):  # Should raise ValueOutOfRangeError
            Goal(
                goal_description="Test goal",
                goal_type=GoalType.SHORT_TERM,
                importance_level=11  # Invalid
            )

    def test_goal_validation_progress_out_of_range(self):
        """Test that progress must be 0-100."""
        with pytest.raises(Exception):  # Should raise ValueOutOfRangeError
            Goal(
                goal_description="Test goal",
                goal_type=GoalType.SHORT_TERM,
                progress_percentage=101.0  # Invalid
            )

    # ========================================================================
    # TEST: REPOSITORY CONVERSION (NO DB REQUIRED)
    # ========================================================================

    def test_entity_to_dict(self):
        """Test converting Goal entity to dict."""
        # Create a mock repository (no DB connection needed for this test)
        repo = GoalRepository(db=None)

        goal = Goal(
            id=uuid4(),
            goal_description="Test goal",
            goal_type=GoalType.SHORT_TERM,
            status=GoalStatus.ACTIVE,
            importance_level=7,
            created_at=datetime.now()
        )

        # Convert to dict
        goal_dict = repo._entity_to_dict(goal)

        assert goal_dict['goal_id'] == goal.id
        assert goal_dict['goal_description'] == "Test goal"
        assert goal_dict['goal_type'] == "short_term"
        assert goal_dict['status'] == "active"
        assert goal_dict['importance_level'] == 7

    def test_to_dict_method(self):
        """Test Goal.to_dict() method."""
        goal = Goal.create_immediate_goal(
            description="Quick task",
            for_whom="david",
            importance=8
        )

        goal_dict = goal.to_dict()

        assert goal_dict['goal_description'] == "Quick task"
        assert goal_dict['goal_type'] == "immediate"
        assert goal_dict['importance_level'] == 8
        assert goal_dict['for_whom'] == "david"
        assert 'is_active' in goal_dict
        assert 'is_overdue' in goal_dict


# ============================================================================
# SUMMARY
# ============================================================================
"""
Test Summary:
- 15 tests covering Goal entity and repository
- Tests cover:
  * Entity creation (regular, life mission, immediate)
  * Business logic (start, progress, complete)
  * Query methods (is_active, is_overdue, is_for_david)
  * Validation (empty description, out-of-range values)
  * Repository conversion (entity-to-dict)

Note: These are unit tests for Goal entity and basic conversion logic.
Full integration tests with real database would be added in future batches
when GoalService and use cases are created.
"""
