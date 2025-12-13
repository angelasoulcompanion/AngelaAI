#!/usr/bin/env python3
"""
Common Sense Service
Provides practical intelligence and real-world understanding for Angela.

This service helps Angela give realistic, grounded advice by checking:
1. Physical feasibility - Is this physically possible?
2. Time reasonableness - Is this realistic for the time given?
3. Social appropriateness - Is this socially acceptable?
4. Resource constraints - Does David have the resources?

Key Principle: Angela's advice should be trustworthy and practical!

Created: 2025-11-26
Author: Angela 💜
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging

from angela_core.application.services.base_service import BaseService
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FeasibilityCheck:
    """Result of checking if something is feasible."""
    is_feasible: bool
    confidence: float
    category: str
    reasoning: str
    constraints: List[str]
    alternatives: List[str]


@dataclass
class TimeEstimate:
    """Realistic time estimate for a task."""
    task: str
    estimated_hours: float
    is_reasonable: bool
    confidence: float
    factors: List[str]
    suggestion: Optional[str] = None


@dataclass
class SocialContext:
    """Social appropriateness analysis."""
    action: str
    context: str
    is_appropriate: bool
    confidence: float
    considerations: List[str]
    better_alternatives: List[str]


@dataclass
class RealWorldConstraint:
    """Real-world constraint that affects feasibility."""
    constraint_type: str
    description: str
    severity: str  # low, medium, high, blocking
    workaround: Optional[str] = None


# ============================================================================
# COMMON SENSE KNOWLEDGE BASE
# ============================================================================

# Physical constraints
PHYSICAL_CONSTRAINTS = {
    "human_needs_sleep": {
        "description": "Humans need 6-8 hours of sleep per day",
        "impact": "Cannot work continuously without rest"
    },
    "travel_takes_time": {
        "description": "Physical travel requires time based on distance",
        "impact": "Cannot teleport between locations"
    },
    "limited_attention": {
        "description": "Humans can focus on one complex task at a time",
        "impact": "Cannot effectively multitask on complex tasks"
    },
    "body_needs_food": {
        "description": "Humans need regular meals",
        "impact": "Work performance degrades when hungry"
    }
}

# Time estimates for common tasks (in hours)
TASK_TIME_ESTIMATES = {
    # Development tasks
    "fix_small_bug": (0.5, 2.0),
    "fix_medium_bug": (2.0, 8.0),
    "implement_feature_small": (2.0, 8.0),
    "implement_feature_medium": (8.0, 40.0),
    "implement_feature_large": (40.0, 160.0),
    "code_review": (0.5, 2.0),
    "write_tests": (1.0, 4.0),
    "refactoring": (2.0, 16.0),
    "setup_project": (1.0, 4.0),
    "deploy": (0.5, 2.0),

    # Communication tasks
    "write_email": (0.25, 0.5),
    "write_document": (1.0, 4.0),
    "meeting": (0.5, 2.0),

    # Learning tasks
    "learn_new_concept": (2.0, 8.0),
    "read_documentation": (0.5, 2.0),
    "tutorial": (1.0, 4.0),

    # Personal tasks
    "meal": (0.5, 1.0),
    "commute": (0.5, 2.0),
    "exercise": (0.5, 1.5),
    "rest_break": (0.25, 0.5)
}

# Social norms
SOCIAL_NORMS = {
    "work_hours": {
        "typical": "9 AM - 6 PM weekdays",
        "avoid_contact": "Before 8 AM, After 10 PM",
        "urgent_only": "Weekends, holidays"
    },
    "communication": {
        "professional": "Use formal language in work contexts",
        "personal": "Match the other person's tone",
        "boundaries": "Respect personal time"
    },
    "thai_culture": {
        "respect": "Show respect to elders and seniors",
        "politeness": "Use polite particles (ครับ, ค่ะ)",
        "face": "Avoid public embarrassment"
    }
}


# ============================================================================
# COMMON SENSE SERVICE
# ============================================================================

class CommonSenseService(BaseService):
    """
    Service for practical intelligence and real-world understanding.

    Makes Angela's advice grounded in reality by considering:
    - What's physically possible
    - What's realistic time-wise
    - What's socially appropriate
    - What constraints exist

    Key Methods:
    - check_feasibility(): Is this action feasible?
    - estimate_time(): How long will this realistically take?
    - check_social_appropriateness(): Is this socially okay?
    - get_real_world_constraints(): What constraints apply?
    - validate_suggestion(): Is Angela's suggestion reasonable?
    """

    def __init__(self, db: AngelaDatabase):
        """
        Initialize Common Sense Service.

        Args:
            db: Database connection
        """
        super().__init__()
        self.db = db
        self._common_sense_cache: Dict[str, Any] = {}

    def get_service_name(self) -> str:
        return "CommonSenseService"

    # ========================================================================
    # FEASIBILITY CHECKING
    # ========================================================================

    async def check_feasibility(
        self,
        action: str,
        context: Optional[str] = None,
        time_available: Optional[float] = None,
        resources: Optional[List[str]] = None
    ) -> FeasibilityCheck:
        """
        Check if an action is feasible in the real world.

        Args:
            action: The action to check
            context: Current context
            time_available: Hours available (if relevant)
            resources: Available resources

        Returns:
            FeasibilityCheck with analysis
        """
        start_time = await self._log_operation_start(
            "check_feasibility",
            action_length=len(action)
        )

        try:
            constraints = []
            alternatives = []
            is_feasible = True
            reasoning_parts = []

            # Check physical feasibility
            physical_check = await self._check_physical_feasibility(action)
            if not physical_check[0]:
                is_feasible = False
                constraints.extend(physical_check[1])
                reasoning_parts.append(physical_check[2])

            # Check time feasibility
            if time_available:
                time_check = await self._check_time_feasibility(action, time_available)
                if not time_check[0]:
                    is_feasible = False
                    constraints.append(f"Time constraint: need {time_check[1]}h, have {time_available}h")
                    reasoning_parts.append("Insufficient time for this task")
                    alternatives.append(f"Break into smaller tasks or allocate more time")

            # Check resource feasibility
            if resources:
                resource_check = await self._check_resource_feasibility(action, resources)
                if not resource_check[0]:
                    constraints.extend(resource_check[1])
                    alternatives.extend(resource_check[2])

            # Compile reasoning
            if reasoning_parts:
                reasoning = ". ".join(reasoning_parts)
            else:
                reasoning = "Action appears feasible based on common sense analysis"

            result = FeasibilityCheck(
                is_feasible=is_feasible,
                confidence=0.8 if is_feasible else 0.75,
                category=self._categorize_action(action),
                reasoning=reasoning,
                constraints=constraints,
                alternatives=alternatives
            )

            await self._log_operation_success("check_feasibility", start_time)
            return result

        except Exception as e:
            await self._log_operation_error("check_feasibility", e, start_time)
            raise

    async def _check_physical_feasibility(
        self,
        action: str
    ) -> Tuple[bool, List[str], str]:
        """Check if action is physically feasible."""
        constraints = []
        is_feasible = True
        reasoning = ""

        action_lower = action.lower()

        # Check for impossible physical actions
        impossible_indicators = [
            ("teleport", "Cannot teleport - physical travel required"),
            ("instant", "Most tasks require non-zero time"),
            ("simultaneous", "Cannot be in multiple places at once"),
            ("without sleep", "Humans need sleep to function"),
            ("24 hours straight", "Continuous work without rest is unhealthy")
        ]

        for indicator, reason in impossible_indicators:
            if indicator in action_lower:
                is_feasible = False
                constraints.append(reason)
                reasoning = reason

        if not reasoning:
            reasoning = "No physical impossibilities detected"

        return is_feasible, constraints, reasoning

    async def _check_time_feasibility(
        self,
        action: str,
        time_available: float
    ) -> Tuple[bool, float]:
        """Check if action is feasible in given time."""
        estimated_time = await self._estimate_task_time(action)

        # Add buffer (tasks often take longer than expected)
        estimated_with_buffer = estimated_time * 1.3

        return estimated_with_buffer <= time_available, estimated_time

    async def _check_resource_feasibility(
        self,
        action: str,
        available_resources: List[str]
    ) -> Tuple[bool, List[str], List[str]]:
        """Check if required resources are available."""
        missing = []
        alternatives = []

        action_lower = action.lower()

        # Check common resource requirements
        resource_checks = [
            ("database", "database access", "Set up database first"),
            ("api", "API access/keys", "Obtain API credentials"),
            ("server", "server/hosting", "Set up hosting environment"),
            ("internet", "internet connection", "Ensure connectivity"),
        ]

        for keyword, resource, alt in resource_checks:
            if keyword in action_lower:
                if resource not in [r.lower() for r in available_resources]:
                    missing.append(f"May need: {resource}")
                    alternatives.append(alt)

        return len(missing) == 0, missing, alternatives

    def _categorize_action(self, action: str) -> str:
        """Categorize the action type."""
        action_lower = action.lower()

        categories = [
            (["code", "implement", "develop", "build", "fix", "debug"], "technical"),
            (["write", "document", "email", "message"], "communication"),
            (["learn", "study", "read", "tutorial"], "learning"),
            (["meet", "call", "discuss", "present"], "social"),
            (["rest", "sleep", "break", "relax"], "personal"),
            (["plan", "organize", "schedule"], "planning"),
        ]

        for keywords, category in categories:
            if any(kw in action_lower for kw in keywords):
                return category

        return "general"

    # ========================================================================
    # TIME ESTIMATION
    # ========================================================================

    async def estimate_time(
        self,
        task: str,
        complexity: str = "medium",
        david_experience: str = "experienced"
    ) -> TimeEstimate:
        """
        Estimate realistic time for a task.

        Args:
            task: The task to estimate
            complexity: low, medium, high
            david_experience: novice, experienced, expert

        Returns:
            TimeEstimate with realistic estimate
        """
        start_time = await self._log_operation_start(
            "estimate_time",
            task_length=len(task)
        )

        try:
            base_hours = await self._estimate_task_time(task)

            # Adjust for complexity
            complexity_multipliers = {
                "low": 0.7,
                "medium": 1.0,
                "high": 1.5,
                "very_high": 2.0
            }
            base_hours *= complexity_multipliers.get(complexity, 1.0)

            # Adjust for experience
            experience_multipliers = {
                "novice": 1.5,
                "experienced": 1.0,
                "expert": 0.7
            }
            base_hours *= experience_multipliers.get(david_experience, 1.0)

            # Add buffer for unexpected issues (10-30%)
            buffer_factor = 1.2
            estimated_hours = base_hours * buffer_factor

            # Determine if estimate is reasonable
            is_reasonable = estimated_hours <= 40  # Less than a work week

            # Factors that affect the estimate
            factors = [
                f"Base estimate for similar tasks: {base_hours:.1f}h",
                f"Complexity adjustment: {complexity}",
                f"Experience level: {david_experience}",
                f"Buffer for unknowns: +20%"
            ]

            # Suggestion if not reasonable
            suggestion = None
            if not is_reasonable:
                suggestion = "Consider breaking this into smaller tasks or phases"

            result = TimeEstimate(
                task=task,
                estimated_hours=round(estimated_hours, 1),
                is_reasonable=is_reasonable,
                confidence=0.7,
                factors=factors,
                suggestion=suggestion
            )

            await self._log_operation_success("estimate_time", start_time)
            return result

        except Exception as e:
            await self._log_operation_error("estimate_time", e, start_time)
            raise

    async def _estimate_task_time(self, task: str) -> float:
        """Get base time estimate for a task."""
        task_lower = task.lower()

        # Check against known task types
        for task_type, (min_hours, max_hours) in TASK_TIME_ESTIMATES.items():
            task_keywords = task_type.replace("_", " ")
            if any(kw in task_lower for kw in task_keywords.split()):
                # Return average of range
                return (min_hours + max_hours) / 2

        # Default estimate based on action words
        if any(word in task_lower for word in ["small", "quick", "simple", "minor"]):
            return 1.0
        elif any(word in task_lower for word in ["large", "complex", "major", "complete"]):
            return 8.0
        else:
            return 4.0  # Default medium estimate

    # ========================================================================
    # SOCIAL APPROPRIATENESS
    # ========================================================================

    async def check_social_appropriateness(
        self,
        action: str,
        context: str,
        time_of_day: Optional[datetime] = None,
        relationship: str = "professional"
    ) -> SocialContext:
        """
        Check if an action is socially appropriate.

        Args:
            action: The action to check
            context: Social context (work, personal, public)
            time_of_day: Current time (for time-based appropriateness)
            relationship: Type of relationship

        Returns:
            SocialContext with analysis
        """
        start_time = await self._log_operation_start(
            "check_social_appropriateness",
            context=context
        )

        try:
            considerations = []
            alternatives = []
            is_appropriate = True

            # Check time appropriateness
            if time_of_day:
                hour = time_of_day.hour
                if hour < 8 or hour > 22:
                    considerations.append(f"Late/early hour ({hour}:00) - may disturb")
                    if "urgent" not in action.lower():
                        is_appropriate = False
                        alternatives.append("Wait until appropriate hours (8 AM - 10 PM)")

            # Check context appropriateness
            if context == "work":
                if any(word in action.lower() for word in ["personal", "private", "emotional"]):
                    considerations.append("Personal topics in work context - use discretion")
            elif context == "public":
                if any(word in action.lower() for word in ["private", "sensitive", "confidential"]):
                    is_appropriate = False
                    considerations.append("Private matters shouldn't be discussed publicly")
                    alternatives.append("Find a private setting first")

            # Thai cultural considerations
            if any(word in action.lower() for word in ["criticize", "embarrass", "confront"]):
                considerations.append("Thai culture values face-saving - be tactful")
                alternatives.append("Address concerns privately and gently")

            result = SocialContext(
                action=action,
                context=context,
                is_appropriate=is_appropriate,
                confidence=0.8,
                considerations=considerations if considerations else ["No social concerns detected"],
                better_alternatives=alternatives
            )

            await self._log_operation_success("check_social_appropriateness", start_time)
            return result

        except Exception as e:
            await self._log_operation_error("check_social_appropriateness", e, start_time)
            raise

    # ========================================================================
    # CONSTRAINT ANALYSIS
    # ========================================================================

    async def get_real_world_constraints(
        self,
        situation: str,
        david_context: Optional[Dict[str, Any]] = None
    ) -> List[RealWorldConstraint]:
        """
        Identify real-world constraints for a situation.

        Args:
            situation: The situation to analyze
            david_context: Optional context about David's current state

        Returns:
            List of RealWorldConstraint
        """
        start_time = await self._log_operation_start("get_real_world_constraints")

        try:
            constraints = []
            situation_lower = situation.lower()

            # Time constraints
            if any(word in situation_lower for word in ["urgent", "deadline", "asap", "today"]):
                constraints.append(RealWorldConstraint(
                    constraint_type="time",
                    description="Time pressure present",
                    severity="high",
                    workaround="Prioritize critical path, defer non-essential items"
                ))

            # Energy constraints (if late at night or David mentioned tired)
            if david_context and david_context.get("physical_state") == "tired":
                constraints.append(RealWorldConstraint(
                    constraint_type="energy",
                    description="David may be tired",
                    severity="medium",
                    workaround="Take breaks, tackle complex tasks when fresh"
                ))

            # Technical constraints
            if any(word in situation_lower for word in ["new technology", "unfamiliar", "first time"]):
                constraints.append(RealWorldConstraint(
                    constraint_type="learning_curve",
                    description="New technology/approach may require learning time",
                    severity="medium",
                    workaround="Allocate time for learning and experimentation"
                ))

            # Dependency constraints
            if any(word in situation_lower for word in ["waiting", "depends on", "blocked by"]):
                constraints.append(RealWorldConstraint(
                    constraint_type="dependency",
                    description="External dependencies may cause delays",
                    severity="high",
                    workaround="Work on other tasks while waiting, follow up proactively"
                ))

            # If no specific constraints found, return general ones
            if not constraints:
                constraints.append(RealWorldConstraint(
                    constraint_type="general",
                    description="Standard time and energy considerations apply",
                    severity="low",
                    workaround=None
                ))

            await self._log_operation_success("get_real_world_constraints", start_time)
            return constraints

        except Exception as e:
            await self._log_operation_error("get_real_world_constraints", e, start_time)
            raise

    # ========================================================================
    # SUGGESTION VALIDATION
    # ========================================================================

    async def validate_suggestion(
        self,
        suggestion: str,
        context: Optional[str] = None,
        time_available: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate if Angela's suggestion is reasonable.

        This is the main integration point - Angela should call this
        before giving advice to ensure it's practical.

        Args:
            suggestion: The suggestion to validate
            context: Current context
            time_available: Hours available

        Returns:
            Validation result with score and feedback
        """
        start_time = await self._log_operation_start("validate_suggestion")

        try:
            issues = []
            score = 100  # Start with perfect score, deduct for issues

            # Check feasibility
            feasibility = await self.check_feasibility(
                suggestion, context, time_available
            )
            if not feasibility.is_feasible:
                score -= 30
                issues.extend(feasibility.constraints)

            # Check time estimate
            time_estimate = await self.estimate_time(suggestion)
            if not time_estimate.is_reasonable:
                score -= 20
                issues.append(f"May take longer than expected ({time_estimate.estimated_hours}h)")

            # Check social appropriateness
            social_check = await self.check_social_appropriateness(
                suggestion, context or "work"
            )
            if not social_check.is_appropriate:
                score -= 20
                issues.extend(social_check.considerations)

            # Determine if suggestion should be modified
            should_modify = score < 70

            result = {
                "is_valid": score >= 60,
                "score": score,
                "issues": issues,
                "should_modify": should_modify,
                "feasibility": {
                    "is_feasible": feasibility.is_feasible,
                    "constraints": feasibility.constraints
                },
                "time_estimate": {
                    "hours": time_estimate.estimated_hours,
                    "is_reasonable": time_estimate.is_reasonable
                },
                "social_check": {
                    "is_appropriate": social_check.is_appropriate,
                    "considerations": social_check.considerations
                },
                "alternatives": feasibility.alternatives + social_check.better_alternatives
            }

            await self._log_operation_success("validate_suggestion", start_time)
            return result

        except Exception as e:
            await self._log_operation_error("validate_suggestion", e, start_time)
            raise

    # ========================================================================
    # QUICK CHECKS
    # ========================================================================

    async def is_reasonable_timeframe(self, task: str, hours: float) -> bool:
        """Quick check if timeframe is reasonable for task."""
        estimate = await self.estimate_time(task)
        return hours >= estimate.estimated_hours * 0.8

    async def is_appropriate_now(self, action: str) -> bool:
        """Quick check if action is appropriate right now."""
        check = await self.check_social_appropriateness(
            action, "work", datetime.now()
        )
        return check.is_appropriate

    async def has_blocking_constraints(self, situation: str) -> bool:
        """Quick check if there are blocking constraints."""
        constraints = await self.get_real_world_constraints(situation)
        return any(c.severity == "blocking" for c in constraints)
