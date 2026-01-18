# 3. FORGETTING GRADIENT PROTOTYPE

## Overview
Implements the memory decay system where memories gradually compress from episodic detail to semantic essence to intuitive patterns, following token economics and human forgetting curves.

---

## DECAY THEORY

### Ebbinghaus Forgetting Curve Adapted for AI

Traditional forgetting curve: `R = e^(-t/S)`

Where:
- R = retention ratio (0-1)
- t = time since learning
- S = strength of memory

For AI, we add:
- Repetition multiplier
- Success-based multiplier
- Criticality resistance
- Access-based reversal

---

## IMPLEMENTATION

```python
import math
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum

class MemoryPhase(Enum):
    """Phases of memory decay through compression."""
    EPISODIC = "episodic"          # Full detail (500 tokens)
    COMPRESSED_1 = "compressed_1"  # 70% retention (350 tokens)
    COMPRESSED_2 = "compressed_2"  # 50% retention (250 tokens)
    SEMANTIC = "semantic"           # Essence only (150 tokens)
    PATTERN = "pattern"             # Pattern only (75 tokens)
    INTUITIVE = "intuitive"         # Gut feeling (50 tokens)
    FORGOTTEN = "forgotten"         # Decayed away


@dataclass
class MemoryRecord:
    """Represents a memory at any point in its lifecycle."""
    
    memory_id: str
    agent_id: str
    content: str
    current_phase: MemoryPhase
    
    # Creation and access
    created_at: datetime
    last_accessed: datetime
    access_count: int
    
    # Strength factors
    success_score: float  # 0-1: how successful was this?
    use_count: int  # How many times successfully used?
    criticality: float  # 0-1: how important?
    repetition_count: int  # How many times seen?
    
    # Token economics
    original_tokens: int  # Episodic phase tokens
    current_tokens: int  # Current phase tokens
    
    # Decay parameters
    decay_rate: float  # % per day
    half_life_days: int  # Days to 50% strength
    last_decay_update: datetime
    
    def calculate_strength(self) -> float:
        """Current memory strength (0-1)."""
        days_elapsed = (datetime.now() - self.created_at).days
        
        # Base decay following half-life
        strength = math.pow(0.5, days_elapsed / self.half_life_days)
        
        # Success multiplier: successful memories strengthen
        success_boost = self.success_score * 0.3
        
        # Access multiplier: recently used memories strengthen
        days_since_access = (datetime.now() - self.last_accessed).days
        recency_boost = math.exp(-days_since_access / 7)  # Exponential recency decay
        
        # Repetition multiplier: repeated memories strengthen
        repetition_boost = min(0.5, self.repetition_count * 0.05)
        
        # Criticality resistance: critical memories resist decay
        criticality_resistance = 1 - (self.criticality * 0.7)  # Critical = 30% of decay
        
        # Apply multipliers
        final_strength = strength * criticality_resistance * (1 + success_boost + recency_boost + repetition_boost)
        
        return max(0, min(1, final_strength))


class DecayGradient:
    """
    Manages the progressive compression of memories through decay phases.
    """
    
    # Phase definitions: each maps to token compression ratio
    PHASE_TOKENS = {
        MemoryPhase.EPISODIC: 500,      # Full episodic memory
        MemoryPhase.COMPRESSED_1: 350,  # 70% detail
        MemoryPhase.COMPRESSED_2: 250,  # 50% detail
        MemoryPhase.SEMANTIC: 150,      # Semantic essence only
        MemoryPhase.PATTERN: 75,        # Pattern signature
        MemoryPhase.INTUITIVE: 50,      # Gut feeling only
        MemoryPhase.FORGOTTEN: 0        # Completely gone
    }
    
    # Phase transitions: when to compress
    PHASE_THRESHOLDS = {
        MemoryPhase.EPISODIC: 1.0,      # Always starts here
        MemoryPhase.COMPRESSED_1: 0.8,  # 80% strength → compress
        MemoryPhase.COMPRESSED_2: 0.6,  # 60% strength → compress more
        MemoryPhase.SEMANTIC: 0.4,      # 40% strength → just essence
        MemoryPhase.PATTERN: 0.2,       # 20% strength → just pattern
        MemoryPhase.INTUITIVE: 0.1,     # 10% strength → gut feeling
        MemoryPhase.FORGOTTEN: 0.01     # < 1% strength → forget
    }
    
    
    def __init__(self, vector_db, sql_db):
        """
        Args:
            vector_db: Weaviate/Pinecone client for embeddings
            sql_db: PostgreSQL connection for metadata
        """
        self.vector_db = vector_db
        self.sql_db = sql_db
        self.compression_strategies = {
            MemoryPhase.EPISODIC: self._compress_episodic_to_1,
            MemoryPhase.COMPRESSED_1: self._compress_1_to_2,
            MemoryPhase.COMPRESSED_2: self._compress_2_to_semantic,
            MemoryPhase.SEMANTIC: self._compress_semantic_to_pattern,
            MemoryPhase.PATTERN: self._compress_pattern_to_intuitive,
            MemoryPhase.INTUITIVE: self._compress_intuitive_to_forgotten
        }
    
    
    def update_memory_phase(self, memory: MemoryRecord) -> MemoryRecord:
        """
        Determine if memory should advance to next decay phase.
        
        Returns: Updated MemoryRecord with new phase if changed
        """
        
        strength = memory.calculate_strength()
        current_phase = memory.current_phase
        
        # Find next phase based on strength
        next_phase = self._find_next_phase(strength)
        
        if next_phase != current_phase:
            print(f"[DECAY] Memory {memory.memory_id} transitioning: {current_phase.value} → {next_phase.value}")
            
            # Compress content
            memory.content = self.compression_strategies[current_phase](memory)
            memory.current_phase = next_phase
            memory.current_tokens = self.PHASE_TOKENS[next_phase]
            memory.last_decay_update = datetime.now()
            
            # Update in database
            self._persist_memory(memory)
        
        return memory
    
    
    def _find_next_phase(self, strength: float) -> MemoryPhase:
        """Determine which phase to move to based on strength."""
        
        # Find the appropriate phase threshold
        for phase, threshold in sorted(
            self.PHASE_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if strength >= threshold:
                return phase
        
        return MemoryPhase.FORGOTTEN
    
    
    # ==================== COMPRESSION STRATEGIES ====================
    
    def _compress_episodic_to_1(self, memory: MemoryRecord) -> str:
        """
        Episodic → Compressed 1
        Remove non-essential details, keep core narrative
        
        From: "I implemented JWT auth using library X with configuration Y 
               on Tuesday at 3:45pm, took 2 hours, had one error which I fixed..."
        To:   "Implemented JWT auth successfully, took 2 hours"
        """
        
        # Use LLM to summarize
        summary = self._call_llm_summarize(
            memory.content,
            compression_ratio=0.7,
            preserve=['outcome', 'key_decision', 'time_estimate']
        )
        return summary
    
    
    def _compress_1_to_2(self, memory: MemoryRecord) -> str:
        """
        Compressed 1 → Compressed 2
        Keep only the core concept and outcome
        
        From: "Implemented JWT auth successfully, took 2 hours"
        To:   "JWT auth implementation successful"
        """
        
        summary = self._call_llm_summarize(
            memory.content,
            compression_ratio=0.5,
            preserve=['concept', 'outcome']
        )
        return summary
    
    
    def _compress_2_to_semantic(self, memory: MemoryRecord) -> str:
        """
        Compressed 2 → Semantic
        Abstract to pure semantic essence
        
        From: "JWT auth implementation successful"
        To:   "JWT authentication method"
        """
        
        # Extract semantic meaning without context
        semantic = self._extract_semantic_meaning(memory.content)
        return semantic
    
    
    def _compress_semantic_to_pattern(self, memory: MemoryRecord) -> str:
        """
        Semantic → Pattern
        Reduce to just the pattern signature
        
        From: "JWT authentication method"
        To:   "token_based_auth_method"
        """
        
        # Generate pattern signature
        pattern = self._generate_pattern_signature(memory.content)
        return pattern
    
    
    def _compress_pattern_to_intuitive(self, memory: MemoryRecord) -> str:
        """
        Pattern → Intuitive
        Convert to gut feeling/instinct
        
        From: "token_based_auth_method"
        To:   "auth_feeling: secure, reliable, standard"
        """
        
        # Generate intuitive representation
        intuition = self._generate_intuition(memory.content)
        return intuition
    
    
    def _compress_intuitive_to_forgotten(self, memory: MemoryRecord) -> str:
        """
        Intuitive → Forgotten
        Memory is essentially gone, but its pattern lives in gut agent
        """
        return "[FORGOTTEN]"
    
    
    # ==================== COMPRESSION HELPERS ====================
    
    def _call_llm_summarize(self, text: str, compression_ratio: float, 
                           preserve: List[str]) -> str:
        """
        Use Claude/GPT to intelligently compress memory.
        
        Args:
            text: Original memory content
            compression_ratio: Target compression (0.7 = keep 70%)
            preserve: Fields/concepts to definitely preserve
        """
        
        target_tokens = int(len(text.split()) * compression_ratio)
        preserve_str = ", ".join(preserve)
        
        prompt = f"""
        Compress this memory to ~{target_tokens} words while preserving: {preserve_str}
        
        Original: {text}
        
        Compressed version (max {target_tokens} words):
        """
        
        # Call Claude API (or GPT)
        # response = claude.messages.create(...)
        # return response.content[0].text
        
        # Placeholder
        return text[:len(text)//2]
    
    
    def _extract_semantic_meaning(self, text: str) -> str:
        """
        Extract just the semantic meaning without context.
        """
        
        prompt = f"""
        Extract the pure semantic meaning from this memory.
        Remove context, timestamps, and emotional coloring.
        Return a single concept or fact.
        
        Memory: {text}
        Semantic meaning:
        """
        
        # Call LLM
        # response = claude.messages.create(...)
        # return response.content[0].text
        
        return text
    
    
    def _generate_pattern_signature(self, text: str) -> str:
        """
        Generate a compact pattern signature.
        Example: "JWT auth" → "token_based_auth"
        """
        
        # Extract key concepts
        concepts = self._extract_concepts(text)
        signature = "_".join(concepts).lower()
        return signature
    
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract main concepts from text."""
        # Use NLP or simple pattern matching
        # Placeholder
        return text.split()[:3]
    
    
    def _generate_intuition(self, text: str) -> str:
        """
        Convert to intuitive/emotional representation.
        Example: "JWT auth" → "secure, reliable, standard"
        """
        
        prompt = f"""
        Convert this memory to intuitive feelings/gut reactions.
        Return 2-3 emotional adjectives that capture the essence.
        
        Memory: {text}
        Intuitive feelings:
        """
        
        # Call LLM
        # response = claude.messages.create(...)
        # return response.content[0].text
        
        return "neutral"
    
    
    def _persist_memory(self, memory: MemoryRecord):
        """Save updated memory to database."""
        
        update_query = """
        UPDATE long_term_memory
        SET 
            current_phase = %s,
            content = %s,
            current_tokens = %s,
            last_decay_update = %s
        WHERE id = %s
        """
        
        # Execute update
        # self.sql_db.execute(update_query, (...))


class TokenEconomics:
    """
    Track token savings from memory decay.
    """
    
    def __init__(self):
        self.total_tokens_saved = 0
        self.decay_events = []
    
    
    def calculate_savings(self, memory: MemoryRecord, 
                         old_phase: MemoryPhase, 
                         new_phase: MemoryPhase) -> Dict:
        """
        Calculate token savings from phase transition.
        """
        
        old_tokens = DecayGradient.PHASE_TOKENS[old_phase]
        new_tokens = DecayGradient.PHASE_TOKENS[new_phase]
        
        tokens_saved = old_tokens - new_tokens
        tokens_saved_pct = (tokens_saved / old_tokens * 100) if old_tokens > 0 else 0
        
        savings = {
            'memory_id': memory.memory_id,
            'phase_transition': f"{old_phase.value} → {new_phase.value}",
            'tokens_saved': tokens_saved,
            'tokens_saved_percent': tokens_saved_pct,
            'timestamp': datetime.now()
        }
        
        self.total_tokens_saved += tokens_saved
        self.decay_events.append(savings)
        
        return savings
    
    
    def get_token_efficiency(self) -> float:
        """
        Calculate overall token efficiency improvement.
        """
        
        if not self.decay_events:
            return 0
        
        avg_savings = sum(e['tokens_saved'] for e in self.decay_events) / len(self.decay_events)
        return avg_savings


# ==================== BATCH DECAY PROCESSOR ====================

class BatchDecayProcessor:
    """
    Processes decay for many memories efficiently.
    """
    
    def __init__(self, gradient: DecayGradient):
        self.gradient = gradient
    
    
    def process_batch_decay(self, memories: List[MemoryRecord], 
                          batch_size: int = 100) -> Dict:
        """
        Process decay for a batch of memories.
        """
        
        results = {
            'processed': 0,
            'phased_up': 0,
            'forgotten': 0,
            'total_tokens_saved': 0,
            'avg_phase_movement': 0
        }
        
        phases_moved = []
        
        for i, memory in enumerate(memories):
            old_phase = memory.current_phase
            updated_memory = self.gradient.update_memory_phase(memory)
            
            if updated_memory.current_phase != old_phase:
                results['phased_up'] += 1
                
                # Track phase movement
                old_idx = list(MemoryPhase).index(old_phase)
                new_idx = list(MemoryPhase).index(updated_memory.current_phase)
                phases_moved.append(new_idx - old_idx)
            
            if updated_memory.current_phase == MemoryPhase.FORGOTTEN:
                results['forgotten'] += 1
            
            results['processed'] += 1
            
            # Calculate token savings
            old_tokens = DecayGradient.PHASE_TOKENS[old_phase]
            new_tokens = DecayGradient.PHASE_TOKENS[updated_memory.current_phase]
            results['total_tokens_saved'] += (old_tokens - new_tokens)
        
        if phases_moved:
            results['avg_phase_movement'] = sum(phases_moved) / len(phases_moved)
        
        return results


# ==================== MONITORING & VISUALIZATION ====================

class DecayMonitor:
    """
    Monitor and visualize memory decay patterns.
    """
    
    def __init__(self, gradient: DecayGradient):
        self.gradient = gradient
    
    
    def get_phase_distribution(self, agent_id: str) -> Dict:
        """
        Get distribution of memories across phases.
        """
        
        query = """
        SELECT current_phase, COUNT(*) as count, AVG(current_tokens) as avg_tokens
        FROM long_term_memory
        WHERE agent_id = %s
        GROUP BY current_phase
        """
        
        # Execute and return results
        return {}
    
    
    def plot_decay_curve(self, memory_id: str) -> str:
        """
        Generate ASCII plot of memory strength over time.
        """
        
        points = []
        for days in range(0, 365, 30):
            date = datetime.now() - timedelta(days=days)
            # Calculate historical strength
            strength = self._calculate_historical_strength(memory_id, date)
            points.append(strength)
        
        # ASCII plot
        plot = self._ascii_plot(points)
        return plot
    
    
    def _ascii_plot(self, values: List[float]) -> str:
        """Create simple ASCII plot."""
        height = 10
        width = len(values)
        
        plot_lines = []
        for y in range(height, 0, -1):
            line = ""
            for x in range(width):
                if values[x] >= (y / height):
                    line += "█"
                else:
                    line += " "
            plot_lines.append(line)
        
        return "\n".join(plot_lines)
    
    
    def _calculate_historical_strength(self, memory_id: str, date: datetime) -> float:
        """Calculate what strength was on a given date."""
        # This would query historical data
        return 0.5


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    
    # Create a memory
    memory = MemoryRecord(
        memory_id="mem_001",
        agent_id="agent_001",
        content="I successfully implemented JWT authentication today. Took 2 hours. No errors.",
        current_phase=MemoryPhase.EPISODIC,
        created_at=datetime.now() - timedelta(days=90),
        last_accessed=datetime.now() - timedelta(days=30),
        access_count=3,
        success_score=0.95,
        use_count=3,
        criticality=0.1,
        repetition_count=1,
        original_tokens=100,
        current_tokens=100,
        decay_rate=0.01,
        half_life_days=180,
        last_decay_update=datetime.now()
    )
    
    # Calculate current strength
    print(f"Memory strength: {memory.calculate_strength():.2%}")
    
    # Process decay (would normally run periodically)
    gradient = DecayGradient(vector_db=None, sql_db=None)
    
    # Simulate multiple decay cycles
    for day in range(0, 360, 90):
        memory.last_decay_update = datetime.now() - timedelta(days=day)
        strength = memory.calculate_strength()
        phase = gradient._find_next_phase(strength)
        tokens = DecayGradient.PHASE_TOKENS[phase]
        
        print(f"Day {day:3d}: Strength {strength:.1%} → Phase: {phase.value:12s} ({tokens:3d} tokens)")
```

---

## DECAY TIMELINE EXAMPLE

For a successfully implemented feature (JWT auth):

```
Day 0:    EPISODIC (500 tokens)
          "Implemented JWT auth. 2 hours. Successful. Configuration..."
          Strength: 100%

Day 30:   EPISODIC → COMPRESSED_1 (350 tokens)
          "JWT auth implementation successful. 2 hour task"
          Strength: 90%

Day 60:   COMPRESSED_1 → COMPRESSED_2 (250 tokens)
          "JWT auth: successful implementation"
          Strength: 80%

Day 120:  COMPRESSED_2 → SEMANTIC (150 tokens)
          "JWT authentication method"
          Strength: 63%

Day 180:  SEMANTIC → PATTERN (75 tokens)
          "token_based_auth"
          Strength: 50%

Day 270:  PATTERN → INTUITIVE (50 tokens)
          "auth_feeling: secure, reliable"
          Strength: 28%

Day 365:  INTUITIVE → FORGOTTEN (0 tokens)
          "[FORGOTTEN - contribution to gut agent]"
          Strength: < 1%
```

Key insight: **The pattern lives on in the gut agent, but specific episodic details are forgotten.**

This saves ~2000 tokens per year for memories that go through full decay, while preserving the essential intuitions.

