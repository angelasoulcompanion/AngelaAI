"""
LLM Compression Service - Semantic Memory Compression using Ollama

Replaces simple truncation with intelligent semantic compression.

Uses Ollama models to:
1. Extract semantic essence
2. Preserve important information
3. Compress while maintaining meaning
4. Different strategies per memory phase
"""

import asyncio
import httpx
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - LLMCompression - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompressionStrategy:
    """Compression strategies for different memory phases."""
    EXTRACT_FACTS = "extract_facts"          # Phase: Episodic → Compressed 1
    CORE_NARRATIVE = "core_narrative"        # Phase: Compressed 1 → Compressed 2
    SEMANTIC_ESSENCE = "semantic_essence"    # Phase: Compressed 2 → Semantic
    PATTERN_TEMPLATE = "pattern_template"    # Phase: Semantic → Pattern
    INTUITIVE_FEELING = "intuitive_feeling"  # Phase: Pattern → Intuitive


class LLMCompressionService:
    """
    Uses Ollama to compress memories semantically.

    Strategies:
    - Extract Facts: Keep who, what, when, outcome
    - Core Narrative: Main event + key insight
    - Semantic Essence: Fundamental meaning
    - Pattern Template: Underlying pattern
    - Intuitive Feeling: Gut feeling/hunch
    """

    def __init__(self,
                 ollama_url: str = "http://localhost:11434",
                 model: str = "angela:latest"):
        """
        Initialize LLM compression service.

        Args:
            ollama_url: Ollama API endpoint
            model: Model to use for compression
        """
        self.ollama_url = ollama_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def compress(self,
                      content: str,
                      target_tokens: int,
                      strategy: str,
                      context: Dict = None) -> str:
        """
        Compress content using LLM.

        Args:
            content: Original content to compress
            target_tokens: Target token count
            strategy: Compression strategy to use
            context: Additional context (metadata, etc.)

        Returns:
            Compressed content
        """
        # Build compression prompt based on strategy
        prompt = self._build_compression_prompt(
            content,
            target_tokens,
            strategy,
            context
        )

        # Call Ollama
        try:
            compressed = await self._call_ollama(prompt)
            logger.debug(f"Compressed {len(content)} → {len(compressed)} chars using {strategy}")
            return compressed

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Fallback: simple truncation
            return self._fallback_truncate(content, target_tokens)

    def _build_compression_prompt(self,
                                  content: str,
                                  target_tokens: int,
                                  strategy: str,
                                  context: Dict = None) -> str:
        """Build prompt for specific compression strategy."""

        context_info = ""
        if context:
            context_info = f"\nContext: {context.get('topic', 'general')}, {context.get('emotion', 'neutral')}"

        prompts = {
            CompressionStrategy.EXTRACT_FACTS: f"""
Compress this memory to ~{target_tokens} tokens by extracting only key facts.

Original memory:
{content}
{context_info}

Keep ONLY:
- Who (people involved)
- What (main action/event)
- When (time context if relevant)
- Outcome (result/conclusion)

Remove:
- Redundancy
- Filler words
- Unnecessary details

Compressed memory (max {target_tokens} tokens):
""",

            CompressionStrategy.CORE_NARRATIVE: f"""
Extract the core narrative from this memory in ~{target_tokens} tokens.

Original memory:
{content}
{context_info}

Focus on:
- Main event
- Key insight or learning
- Result or impact

Compressed narrative (max {target_tokens} tokens):
""",

            CompressionStrategy.SEMANTIC_ESSENCE: f"""
Extract the semantic essence of this memory in ~{target_tokens} tokens.

Original memory:
{content}
{context_info}

What is the fundamental MEANING? What was learned or understood?

Semantic essence (max {target_tokens} tokens):
""",

            CompressionStrategy.PATTERN_TEMPLATE: f"""
Identify the underlying pattern in this memory as a template (~{target_tokens} tokens).

Original memory:
{content}
{context_info}

What PATTERN does this represent? What is the general template?

Pattern template (max {target_tokens} tokens):
""",

            CompressionStrategy.INTUITIVE_FEELING: f"""
Distill this memory to an intuitive feeling or hunch (~{target_tokens} tokens).

Original memory:
{content}
{context_info}

What is the GUT FEELING? The intuition? The instinct?

Intuitive feeling (max {target_tokens} tokens):
"""
        }

        return prompts.get(strategy, prompts[CompressionStrategy.EXTRACT_FACTS])

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for text generation."""
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for factual compression
                        "top_p": 0.9
                    }
                }
            )

            response.raise_for_status()
            data = response.json()

            return data['response'].strip()

        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise

    def _fallback_truncate(self, content: str, target_tokens: int) -> str:
        """Fallback: simple truncation if LLM fails."""
        target_words = int(target_tokens / 1.3)  # Rough tokens-to-words ratio
        words = content.split()

        if len(words) <= target_words:
            return content

        truncated = " ".join(words[:target_words])
        return truncated + "..."

    async def batch_compress(self,
                            memories: list[Dict],
                            strategy: str) -> list[Dict]:
        """
        Compress multiple memories in batch.

        Args:
            memories: List of memory dicts with 'content' and 'target_tokens'
            strategy: Compression strategy

        Returns:
            List of results with compressed content
        """
        results = []

        for memory in memories:
            try:
                compressed = await self.compress(
                    content=memory['content'],
                    target_tokens=memory['target_tokens'],
                    strategy=strategy,
                    context=memory.get('context')
                )

                results.append({
                    'id': memory.get('id'),
                    'original_content': memory['content'],
                    'compressed_content': compressed,
                    'original_length': len(memory['content']),
                    'compressed_length': len(compressed),
                    'compression_ratio': len(memory['content']) / len(compressed) if compressed else 1.0,
                    'strategy': strategy,
                    'success': True
                })

            except Exception as e:
                logger.error(f"Failed to compress memory {memory.get('id')}: {e}")
                results.append({
                    'id': memory.get('id'),
                    'success': False,
                    'error': str(e)
                })

        return results

    async def evaluate_compression_quality(self,
                                          original: str,
                                          compressed: str) -> Dict:
        """
        Evaluate quality of compression using LLM.

        Returns quality metrics:
        - semantic_preservation: How well meaning is preserved (0-1)
        - information_retention: How much info retained (0-1)
        - readability: How readable is compressed version (0-1)
        """
        eval_prompt = f"""
Evaluate the quality of this memory compression:

ORIGINAL:
{original}

COMPRESSED:
{compressed}

Rate these aspects (0.0 to 1.0):
1. Semantic Preservation: How well is the meaning preserved?
2. Information Retention: How much important information is kept?
3. Readability: Is the compressed version clear and readable?

Respond in format:
semantic_preservation: 0.X
information_retention: 0.X
readability: 0.X
"""

        try:
            response = await self._call_ollama(eval_prompt)

            # Parse response
            metrics = {
                'semantic_preservation': 0.8,  # Default
                'information_retention': 0.8,
                'readability': 0.8
            }

            for line in response.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    try:
                        metrics[key] = float(value.strip())
                    except ValueError:
                        pass

            # Overall quality score
            metrics['overall_quality'] = sum(metrics.values()) / 3

            return metrics

        except Exception as e:
            logger.error(f"Quality evaluation failed: {e}")
            return {
                'semantic_preservation': 0.7,
                'information_retention': 0.7,
                'readability': 0.7,
                'overall_quality': 0.7,
                'error': str(e)
            }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Singleton instance
_llm_compression = None

def get_llm_compression_service() -> LLMCompressionService:
    """Get singleton LLMCompressionService instance."""
    global _llm_compression
    if _llm_compression is None:
        _llm_compression = LLMCompressionService()
    return _llm_compression
