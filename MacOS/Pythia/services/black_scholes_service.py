"""
Pythia — Black-Scholes Options Pricing Service
European options: Call/Put pricing, Greeks, Implied Volatility.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

from config import PythiaConfig


@dataclass
class OptionPrice:
    option_type: str  # call or put
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    price: float
    intrinsic_value: float
    time_value: float
    # Greeks
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    success: bool = True
    message: str = ""


def price_option(
    option_type: str,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
) -> OptionPrice:
    """Price a European option using Black-Scholes-Merton."""
    if time_to_expiry <= 0:
        intrinsic = max(spot - strike, 0) if option_type == "call" else max(strike - spot, 0)
        return OptionPrice(
            option_type=option_type, spot=spot, strike=strike,
            time_to_expiry=0, risk_free_rate=risk_free_rate, volatility=volatility,
            price=intrinsic, intrinsic_value=intrinsic, time_value=0,
            delta=1.0 if option_type == "call" and spot > strike else (-1.0 if option_type == "put" and spot < strike else 0.0),
            gamma=0, theta=0, vega=0, rho=0,
        )

    T = time_to_expiry
    S = spot
    K = strike
    r = risk_free_rate
    q = dividend_yield
    sigma = volatility

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = np.exp(-q * T) * norm.cdf(d1)
        intrinsic = max(S - K, 0)
        rho_val = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        delta = -np.exp(-q * T) * norm.cdf(-d1)
        intrinsic = max(K - S, 0)
        rho_val = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
    theta = (-(S * sigma * np.exp(-q * T) * norm.pdf(d1)) / (2 * np.sqrt(T))
             - r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))
             + q * S * np.exp(-q * T) * (norm.cdf(d1) if option_type == "call" else norm.cdf(-d1))) / 365
    vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100

    return OptionPrice(
        option_type=option_type, spot=spot, strike=strike,
        time_to_expiry=T, risk_free_rate=r, volatility=sigma,
        price=round(float(price), 4),
        intrinsic_value=round(float(intrinsic), 4),
        time_value=round(float(price - intrinsic), 4),
        delta=round(float(delta), 6),
        gamma=round(float(gamma), 6),
        theta=round(float(theta), 6),
        vega=round(float(vega), 6),
        rho=round(float(rho_val), 6),
    )


def implied_volatility(
    option_type: str,
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    dividend_yield: float = 0.0,
) -> dict:
    """Calculate implied volatility from market price using Brent's method."""
    def objective(sigma: float) -> float:
        result = price_option(option_type, spot, strike, time_to_expiry, risk_free_rate, sigma, dividend_yield)
        return result.price - market_price

    try:
        iv = brentq(objective, 0.001, 5.0, xtol=1e-8)
        return {
            "implied_volatility": round(float(iv), 6),
            "market_price": market_price,
            "success": True,
        }
    except ValueError:
        return {
            "implied_volatility": None,
            "market_price": market_price,
            "success": False,
            "message": "Cannot find implied volatility in range [0.1%, 500%]",
        }


def generate_greeks_surface(
    option_type: str,
    spot: float,
    risk_free_rate: float,
    volatility: float,
    strike_range: tuple[float, float] = (0.8, 1.2),
    expiry_range: tuple[float, float] = (0.05, 2.0),
    n_strikes: int = 20,
    n_expiries: int = 20,
) -> dict:
    """Generate Greeks surface data for 3D visualization."""
    strikes = np.linspace(spot * strike_range[0], spot * strike_range[1], n_strikes)
    expiries = np.linspace(expiry_range[0], expiry_range[1], n_expiries)

    surface = []
    for K in strikes:
        for T in expiries:
            result = price_option(option_type, spot, float(K), float(T), risk_free_rate, volatility)
            surface.append({
                "strike": round(float(K), 2),
                "expiry": round(float(T), 4),
                "price": result.price,
                "delta": result.delta,
                "gamma": result.gamma,
                "theta": result.theta,
                "vega": result.vega,
            })

    return {
        "option_type": option_type,
        "spot": spot,
        "volatility": volatility,
        "risk_free_rate": risk_free_rate,
        "surface": surface,
    }
