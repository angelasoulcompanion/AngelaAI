# 2. ANALYTICS AGENT ALGORITHM: INTELLIGENT MEMORY ROUTING

## Overview
The Analytics Agent is the intelligence layer between fresh memory and long-term storage. It decides where each memory should be routed based on success patterns, repetition, criticality, and emergent patterns.

---

## ANALYTICS AGENT ARCHITECTURE

```
                    New Memory Event
                           ↓
                    ┌──────────────┐
                    │ ANALYTICS    │
                    │ AGENT        │
                    └──────────────┘
                    /      |      \
         ┌──────────┐  ┌────────┐  ┌──────────┐
         ↓          ↓  ↓        ↓  ↓          ↓
      Relevance  Success  Pattern  Criticality Decay
      Analyzer   Tracker  Detector  Detector   Manager
         │          │        │         │        │
         └──────────┴────────┴─────────┴────────┘
                           ↓
                    Routing Decision
                    ├─ LONG-TERM
                    ├─ PROCEDURAL
                    ├─ SHOCK
                    ├─ GUT PATTERN
                    └─ DECAY
```

---

## CORE ROUTING ALGORITHM

```python
class AnalyticsAgent:
    """
    Intelligent memory router that decides where to store memories
    based on multiple signals.
    """
    
    def __init__(self):
        self.weights = {
            'success_score': 0.35,
            'repetition_signal': 0.25,
            'criticality': 0.20,
            'pattern_novelty': 0.15,
            'context_richness': 0.05
        }
        self.routing_thresholds = {
            'long_term': 0.70,
            'procedural': 0.60,  # Requires high success rate
            'shock': 0.85,  # Criticality threshold
            'gut_pattern': 0.50
        }
    
    def analyze_memory(self, fresh_memory_event):
        """
        Main routing decision function.
        
        Returns:
            {
                'target_tier': str,
                'confidence': float (0-1),
                'reasoning': dict,
                'alternative_routes': list
            }
        """
        
        # Extract signals from the event
        signals = self._extract_signals(fresh_memory_event)
        
        # Calculate routing scores
        scores = self._calculate_scores(signals)
        
        # Determine primary and alternative routes
        routing_decision = self._determine_route(scores)
        
        # Record decision for future learning
        self._record_routing_decision(fresh_memory_event, routing_decision)
        
        return routing_decision
    
    
    # ==================== SIGNAL EXTRACTION ====================
    
    def _extract_signals(self, event):
        """
        Extract meaningful signals from the raw memory event.
        
        Signals:
        - success_score: Did this work? (0-1)
        - repetition_count: How many times seen? (0-N)
        - criticality: How important/dangerous? (0-1)
        - pattern_novelty: Is this a new pattern? (0-1)
        - context_richness: How much context? (0-1)
        """
        
        return {
            'success_score': self._calculate_success_score(event),
            'repetition_count': self._detect_repetition(event),
            'repetition_signal': self._normalize_repetition(event),
            'criticality': self._assess_criticality(event),
            'pattern_novelty': self._detect_pattern_novelty(event),
            'context_richness': self._assess_context_richness(event),
            'emotional_intensity': self._assess_emotional_intensity(event),
            'temporal_urgency': self._assess_temporal_urgency(event)
        }
    
    
    def _calculate_success_score(self, event):
        """
        Determine if this experience was successful (0-1).
        
        High success = worth storing in long-term
        Low success = may not be worth keeping
        """
        
        success_indicators = {
            'outcome': event.get('outcome'),  # 'success', 'failure', 'partial'
            'error_rate': event.get('error_rate', 0),
            'execution_time': event.get('execution_time_ms'),
            'efficiency': event.get('efficiency_rating'),
            'user_satisfaction': event.get('user_satisfaction', 0.5),
            'performance_vs_baseline': event.get('performance_vs_baseline', 1.0)
        }
        
        # Outcome mapping
        outcome_scores = {
            'success': 0.95,
            'partial': 0.55,
            'failure': 0.05
        }
        base_score = outcome_scores.get(success_indicators['outcome'], 0.5)
        
        # Adjust by error rate
        error_penalty = success_indicators['error_rate'] * 0.3
        
        # Adjust by efficiency (if too slow, lower score)
        if success_indicators['execution_time']:
            if success_indicators['execution_time'] > 5000:  # > 5 seconds
                efficiency_penalty = min(0.2, 
                    (success_indicators['execution_time'] - 5000) / 10000)
            else:
                efficiency_penalty = 0
        else:
            efficiency_penalty = 0
        
        # User satisfaction weight
        satisfaction_bonus = success_indicators['user_satisfaction'] * 0.1
        
        # Performance vs baseline
        if success_indicators['performance_vs_baseline'] > 1.0:
            performance_bonus = min(0.15, 
                (success_indicators['performance_vs_baseline'] - 1.0) * 0.1)
        else:
            performance_bonus = 0
        
        final_score = max(0, min(1, 
            base_score 
            - error_penalty 
            - efficiency_penalty 
            + satisfaction_bonus 
            + performance_bonus
        ))
        
        return final_score
    
    
    def _detect_repetition(self, event):
        """
        How many times have we seen this pattern before?
        
        Returns: count of similar events in recent memory
        """
        
        # Generate a pattern signature from the event
        pattern_signature = self._generate_signature(event)
        
        # Query recent memory for similar patterns
        similar_count = self._query_similar_patterns(pattern_signature)
        
        return similar_count
    
    
    def _normalize_repetition(self, event):
        """
        Convert repetition count to a 0-1 signal.
        
        More repetitions = stronger signal to consolidate into habit
        """
        
        repetition_count = self._detect_repetition(event)
        
        # Sigmoid curve: 5 repetitions = 0.5, 10+ = 0.95
        repetition_signal = 1 / (1 + math.exp(-0.5 * (repetition_count - 5)))
        
        return repetition_signal
    
    
    def _assess_criticality(self, event):
        """
        How critical/important is this event?
        
        Criticality matrix:
        - Security issues: 0.95+
        - Data loss/corruption: 0.90+
        - Service outage: 0.85+
        - Performance degradation: 0.60+
        - Normal operations: 0.20+
        """
        
        event_type = event.get('event_type', 'normal')
        severity = event.get('severity', 0)
        impact_scope = event.get('impact_scope', 'local')  # local, user, system, all
        
        # Base criticality by type
        type_criticality = {
            'security_breach': 0.95,
            'unauthorized_access': 0.93,
            'data_corruption': 0.90,
            'service_outage': 0.85,
            'cascade_failure': 0.87,
            'resource_exhaustion': 0.75,
            'performance_degradation': 0.50,
            'warning': 0.35,
            'info': 0.15,
            'normal': 0.10
        }
        
        base_criticality = type_criticality.get(event_type, 0.10)
        
        # Adjust by severity
        severity_adjustment = (severity - 0.5) * 0.2  # ±10%
        
        # Adjust by impact scope
        scope_multiplier = {
            'local': 0.5,
            'user': 0.7,
            'system': 0.9,
            'all': 1.0
        }
        
        final_criticality = max(0, min(1, 
            (base_criticality + severity_adjustment) * scope_multiplier.get(impact_scope, 1.0)
        ))
        
        return final_criticality
    
    
    def _detect_pattern_novelty(self, event):
        """
        Is this a new, unseen pattern (0-1)?
        
        Novel patterns are interesting for the gut agent
        Familiar patterns consolidate into habits
        """
        
        event_signature = self._generate_signature(event)
        
        # Query for similar patterns
        similar_memories = self._query_vector_db(
            embedding=event.get('embedding'),
            top_k=50,
            threshold=0.85
        )
        
        if len(similar_memories) == 0:
            novelty = 1.0  # Completely novel
        elif len(similar_memories) < 3:
            novelty = 0.8  # Rare
        elif len(similar_memories) < 10:
            novelty = 0.5  # Somewhat familiar
        else:
            novelty = 0.1  # Very familiar
        
        return novelty
    
    
    def _assess_context_richness(self, event):
        """
        How much context/detail was captured?
        
        Rich context = better for long-term storage
        Sparse context = may not be worth storing
        """
        
        event_data = event.get('data', {})
        
        # Count fields with meaningful data
        meaningful_fields = 0
        total_fields = 0
        
        important_fields = {
            'description': 1.0,
            'outcome': 1.0,
            'error_message': 0.8,
            'stack_trace': 0.8,
            'user_context': 0.6,
            'system_state': 0.6,
            'timestamp': 0.5,
            'metadata': 0.5
        }
        
        richness_score = 0
        for field, weight in important_fields.items():
            if field in event_data and event_data[field]:
                richness_score += weight
        
        max_richness = sum(important_fields.values())
        context_richness = richness_score / max_richness
        
        return min(1.0, context_richness)
    
    
    def _assess_emotional_intensity(self, event):
        """
        How emotionally significant is this event?
        
        Used for shock memory prioritization
        """
        
        intensity_indicators = {
            'was_failure': event.get('outcome') == 'failure',
            'affected_users': event.get('affected_user_count', 0) > 0,
            'financial_impact': event.get('financial_impact_usd', 0) > 0,
            'system_down': event.get('system_down_duration_sec', 0) > 0,
            'data_loss': event.get('data_lost_count', 0) > 0
        }
        
        # Score based on indicators
        intensity = sum([
            0.3 if intensity_indicators['was_failure'] else 0,
            0.2 if intensity_indicators['affected_users'] else 0,
            0.3 if intensity_indicators['financial_impact'] else 0,
            0.4 if intensity_indicators['system_down'] else 0,
            0.4 if intensity_indicators['data_loss'] else 0
        ])
        
        return min(1.0, intensity)
    
    
    def _assess_temporal_urgency(self, event):
        """
        Does this event need immediate action?
        
        Urgent events get priority routing
        """
        
        urgency_factors = {
            'is_time_sensitive': event.get('is_time_sensitive', False),
            'deadline_hours': event.get('deadline_hours', float('inf')),
            'stakeholders_waiting': event.get('stakeholders_waiting', 0)
        }
        
        urgency = 0
        if urgency_factors['is_time_sensitive']:
            urgency += 0.3
        
        hours = urgency_factors['deadline_hours']
        if hours < 1:
            urgency += 0.5
        elif hours < 24:
            urgency += 0.3
        else:
            urgency += 0.1
        
        urgency += min(0.2, urgency_factors['stakeholders_waiting'] * 0.05)
        
        return min(1.0, urgency)
    
    
    # ==================== SCORING ====================
    
    def _calculate_scores(self, signals):
        """
        Calculate weighted scores for each potential routing destination.
        
        Returns:
            {
                'long_term': float,
                'procedural': float,
                'shock': float,
                'gut_pattern': float,
                'decay': float
            }
        """
        
        scores = {}
        
        # LONG-TERM MEMORY SCORE
        # Prioritizes: high success, moderate novelty, good context
        scores['long_term'] = (
            signals['success_score'] * 0.40 +
            signals['repetition_signal'] * 0.30 +
            signals['context_richness'] * 0.20 +
            (1 - signals['pattern_novelty']) * 0.10  # Less novel is better
        )
        
        # PROCEDURAL MEMORY SCORE
        # Prioritizes: high success, high repetition, moderate criticality
        scores['procedural'] = (
            signals['success_score'] * 0.50 +
            signals['repetition_signal'] * 0.35 +
            (1 - signals['criticality']) * 0.15  # Not too critical
        )
        
        # SHOCK MEMORY SCORE
        # Prioritizes: high criticality, high emotional intensity
        scores['shock'] = (
            signals['criticality'] * 0.50 +
            signals['emotional_intensity'] * 0.30 +
            signals['temporal_urgency'] * 0.20
        )
        
        # GUT PATTERN SCORE
        # Prioritizes: moderate success, high novelty, repeating patterns
        scores['gut_pattern'] = (
            signals['success_score'] * 0.25 +
            signals['pattern_novelty'] * 0.40 +
            signals['repetition_signal'] * 0.25 +
            signals['criticality'] * 0.10
        )
        
        # DECAY SCORE (should be deleted/forgotten)
        # Low success + low context + high familiarity = candidate for forgetting
        scores['decay'] = (
            (1 - signals['success_score']) * 0.40 +
            (1 - signals['context_richness']) * 0.30 +
            (1 - signals['pattern_novelty']) * 0.30
        )
        
        return scores
    
    
    # ==================== ROUTING DECISION ====================
    
    def _determine_route(self, scores):
        """
        Use scores to determine best routing destination.
        
        Rules:
        1. If shock score > 0.85: SHOCK MEMORY
        2. If decay score > 0.7: DECAY
        3. If procedural score > 0.60 AND repetition is high: PROCEDURAL
        4. If long_term score > 0.70: LONG_TERM
        5. If gut_pattern score > 0.50: GUT_PATTERN (contribution)
        6. Otherwise: FRESH (keep in buffer for now)
        """
        
        decision = {
            'target_tier': None,
            'confidence': 0,
            'reasoning': {},
            'alternative_routes': []
        }
        
        # Rule 1: Critical failures go to shock memory
        if scores['shock'] > self.routing_thresholds['shock']:
            decision['target_tier'] = 'SHOCK'
            decision['confidence'] = scores['shock']
            decision['reasoning'] = {
                'rule': 'Critical incident detection',
                'score': scores['shock'],
                'reason': 'High criticality and emotional intensity'
            }
            return decision
        
        # Rule 2: Low-value memories are forgotten
        if scores['decay'] > 0.70:
            decision['target_tier'] = 'DECAY'
            decision['confidence'] = scores['decay']
            decision['reasoning'] = {
                'rule': 'Low-value forgetting',
                'score': scores['decay'],
                'reason': 'Low success, poor context, familiar pattern'
            }
            return decision
        
        # Rule 3: Repeated successes become habits
        if scores['procedural'] > self.routing_thresholds['procedural']:
            decision['target_tier'] = 'PROCEDURAL'
            decision['confidence'] = scores['procedural']
            decision['reasoning'] = {
                'rule': 'Habit consolidation',
                'score': scores['procedural'],
                'reason': 'High success with repetition'
            }
            return decision
        
        # Rule 4: Successful experiences go to long-term
        if scores['long_term'] > self.routing_thresholds['long_term']:
            decision['target_tier'] = 'LONG_TERM'
            decision['confidence'] = scores['long_term']
            decision['reasoning'] = {
                'rule': 'Long-term storage',
                'score': scores['long_term'],
                'reason': 'Good success, moderate novelty, rich context'
            }
            return decision
        
        # Rule 5: Interesting patterns feed the gut agent
        if scores['gut_pattern'] > self.routing_thresholds['gut_pattern']:
            decision['target_tier'] = 'GUT_PATTERN'
            decision['confidence'] = scores['gut_pattern']
            decision['reasoning'] = {
                'rule': 'Collective pattern',
                'score': scores['gut_pattern'],
                'reason': 'Interesting pattern for collective intuition'
            }
            return decision
        
        # Default: Keep in fresh memory for now
        decision['target_tier'] = 'FRESH'
        decision['confidence'] = 0.5
        decision['reasoning'] = {
            'rule': 'Indeterminate - waiting for more data',
            'scores': scores,
            'reason': 'No strong signal for routing yet'
        }
        
        # Alternative routes (sorted by score)
        sorted_routes = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        decision['alternative_routes'] = [
            (tier, score) for tier, score in sorted_routes
            if tier != decision['target_tier'] and score > 0.3
        ]
        
        return decision
    
    
    # ==================== HELPER FUNCTIONS ====================
    
    def _generate_signature(self, event):
        """Generate a compact signature for pattern matching."""
        return {
            'event_type': event.get('event_type'),
            'outcome': event.get('outcome'),
            'category': event.get('category')
        }
    
    
    def _query_similar_patterns(self, signature):
        """Query database for similar patterns."""
        # This would query the memory database
        # Placeholder implementation
        return 0
    
    
    def _query_vector_db(self, embedding, top_k=50, threshold=0.85):
        """Query vector database for similar memories."""
        # This would use Weaviate/Pinecone
        # Placeholder implementation
        return []
    
    
    def _record_routing_decision(self, event, decision):
        """Log the routing decision for future learning."""
        # Store in analytics_metadata table
        pass


# ==================== LEARNING & ADAPTATION ====================

class AnalyticsAgentLearner:
    """
    Learns from routing outcomes to improve future decisions.
    """
    
    def __init__(self, analytics_agent):
        self.agent = analytics_agent
    
    
    def feedback_loop(self, event_id, target_tier, actual_outcome):
        """
        Receive feedback about whether routing was correct.
        
        Adjust weights based on success/failure.
        """
        
        # Query the routing decision from analytics_metadata
        routing_record = self._get_routing_record(event_id)
        
        # Determine if routing was successful
        was_successful = self._evaluate_success(actual_outcome, target_tier)
        
        # If unsuccessful, analyze why and adjust weights
        if not was_successful:
            self._adjust_weights(routing_record, target_tier)
        
        # Store feedback for future analysis
        self._store_feedback(event_id, was_successful, target_tier)
    
    
    def _evaluate_success(self, actual_outcome, target_tier):
        """
        Was the routing decision correct?
        
        Success criteria vary by tier:
        - LONG_TERM: Memory was actually useful/accessed
        - PROCEDURAL: Habit formation was successful
        - SHOCK: Critical issue prevented recurrence
        - DECAY: Memory didn't need to be recalled
        """
        
        success_criteria = {
            'LONG_TERM': actual_outcome.get('was_retrieved', False),
            'PROCEDURAL': actual_outcome.get('execution_automated', False),
            'SHOCK': actual_outcome.get('incident_prevented', False),
            'DECAY': not actual_outcome.get('regret_forgotten', False),
            'GUT_PATTERN': actual_outcome.get('contributed_to_intuition', False)
        }
        
        return success_criteria.get(target_tier, False)
    
    
    def _adjust_weights(self, routing_record, target_tier):
        """
        Adjust the weights in the analytics agent based on failures.
        
        Uses gradient descent-like approach.
        """
        
        learning_rate = 0.01
        
        # Get the signals that led to this routing
        signals = routing_record['signals']
        
        # If routing was wrong, reduce weight of signals that led to it
        # This is simplified; real implementation would be more sophisticated
        
        pass


```

---

## EXAMPLE ROUTING SCENARIOS

### Scenario 1: Successful API Call
```json
{
  "event_type": "api_call",
  "outcome": "success",
  "error_rate": 0,
  "execution_time_ms": 245,
  "user_satisfaction": 0.95,
  "performance_vs_baseline": 1.2,
  "repetition_count": 3,
  "criticality": 0.1,
  "context_richness": 0.8
}

ANALYTICS AGENT ANALYSIS:
- success_score: 0.95
- repetition_signal: 0.65 (3 repetitions)
- criticality: 0.1
- context_richness: 0.8

SCORES:
- long_term: 0.78 ✓ (passes threshold 0.70)
- procedural: 0.63
- shock: 0.05
- decay: 0.05

→ ROUTE TO: LONG_TERM MEMORY
→ CONFIDENCE: 0.78
```

### Scenario 2: Security Breach
```json
{
  "event_type": "security_breach",
  "severity": 0.95,
  "impact_scope": "all",
  "outcome": "failure",
  "affected_user_count": 5000,
  "data_lost_count": 1000000,
  "financial_impact_usd": 500000
}

ANALYTICS AGENT ANALYSIS:
- criticality: 0.95
- emotional_intensity: 0.95
- success_score: 0.05

SCORES:
- shock: 0.92 ✓ (passes threshold 0.85)
- long_term: 0.25
- procedural: 0.15

→ ROUTE TO: SHOCK MEMORY
→ CONFIDENCE: 0.92
→ PRESERVATION: Maximum decay resistance
```

### Scenario 3: Repeated Deployment
```json
{
  "event_type": "deployment",
  "outcome": "success",
  "execution_time_ms": 1500,
  "user_satisfaction": 0.95,
  "repetition_count": 15,
  "pattern_novelty": 0.1,
  "context_richness": 0.7
}

ANALYTICS AGENT ANALYSIS:
- success_score: 0.90
- repetition_signal: 0.95 (15 repetitions!)
- pattern_novelty: 0.1

SCORES:
- procedural: 0.78 ✓ (passes threshold 0.60)
- long_term: 0.72
- decay: 0.05

→ ROUTE TO: PROCEDURAL MEMORY
→ CONFIDENCE: 0.78
→ RESULT: Becomes automated habit
```

---

## INTEGRATION WITH DECAY SYSTEM

The Analytics Agent also manages memory decay:

```python
def calculate_decay_rate(memory):
    """
    Determine how fast a memory should decay.
    
    Factors:
    - Success rate (failures decay faster)
    - Access frequency (rarely accessed decays faster)
    - Importance/criticality (critical memories never decay)
    """
    
    base_decay_rate = 0.01  # 1% per day
    
    # Success multiplier: failures decay 5x faster
    success_multiplier = 1.0 if memory.success_score < 0.5 else 0.2
    
    # Access multiplier: rarely used memories decay faster
    if memory.access_count == 0:
        access_multiplier = 2.0
    elif memory.access_count < 5:
        access_multiplier = 1.5
    else:
        access_multiplier = 0.5
    
    # Criticality: shock memories nearly never decay
    criticality_multiplier = 0.01 if memory.is_critical else 1.0
    
    final_decay_rate = base_decay_rate * success_multiplier * access_multiplier * criticality_multiplier
    
    return final_decay_rate
```

---

This provides the foundation for intelligent, adaptive memory management that mimics how human brains decide what to keep and what to forget.
