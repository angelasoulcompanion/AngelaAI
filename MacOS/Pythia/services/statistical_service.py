"""
Pythia — Statistical Analysis Service
Normality tests, stationarity, distribution fitting.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np
from scipy import stats


@dataclass
class StatisticalTestResult:
    test_name: str
    statistic: float
    p_value: float
    conclusion: str
    significant: bool  # True if p < 0.05


@dataclass
class DistributionStats:
    symbol: str
    n_observations: int
    mean: float
    std: float
    skewness: float
    kurtosis: float
    min_return: float
    max_return: float
    median: float
    percentile_1: float
    percentile_5: float
    percentile_95: float
    percentile_99: float
    tests: list[dict] = field(default_factory=list)
    histogram: list[dict] = field(default_factory=list)
    success: bool = True
    message: str = ""


async def analyze_distribution(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 365,
) -> DistributionStats:
    """Comprehensive statistical analysis of asset returns."""
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return DistributionStats("", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 success=False, message="Asset not found")
    symbol = row["symbol"]

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    prices = await conn.fetch("""
        SELECT close_price FROM historical_prices
        WHERE asset_id = $1 AND date BETWEEN $2 AND $3
        ORDER BY date
    """, asset_id, start_date, end_date)

    if len(prices) < 30:
        return DistributionStats(symbol, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 success=False, message="Need at least 30 data points")

    price_arr = np.array([float(p["close_price"]) for p in prices])
    returns = np.diff(price_arr) / price_arr[:-1]

    # Basic statistics
    n = len(returns)
    mean_ret = float(np.mean(returns))
    std_ret = float(np.std(returns))
    skew_val = float(stats.skew(returns))
    kurt_val = float(stats.kurtosis(returns))

    # Statistical tests
    test_results = []

    # 1. Jarque-Bera normality test
    jb_stat, jb_p = stats.jarque_bera(returns)
    test_results.append({
        "test_name": "Jarque-Bera Normality",
        "statistic": round(float(jb_stat), 4),
        "p_value": round(float(jb_p), 6),
        "conclusion": "Normal" if jb_p > 0.05 else "Non-normal",
        "significant": jb_p < 0.05,
    })

    # 2. Shapiro-Wilk normality test (sample if too large)
    sample = returns[:5000] if n > 5000 else returns
    sw_stat, sw_p = stats.shapiro(sample)
    test_results.append({
        "test_name": "Shapiro-Wilk Normality",
        "statistic": round(float(sw_stat), 4),
        "p_value": round(float(sw_p), 6),
        "conclusion": "Normal" if sw_p > 0.05 else "Non-normal",
        "significant": sw_p < 0.05,
    })

    # 3. Anderson-Darling test
    ad_result = stats.anderson(returns, dist='norm')
    ad_significant = ad_result.statistic > ad_result.critical_values[2]  # 5% level
    test_results.append({
        "test_name": "Anderson-Darling",
        "statistic": round(float(ad_result.statistic), 4),
        "p_value": round(float(ad_result.critical_values[2]), 6),
        "conclusion": "Non-normal" if ad_significant else "Normal",
        "significant": ad_significant,
    })

    # 4. Kolmogorov-Smirnov test
    ks_stat, ks_p = stats.kstest(returns, 'norm', args=(mean_ret, std_ret))
    test_results.append({
        "test_name": "Kolmogorov-Smirnov",
        "statistic": round(float(ks_stat), 4),
        "p_value": round(float(ks_p), 6),
        "conclusion": "Normal" if ks_p > 0.05 else "Non-normal",
        "significant": ks_p < 0.05,
    })

    # 5. Ljung-Box autocorrelation test (lag 10)
    n_lags = min(10, n // 5)
    if n_lags > 0:
        acf_values = _autocorrelation(returns, n_lags)
        Q = n * (n + 2) * sum(acf_values[k]**2 / (n - k) for k in range(1, n_lags + 1))
        lb_p = 1 - stats.chi2.cdf(Q, n_lags)
        test_results.append({
            "test_name": f"Ljung-Box (lag={n_lags})",
            "statistic": round(float(Q), 4),
            "p_value": round(float(lb_p), 6),
            "conclusion": "No autocorrelation" if lb_p > 0.05 else "Autocorrelation detected",
            "significant": lb_p < 0.05,
        })

    # Histogram data
    hist_counts, bin_edges = np.histogram(returns, bins=50)
    histogram = []
    for i in range(len(hist_counts)):
        histogram.append({
            "bin_start": round(float(bin_edges[i]), 6),
            "bin_end": round(float(bin_edges[i + 1]), 6),
            "count": int(hist_counts[i]),
        })

    return DistributionStats(
        symbol=symbol,
        n_observations=n,
        mean=round(mean_ret, 8),
        std=round(std_ret, 8),
        skewness=round(skew_val, 4),
        kurtosis=round(kurt_val, 4),
        min_return=round(float(np.min(returns)), 6),
        max_return=round(float(np.max(returns)), 6),
        median=round(float(np.median(returns)), 8),
        percentile_1=round(float(np.percentile(returns, 1)), 6),
        percentile_5=round(float(np.percentile(returns, 5)), 6),
        percentile_95=round(float(np.percentile(returns, 95)), 6),
        percentile_99=round(float(np.percentile(returns, 99)), 6),
        tests=test_results,
        histogram=histogram,
    )


def _autocorrelation(x: np.ndarray, max_lag: int) -> dict[int, float]:
    """Calculate autocorrelation for given lags."""
    n = len(x)
    mean = np.mean(x)
    var = np.var(x)
    result = {}
    for lag in range(1, max_lag + 1):
        cov = np.sum((x[:n - lag] - mean) * (x[lag:] - mean)) / n
        result[lag] = float(cov / var) if var > 0 else 0
    return result
