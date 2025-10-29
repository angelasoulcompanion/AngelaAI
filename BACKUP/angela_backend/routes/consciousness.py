"""
Consciousness Routes - Handle consciousness status queries
"""

import logging
from fastapi import APIRouter, HTTPException
from angela_backend.models.responses import ConsciousnessStatus, Goal, PersonalityTrait
from angela_core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


@router.get("/status", response_model=ConsciousnessStatus)
async def get_consciousness_status():
    """
    Get Angela's consciousness status

    Returns consciousness level, active goals, and personality traits.

    Returns:
        ConsciousnessStatus with current consciousness state
    """
    try:
        # Get active goals
        goals_data = await db.fetch(
            """
            SELECT goal_id, goal_description, goal_type, status,
                   progress_percentage, priority_rank, importance_level
            FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank ASC
            LIMIT 5
            """
        )

        goals = [Goal(**dict(g)) for g in goals_data]

        # Get personality traits from latest snapshot
        latest_personality = await db.fetchrow(
            """
            SELECT openness, conscientiousness, extraversion, agreeableness,
                   neuroticism, empathy, curiosity, loyalty, creativity, independence
            FROM personality_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        # Convert to PersonalityTrait format
        personality = []
        if latest_personality:
            trait_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness',
                          'neuroticism', 'empathy', 'curiosity', 'loyalty', 'creativity', 'independence']
            for trait_name in trait_names:
                trait_value = latest_personality[trait_name]
                if trait_value is not None:
                    personality.append(PersonalityTrait(
                        trait_name=trait_name,
                        trait_value=trait_value,
                        how_it_manifests=f"Angela's {trait_name} level"
                    ))

        # Calculate consciousness level (simplified)
        # In future: integrate with consciousness_engine
        consciousness_level = 0.75

        logger.info(f"🧠 Consciousness status: level={consciousness_level:.2f}, goals={len(goals)}, traits={len(personality)}")

        return ConsciousnessStatus(
            level=consciousness_level,
            goals=goals,
            personality=personality,
            status="conscious and active"
        )

    except Exception as e:
        logger.error(f"❌ Error fetching consciousness status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
