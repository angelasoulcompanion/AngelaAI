"""
Pythia Pydantic Models — Request/Response schemas for FastAPI
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# ASSETS
# ============================================================

class AssetCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str = "thai_stock"
    exchange: Optional[str] = None
    currency: str = "THB"
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: str = "Thailand"


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# PORTFOLIOS
# ============================================================

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_currency: str = "THB"
    benchmark_symbol: str = "^SET"
    risk_free_rate: Decimal = Decimal("0.02")
    initial_capital: Optional[Decimal] = None
    inception_date: Optional[date] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    benchmark_symbol: Optional[str] = None
    risk_free_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None


# ============================================================
# HOLDINGS
# ============================================================

class HoldingCreate(BaseModel):
    asset_id: UUID
    weight: Decimal
    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None


class HoldingUpdate(BaseModel):
    weight: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    target_weight: Optional[Decimal] = None


# ============================================================
# TRANSACTIONS
# ============================================================

class TransactionCreate(BaseModel):
    asset_id: UUID
    transaction_type: str
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal("0")
    taxes: Decimal = Decimal("0")
    total_amount: Decimal
    transaction_date: date
    settlement_date: Optional[date] = None
    notes: Optional[str] = None


# ============================================================
# WATCHLIST
# ============================================================

class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WatchlistItemAdd(BaseModel):
    asset_id: UUID
    notes: Optional[str] = None


# ============================================================
# SETTINGS
# ============================================================

class SettingUpdate(BaseModel):
    setting_value: str
