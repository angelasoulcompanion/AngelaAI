"""
Pythia Configuration — Quantitative Finance + AI Analysis Platform
"""
import os


class PythiaConfig:
    APP_NAME = "Pythia"
    APP_VERSION = "1.0.0"
    DEBUG = True

    # ── LLM Configuration ──────────────────────────────
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "scb10x/typhoon2.5-qwen3-4b")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")

    CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    CLAUDE_DAILY_LIMIT = 50  # max Claude API calls per day

    LLM_TEMPERATURE = 0.3  # financial precision
    LLM_MAX_TOKENS = 1024

    # MPT Settings
    RISK_FREE_RATES = {
        "THB": 0.0225,   # Bank of Thailand rate
        "USD": 0.0435,   # US Federal Funds rate
    }
    DEFAULT_RISK_FREE_RATE = 0.0225
    DEFAULT_BENCHMARK = "^SET"
    TRADING_DAYS_PER_YEAR = 252

    # Data Sources
    YAHOO_FINANCE_ENABLED = True
    PRICE_HISTORY_DAYS = 365

    # Risk Management
    VAR_CONFIDENCE_LEVEL = 0.95
    VAR_HOLDING_PERIOD = 1

    # Monte Carlo
    MC_DEFAULT_SIMULATIONS = 10000
    MC_DEFAULT_TIME_STEPS = 252

    # Optimization
    OPTIMIZATION_MAX_ITERATIONS = 1000
    OPTIMIZATION_TOLERANCE = 1e-8

    @classmethod
    def get_settings_dict(cls) -> dict:
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "risk_free_rates": cls.RISK_FREE_RATES,
            "default_benchmark": cls.DEFAULT_BENCHMARK,
            "trading_days": cls.TRADING_DAYS_PER_YEAR,
            "var_confidence": cls.VAR_CONFIDENCE_LEVEL,
            "mc_simulations": cls.MC_DEFAULT_SIMULATIONS,
        }
