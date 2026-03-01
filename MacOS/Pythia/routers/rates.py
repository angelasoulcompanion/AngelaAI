"""
Pythia — Risk-free rate management
"""
from fastapi import APIRouter, Depends

from db import get_conn
from config import PythiaConfig

router = APIRouter(prefix="/api/rates", tags=["rates"])


@router.get("/risk-free")
async def get_risk_free_rates():
    """Get current risk-free rates."""
    return PythiaConfig.RISK_FREE_RATES


@router.get("/risk-free/{currency}")
async def get_risk_free_rate(currency: str):
    """Get risk-free rate for a specific currency."""
    rate = PythiaConfig.RISK_FREE_RATES.get(currency.upper())
    if rate is None:
        return {"currency": currency.upper(), "rate": PythiaConfig.DEFAULT_RISK_FREE_RATE, "source": "default"}
    return {"currency": currency.upper(), "rate": rate, "source": "config"}
