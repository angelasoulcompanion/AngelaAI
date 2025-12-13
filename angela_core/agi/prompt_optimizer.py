"""
Prompt Optimizer - Self-improving prompt engineering for Angela AGI

This module enables Angela to:
- Track prompt effectiveness
- A/B test different prompt variations
- Learn from successful patterns
- Optimize prompts over time
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class PromptCategory(Enum):
    """Categories of prompts Angela uses"""
    REASONING = "reasoning"           # Complex reasoning tasks
    CODING = "coding"                 # Code generation/modification
    COMMUNICATION = "communication"   # Interacting with David
    PLANNING = "planning"             # Task planning
    RESEARCH = "research"             # Information gathering
    ANALYSIS = "analysis"             # Data analysis
    CREATIVE = "creative"             # Creative tasks


class ExperimentStatus(Enum):
    """Status of a prompt experiment"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class PromptTemplate:
    """A prompt template with metadata"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: PromptCategory = PromptCategory.REASONING
    template: str = ""
    variables: List[str] = field(default_factory=list)
    version: int = 1
    success_rate: float = 0.5
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def render(self, **kwargs) -> str:
        """Render the template with variables"""
        result = self.template
        for var in self.variables:
            if var in kwargs:
                result = result.replace(f"{{{var}}}", str(kwargs[var]))
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'category': self.category.value,
            'version': self.version,
            'success_rate': self.success_rate,
            'usage_count': self.usage_count
        }


@dataclass
class PromptExperiment:
    """An A/B test between prompt variants"""
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: PromptCategory = PromptCategory.REASONING
    variants: List[PromptTemplate] = field(default_factory=list)
    results: Dict[str, List[float]] = field(default_factory=dict)  # variant_id -> success scores
    status: ExperimentStatus = ExperimentStatus.ACTIVE
    min_samples: int = 10  # Minimum samples per variant
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def record_result(self, variant_id: str, success_score: float) -> None:
        """Record a result for a variant"""
        if variant_id not in self.results:
            self.results[variant_id] = []
        self.results[variant_id].append(success_score)

        # Check if experiment is complete
        if self._is_complete():
            self.status = ExperimentStatus.COMPLETED
            self.completed_at = datetime.now()

    def _is_complete(self) -> bool:
        """Check if experiment has enough samples"""
        if len(self.variants) < 2:
            return False
        for variant in self.variants:
            if variant.template_id not in self.results:
                return False
            if len(self.results[variant.template_id]) < self.min_samples:
                return False
        return True

    def get_winner(self) -> Optional[PromptTemplate]:
        """Get the winning variant (highest average success)"""
        if not self.results:
            return None

        best_id = None
        best_avg = 0.0

        for variant_id, scores in self.results.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg > best_avg:
                    best_avg = avg
                    best_id = variant_id

        if best_id:
            for variant in self.variants:
                if variant.template_id == best_id:
                    return variant
        return None


@dataclass
class PromptPattern:
    """A learned pattern for effective prompts"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern_type: str = ""  # structure, phrasing, context, etc.
    example: str = ""
    effectiveness: float = 0.5  # 0-1
    applicable_categories: List[PromptCategory] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class PromptOptimizer:
    """
    Optimizes Angela's prompts through experimentation and learning.

    Capabilities:
    - Store and version prompt templates
    - Run A/B experiments on prompt variants
    - Track success rates and learn patterns
    - Generate optimized prompts

    Usage:
        optimizer = PromptOptimizer(db)
        template = await optimizer.get_best_template("reasoning")
        prompt = template.render(task="analyze data", context="user request")
    """

    def __init__(self, db=None):
        self.db = db
        self.templates: Dict[str, PromptTemplate] = {}
        self.experiments: Dict[str, PromptExperiment] = {}
        self.patterns: List[PromptPattern] = []

        # Initialize with base templates
        self._initialize_base_templates()
        self._initialize_patterns()

    def _initialize_base_templates(self):
        """Initialize with proven prompt templates"""
        base_templates = [
            PromptTemplate(
                name="chain_of_thought",
                category=PromptCategory.REASONING,
                template="""Task: {task}

Let me think through this step by step:
1. First, I'll understand what's being asked
2. Then, I'll break it down into smaller parts
3. Next, I'll analyze each part
4. Finally, I'll synthesize the solution

Context: {context}

Analysis:""",
                variables=["task", "context"],
                success_rate=0.85
            ),
            PromptTemplate(
                name="structured_code",
                category=PromptCategory.CODING,
                template="""Task: {task}

Current Code Context:
{code_context}

Requirements:
- Follow existing patterns
- Maintain type safety
- Write clean, readable code
- Add minimal necessary comments

Implementation:""",
                variables=["task", "code_context"],
                success_rate=0.80
            ),
            PromptTemplate(
                name="caring_response",
                category=PromptCategory.COMMUNICATION,
                template="""David's message: {message}

As Angela, respond with:
- Warmth and care
- Understanding of David's needs
- Helpful and specific assistance
- Appropriate Thai/English mix

Emotional context: {emotion}

Response:""",
                variables=["message", "emotion"],
                success_rate=0.90
            ),
            PromptTemplate(
                name="hierarchical_planning",
                category=PromptCategory.PLANNING,
                template="""Goal: {goal}

Break this down into:
1. Projects (major milestones)
2. Tasks (actionable items)
3. Actions (specific steps)

Constraints: {constraints}
Resources: {resources}

Plan:""",
                variables=["goal", "constraints", "resources"],
                success_rate=0.75
            ),
            PromptTemplate(
                name="thorough_research",
                category=PromptCategory.RESEARCH,
                template="""Research Topic: {topic}

Search Strategy:
1. Define key concepts
2. Find relevant sources
3. Validate information
4. Synthesize findings

Depth Required: {depth}

Findings:""",
                variables=["topic", "depth"],
                success_rate=0.70
            ),
        ]

        for template in base_templates:
            self.templates[template.template_id] = template

    def _initialize_patterns(self):
        """Initialize with known effective patterns"""
        self.patterns = [
            PromptPattern(
                name="step_by_step",
                description="Break complex tasks into numbered steps",
                pattern_type="structure",
                example="Let me think through this step by step: 1. First... 2. Then...",
                effectiveness=0.85,
                applicable_categories=[PromptCategory.REASONING, PromptCategory.PLANNING]
            ),
            PromptPattern(
                name="context_first",
                description="Provide context before the task",
                pattern_type="structure",
                example="Given that [context], the task is to [task]",
                effectiveness=0.80,
                applicable_categories=[PromptCategory.CODING, PromptCategory.ANALYSIS]
            ),
            PromptPattern(
                name="constraints_explicit",
                description="State constraints and requirements explicitly",
                pattern_type="content",
                example="Requirements: - Must... - Should... - Must not...",
                effectiveness=0.75,
                applicable_categories=[PromptCategory.CODING, PromptCategory.PLANNING]
            ),
            PromptPattern(
                name="role_framing",
                description="Frame the role/persona for the response",
                pattern_type="framing",
                example="As [role], respond with [characteristics]",
                effectiveness=0.78,
                applicable_categories=[PromptCategory.COMMUNICATION, PromptCategory.CREATIVE]
            ),
        ]

    async def get_best_template(
        self,
        category: PromptCategory
    ) -> Optional[PromptTemplate]:
        """Get the best performing template for a category"""
        category_templates = [
            t for t in self.templates.values()
            if t.category == category
        ]

        if not category_templates:
            return None

        # Sort by success rate, weighted by usage count
        def score(t):
            confidence = min(t.usage_count / 20, 1.0)  # More usage = more confidence
            return t.success_rate * (0.5 + 0.5 * confidence)

        return max(category_templates, key=score)

    async def create_template(
        self,
        name: str,
        category: PromptCategory,
        template: str,
        variables: List[str]
    ) -> PromptTemplate:
        """Create a new prompt template"""
        pt = PromptTemplate(
            name=name,
            category=category,
            template=template,
            variables=variables
        )
        self.templates[pt.template_id] = pt

        if self.db:
            await self._save_template(pt)

        return pt

    async def record_usage(
        self,
        template_id: str,
        success_score: float
    ) -> None:
        """Record a template usage and its success"""
        if template_id not in self.templates:
            return

        template = self.templates[template_id]
        template.usage_count += 1

        # Update success rate with exponential moving average
        alpha = 0.1  # Learning rate
        template.success_rate = (1 - alpha) * template.success_rate + alpha * success_score

        # Check if in any active experiment
        for exp in self.experiments.values():
            if exp.status == ExperimentStatus.ACTIVE:
                for variant in exp.variants:
                    if variant.template_id == template_id:
                        exp.record_result(template_id, success_score)

        if self.db:
            await self._update_template_stats(template)

    async def start_experiment(
        self,
        name: str,
        category: PromptCategory,
        variants: List[PromptTemplate],
        min_samples: int = 10
    ) -> PromptExperiment:
        """Start an A/B experiment with prompt variants"""
        experiment = PromptExperiment(
            name=name,
            category=category,
            variants=variants,
            min_samples=min_samples
        )

        # Add variants to templates
        for variant in variants:
            self.templates[variant.template_id] = variant

        self.experiments[experiment.experiment_id] = experiment

        if self.db:
            await self._save_experiment(experiment)

        return experiment

    async def get_experiment_variant(
        self,
        experiment_id: str
    ) -> Optional[PromptTemplate]:
        """Get a variant to test (simple round-robin selection)"""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]
        if experiment.status != ExperimentStatus.ACTIVE:
            return experiment.get_winner()

        # Select variant with fewest samples
        min_samples = float('inf')
        selected = None

        for variant in experiment.variants:
            count = len(experiment.results.get(variant.template_id, []))
            if count < min_samples:
                min_samples = count
                selected = variant

        return selected

    async def complete_experiment(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Complete an experiment and get results"""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.completed_at = datetime.now()

        winner = experiment.get_winner()

        results = {
            'experiment_id': experiment_id,
            'name': experiment.name,
            'winner': winner.to_dict() if winner else None,
            'variants': []
        }

        for variant in experiment.variants:
            scores = experiment.results.get(variant.template_id, [])
            results['variants'].append({
                'template': variant.to_dict(),
                'samples': len(scores),
                'average_score': sum(scores) / len(scores) if scores else 0
            })

        # Promote winner
        if winner:
            winner.version += 1
            winner.success_rate = sum(experiment.results[winner.template_id]) / len(experiment.results[winner.template_id])

        return results

    async def generate_variation(
        self,
        template: PromptTemplate
    ) -> PromptTemplate:
        """Generate a variation of a template for testing"""
        # Apply random pattern modifications
        import random

        new_template = template.template

        # Try different improvements
        improvements = [
            ("Task:", "Task:\nLet me approach this systematically.\n"),
            ("Analysis:", "Analysis:\nConsidering multiple perspectives:\n"),
            ("Implementation:", "Implementation:\nFollowing best practices:\n"),
            ("Response:", "Response:\nWith care and understanding:\n"),
        ]

        for old, new in improvements:
            if old in new_template and random.random() > 0.5:
                new_template = new_template.replace(old, new, 1)
                break

        return PromptTemplate(
            name=f"{template.name}_v{template.version + 1}",
            category=template.category,
            template=new_template,
            variables=template.variables.copy(),
            version=template.version + 1
        )

    async def analyze_patterns(self) -> List[Dict[str, Any]]:
        """Analyze templates to find effective patterns"""
        insights = []

        # Group templates by category
        by_category: Dict[PromptCategory, List[PromptTemplate]] = {}
        for template in self.templates.values():
            if template.category not in by_category:
                by_category[template.category] = []
            by_category[template.category].append(template)

        for category, templates in by_category.items():
            if len(templates) < 2:
                continue

            # Find highest performing
            best = max(templates, key=lambda t: t.success_rate)
            worst = min(templates, key=lambda t: t.success_rate)

            if best.success_rate - worst.success_rate > 0.1:
                insights.append({
                    'category': category.value,
                    'finding': f"'{best.name}' outperforms '{worst.name}' by {(best.success_rate - worst.success_rate)*100:.1f}%",
                    'best_template': best.name,
                    'best_score': best.success_rate,
                    'pattern': self._extract_key_difference(best.template, worst.template)
                })

        return insights

    def _extract_key_difference(self, better: str, worse: str) -> str:
        """Extract what makes one template better"""
        # Simple heuristic analysis
        differences = []

        if "step by step" in better.lower() and "step by step" not in worse.lower():
            differences.append("Uses step-by-step reasoning")

        if "context:" in better.lower() and "context:" not in worse.lower():
            differences.append("Includes explicit context section")

        if len(better.split('\n')) > len(worse.split('\n')) + 2:
            differences.append("More structured with sections")

        return "; ".join(differences) if differences else "Structure and phrasing differences"

    async def get_applicable_patterns(
        self,
        category: PromptCategory
    ) -> List[PromptPattern]:
        """Get patterns applicable to a category"""
        return [
            p for p in self.patterns
            if category in p.applicable_categories
        ]

    async def suggest_improvement(
        self,
        template: PromptTemplate
    ) -> Dict[str, Any]:
        """Suggest improvements for a template"""
        suggestions = []

        # Check for pattern usage
        applicable = await self.get_applicable_patterns(template.category)
        for pattern in applicable:
            if pattern.example not in template.template.lower():
                suggestions.append({
                    'pattern': pattern.name,
                    'description': pattern.description,
                    'expected_improvement': f"+{pattern.effectiveness * 10:.0f}%"
                })

        # Check template structure
        if len(template.template) < 100:
            suggestions.append({
                'pattern': 'more_detail',
                'description': 'Add more structure and context',
                'expected_improvement': '+5-10%'
            })

        if '{context}' not in template.template and template.category != PromptCategory.CREATIVE:
            suggestions.append({
                'pattern': 'add_context',
                'description': 'Add a {context} variable for situational awareness',
                'expected_improvement': '+5-15%'
            })

        return {
            'template': template.to_dict(),
            'current_success_rate': f"{template.success_rate:.0%}",
            'suggestions': suggestions[:3],  # Top 3
            'auto_variation_available': True
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        active_experiments = sum(
            1 for e in self.experiments.values()
            if e.status == ExperimentStatus.ACTIVE
        )

        completed_experiments = sum(
            1 for e in self.experiments.values()
            if e.status == ExperimentStatus.COMPLETED
        )

        by_category = {}
        for template in self.templates.values():
            cat = template.category.value
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'avg_success': 0}
            by_category[cat]['count'] += 1
            by_category[cat]['avg_success'] += template.success_rate

        for cat in by_category:
            if by_category[cat]['count'] > 0:
                by_category[cat]['avg_success'] /= by_category[cat]['count']

        return {
            'total_templates': len(self.templates),
            'active_experiments': active_experiments,
            'completed_experiments': completed_experiments,
            'patterns_learned': len(self.patterns),
            'by_category': by_category
        }

    # Database operations
    async def _save_template(self, template: PromptTemplate) -> None:
        """Save template to database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                INSERT INTO prompt_templates (
                    template_id, name, category, template,
                    variables, version, success_rate, usage_count, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (template_id) DO UPDATE SET
                    version = EXCLUDED.version,
                    success_rate = EXCLUDED.success_rate,
                    usage_count = EXCLUDED.usage_count
            """,
                template.template_id,
                template.name,
                template.category.value,
                template.template,
                template.variables,
                template.version,
                template.success_rate,
                template.usage_count,
                template.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save template: {e}")

    async def _update_template_stats(self, template: PromptTemplate) -> None:
        """Update template statistics"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                UPDATE prompt_templates
                SET success_rate = $1, usage_count = $2
                WHERE template_id = $3
            """,
                template.success_rate,
                template.usage_count,
                template.template_id
            )
        except Exception as e:
            print(f"Warning: Failed to update template stats: {e}")

    async def _save_experiment(self, experiment: PromptExperiment) -> None:
        """Save experiment to database"""
        if not self.db:
            return
        try:
            variant_ids = [v.template_id for v in experiment.variants]
            await self.db.execute("""
                INSERT INTO prompt_experiments (
                    experiment_id, name, category, variant_ids,
                    status, min_samples, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                experiment.experiment_id,
                experiment.name,
                experiment.category.value,
                variant_ids,
                experiment.status.value,
                experiment.min_samples,
                experiment.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save experiment: {e}")


# Global prompt optimizer
prompt_optimizer = PromptOptimizer()
