"""
Pythia Router — Options Pricing (Black-Scholes)
"""
from typing import Optional

from fastapi import APIRouter, Query

from services.black_scholes_service import (
    price_option,
    implied_volatility,
    generate_greeks_surface,
)

router = APIRouter(prefix="/api/options", tags=["Options"])


@router.get("/price")
async def option_price(
    option_type: str = Query("call", description="call | put"),
    spot: float = Query(..., description="Current spot price"),
    strike: float = Query(..., description="Strike price"),
    time_to_expiry: float = Query(..., description="Time to expiry in years"),
    risk_free_rate: float = Query(0.0225, ge=0, le=0.5),
    volatility: float = Query(0.20, ge=0.01, le=5.0),
    dividend_yield: float = Query(0.0, ge=0, le=0.2),
):
    result = price_option(option_type, spot, strike, time_to_expiry, risk_free_rate, volatility, dividend_yield)
    return {
        "option_type": result.option_type,
        "spot": result.spot,
        "strike": result.strike,
        "time_to_expiry": result.time_to_expiry,
        "price": result.price,
        "intrinsic_value": result.intrinsic_value,
        "time_value": result.time_value,
        "greeks": {
            "delta": result.delta,
            "gamma": result.gamma,
            "theta": result.theta,
            "vega": result.vega,
            "rho": result.rho,
        },
    }


@router.get("/implied-volatility")
async def calc_implied_volatility(
    option_type: str = Query("call"),
    market_price: float = Query(..., description="Observed market price"),
    spot: float = Query(...),
    strike: float = Query(...),
    time_to_expiry: float = Query(...),
    risk_free_rate: float = Query(0.0225),
    dividend_yield: float = Query(0.0),
):
    result = implied_volatility(option_type, market_price, spot, strike, time_to_expiry, risk_free_rate, dividend_yield)
    return result


@router.get("/greeks-surface")
async def greeks_surface(
    option_type: str = Query("call"),
    spot: float = Query(...),
    risk_free_rate: float = Query(0.0225),
    volatility: float = Query(0.20),
    n_strikes: int = Query(20, ge=5, le=50),
    n_expiries: int = Query(20, ge=5, le=50),
):
    result = generate_greeks_surface(option_type, spot, risk_free_rate, volatility,
                                     n_strikes=n_strikes, n_expiries=n_expiries)
    return result
