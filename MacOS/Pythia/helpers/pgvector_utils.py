"""
Pythia — pgvector Utilities
Convert Python lists to PostgreSQL vector format.
"""


def embedding_to_pgvector(embedding: list[float]) -> str:
    """Convert list[float] to pgvector string format '[0.1,0.2,...]'."""
    return "[" + ",".join(str(round(v, 8)) for v in embedding) + "]"
