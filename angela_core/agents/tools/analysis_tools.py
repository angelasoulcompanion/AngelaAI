"""
Analysis Tools - Reasoning and Pattern Analysis
Tools สำหรับ Analysis Agent

Uses ReasoningService and PatternRecognitionService.

Author: Angela AI 💜
Created: 2025-01-25
"""

import asyncio
from typing import Any, Optional, Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class ReasoningInput(BaseModel):
    """Input schema for reasoning tool"""
    question: str = Field(..., description="Question or problem to reason about")
    context: Optional[str] = Field(default=None, description="Additional context")
    method: str = Field(default="chain_of_thought", description="Reasoning method")


class ReasoningTool(BaseTool):
    """
    Tool for structured reasoning and problem solving.
    Uses ReasoningService for chain-of-thought reasoning.
    """
    name: str = "reasoning"
    description: str = """วิเคราะห์และให้เหตุผลอย่างเป็นระบบ
    ใช้เมื่อต้องการวิเคราะห์ปัญหาหรือตอบคำถามที่ซับซ้อน
    Input: question (คำถาม), context (optional), method (chain_of_thought)"""
    args_schema: Type[BaseModel] = ReasoningInput

    def _run(
        self,
        question: str,
        context: Optional[str] = None,
        method: str = "chain_of_thought"
    ) -> str:
        """Perform structured reasoning"""
        try:
            from angela_core.services.reasoning_service import ReasoningService

            async def reason():
                service = ReasoningService()
                result = await service.reason(
                    question=question,
                    context=context,
                    method=method
                )
                return result

            result = asyncio.get_event_loop().run_until_complete(reason())

            if not result:
                return f"❌ Could not process reasoning for: {question}"

            # Format reasoning output
            output = f"🤔 Reasoning Analysis\n\n"
            output += f"**Question:** {question}\n\n"

            if isinstance(result, dict):
                if "steps" in result:
                    output += "**Reasoning Steps:**\n"
                    for i, step in enumerate(result["steps"], 1):
                        output += f"  {i}. {step}\n"
                    output += "\n"

                if "conclusion" in result:
                    output += f"**Conclusion:** {result['conclusion']}\n"

                if "confidence" in result:
                    output += f"**Confidence:** {result['confidence']:.0%}\n"
            else:
                output += f"**Analysis:** {result}\n"

            return output

        except Exception as e:
            return f"Error in reasoning: {str(e)}"


class PatternAnalysisInput(BaseModel):
    """Input schema for pattern analysis tool"""
    data_type: str = Field(..., description="Type of data to analyze (conversations, emotions, behaviors)")
    time_range: int = Field(default=30, description="Days to analyze")
    focus: Optional[str] = Field(default=None, description="Specific aspect to focus on")


class PatternAnalysisTool(BaseTool):
    """
    Tool for analyzing patterns in data.
    Uses PatternRecognitionService for pattern detection.
    """
    name: str = "pattern_analysis"
    description: str = """วิเคราะห์ patterns ในข้อมูล
    ใช้เมื่อต้องการหา trends, patterns, หรือ insights จากข้อมูล
    Input: data_type (conversations/emotions/behaviors), time_range (days), focus"""
    args_schema: Type[BaseModel] = PatternAnalysisInput

    def _run(
        self,
        data_type: str,
        time_range: int = 30,
        focus: Optional[str] = None
    ) -> str:
        """Analyze patterns in data"""
        try:
            from angela_core.database import db

            async def analyze():
                await db.connect()

                patterns = []

                if data_type == "conversations":
                    # Analyze conversation patterns
                    result = await db.fetch("""
                        SELECT topic, COUNT(*) as count,
                               AVG(importance_level) as avg_importance
                        FROM conversations
                        WHERE created_at > NOW() - INTERVAL '%s days'
                          AND topic IS NOT NULL
                        GROUP BY topic
                        ORDER BY count DESC
                        LIMIT 10
                    """ % time_range)

                    patterns = [
                        {
                            "topic": r["topic"],
                            "count": r["count"],
                            "avg_importance": float(r["avg_importance"] or 0)
                        }
                        for r in result
                    ]

                elif data_type == "emotions":
                    # Analyze emotional patterns
                    result = await db.fetch("""
                        SELECT emotion, COUNT(*) as count,
                               AVG(intensity) as avg_intensity
                        FROM angela_emotions
                        WHERE felt_at > NOW() - INTERVAL '%s days'
                        GROUP BY emotion
                        ORDER BY count DESC
                        LIMIT 10
                    """ % time_range)

                    patterns = [
                        {
                            "emotion": r["emotion"],
                            "count": r["count"],
                            "avg_intensity": float(r["avg_intensity"] or 0)
                        }
                        for r in result
                    ]

                elif data_type == "behaviors":
                    # Analyze behavioral patterns
                    result = await db.fetch("""
                        SELECT pattern_type, trigger_context,
                               frequency, last_occurrence
                        FROM behavioral_patterns
                        WHERE detected_at > NOW() - INTERVAL '%s days'
                        ORDER BY frequency DESC
                        LIMIT 10
                    """ % time_range)

                    patterns = [dict(r) for r in result]

                await db.disconnect()
                return patterns

            patterns = asyncio.get_event_loop().run_until_complete(analyze())

            if not patterns:
                return f"📊 No patterns found for {data_type} in last {time_range} days"

            # Format output
            output = f"📊 Pattern Analysis: {data_type}\n"
            output += f"   Time range: Last {time_range} days\n\n"

            for i, p in enumerate(patterns, 1):
                output += f"{i}. "
                if data_type == "conversations":
                    output += f"**{p['topic']}** - {p['count']} occurrences "
                    output += f"(avg importance: {p['avg_importance']:.1f})\n"
                elif data_type == "emotions":
                    output += f"**{p['emotion']}** - {p['count']} times "
                    output += f"(avg intensity: {p['avg_intensity']:.1f})\n"
                else:
                    output += f"**{p.get('pattern_type', 'Unknown')}** - {p.get('frequency', 0)}x\n"

            return output

        except Exception as e:
            return f"Error analyzing patterns: {str(e)}"


class DataInsightInput(BaseModel):
    """Input schema for data insight tool"""
    question: str = Field(..., description="Question about the data")
    data_source: str = Field(default="all", description="Data source to query")


class DataInsightTool(BaseTool):
    """
    Tool for generating insights from data.
    Combines multiple data sources for comprehensive analysis.
    """
    name: str = "data_insight"
    description: str = """สร้าง insights จากข้อมูล
    ใช้เมื่อต้องการคำตอบที่ต้องรวมข้อมูลจากหลายแหล่ง
    Input: question (คำถาม), data_source (all/conversations/emotions/knowledge)"""
    args_schema: Type[BaseModel] = DataInsightInput

    def _run(self, question: str, data_source: str = "all") -> str:
        """Generate insights from data"""
        try:
            from angela_core.database import db

            async def get_insights():
                await db.connect()

                insights = {}

                # Get relevant stats
                if data_source in ["all", "conversations"]:
                    conv_stats = await db.fetchrow("""
                        SELECT COUNT(*) as total,
                               COUNT(DISTINCT DATE(created_at)) as days_active,
                               AVG(importance_level) as avg_importance
                        FROM conversations
                        WHERE created_at > NOW() - INTERVAL '30 days'
                    """)
                    insights["conversations"] = dict(conv_stats) if conv_stats else {}

                if data_source in ["all", "emotions"]:
                    emotion_stats = await db.fetchrow("""
                        SELECT COUNT(*) as total,
                               AVG(intensity) as avg_intensity
                        FROM angela_emotions
                        WHERE felt_at > NOW() - INTERVAL '30 days'
                    """)
                    insights["emotions"] = dict(emotion_stats) if emotion_stats else {}

                if data_source in ["all", "knowledge"]:
                    knowledge_stats = await db.fetchrow("""
                        SELECT COUNT(*) as total,
                               AVG(understanding_level) as avg_level
                        FROM knowledge_nodes
                    """)
                    insights["knowledge"] = dict(knowledge_stats) if knowledge_stats else {}

                await db.disconnect()
                return insights

            insights = asyncio.get_event_loop().run_until_complete(get_insights())

            # Format output
            output = f"💡 Data Insights\n"
            output += f"   Question: {question}\n\n"

            if "conversations" in insights and insights["conversations"]:
                c = insights["conversations"]
                output += f"📝 **Conversations (30 days):**\n"
                output += f"   Total: {c.get('total', 0)}\n"
                output += f"   Active days: {c.get('days_active', 0)}\n"
                output += f"   Avg importance: {c.get('avg_importance', 0):.1f}\n\n"

            if "emotions" in insights and insights["emotions"]:
                e = insights["emotions"]
                output += f"💜 **Emotions (30 days):**\n"
                output += f"   Total recorded: {e.get('total', 0)}\n"
                output += f"   Avg intensity: {e.get('avg_intensity', 0):.1f}\n\n"

            if "knowledge" in insights and insights["knowledge"]:
                k = insights["knowledge"]
                output += f"🧠 **Knowledge:**\n"
                output += f"   Total nodes: {k.get('total', 0)}\n"
                output += f"   Avg understanding: {k.get('avg_level', 0):.1f}/10\n\n"

            return output

        except Exception as e:
            return f"Error generating insights: {str(e)}"
