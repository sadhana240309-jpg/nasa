"""
TerraScope Scientific Statistical Analysis Engine.

Implements rigorous non-parametric trend detection and multi-hypothesis correction:
- Mann-Kendall Trend Test with tie corrections
- Sen's Slope Estimator
- Temporal scaling to Annual Rate of Change
- Variability Normalization (Relative % change / year and Standardized Slope)
- False Discovery Rate (FDR) Multi-Testing Correction via Benjamini-Hochberg
- Ranked environmental trend discovery across heterogeneous variables
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from pydantic import BaseModel


class StatisticalResult(BaseModel):
    variable_code: str
    variable_name: str
    official_source_name: str
    trend_direction: str  # "Increasing trend" | "Decreasing trend" | "No statistically significant trend"
    sens_slope: float
    annual_rate_of_change: float
    original_measurement_unit: str
    p_value: float
    fdr_adjusted_p_value: float
    is_statistically_significant: bool
    kendall_tau: float
    z_score: float
    s_statistic: float
    valid_observations_count: int
    total_observations_count: int
    missing_observations_count: int
    data_coverage_period: str
    coverage_ratio: float
    relative_annual_change_pct: float
    standardized_slope: float
    intercept: float
    confidence_interval_95: Tuple[float, float]
    fitted_trend_line: List[Dict[str, Any]]
    scientific_summary: str


def compute_mann_kendall(
    values: np.ndarray,
    times: np.ndarray,
    temporal_frequency: str = "monthly",  # "monthly", "annual", "daily", "sporadic"
) -> Dict[str, Any]:
    """
    Computes the Mann-Kendall test statistic and Sen's slope estimator.
    
    Args:
        values: 1D array of observed values (finite floats, NaNs removed).
        times: 1D array of time steps (numerical years or fractional years).
        temporal_frequency: "monthly", "annual", "daily", or "sporadic".
        
    Returns:
        Dictionary with statistical metrics.
    """
    n = len(values)
    if n < 6:
        raise ValueError(f"Insufficient valid observations (n={n}) for Mann-Kendall test. Minimum required is 6.")

    # Calculate Kendall's S statistic
    # S = sum_{k=1}^{n-1} sum_{j=k+1}^n sgn(x_j - x_k)
    s = 0.0
    slopes = []
    
    for k in range(n - 1):
        diff_vals = values[k + 1 :] - values[k]
        diff_times = times[k + 1 :] - times[k]
        
        # Mann-Kendall signs
        s += np.sum(np.sign(diff_vals))
        
        # Sen's slopes
        valid_time_diff = diff_times != 0
        if np.any(valid_time_diff):
            slopes.extend(diff_vals[valid_time_diff] / diff_times[valid_time_diff])

    # Tie corrections for variance of S
    # Count identical values
    unique_vals, counts = np.unique(values, return_counts=True)
    tie_term = np.sum(counts * (counts - 1) * (2 * counts + 5))
    
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    
    # Calculate Z statistic with continuity correction
    if s > 0:
        z = (s - 1.0) / np.sqrt(var_s) if var_s > 0 else 0.0
    elif s < 0:
        z = (s + 1.0) / np.sqrt(var_s) if var_s > 0 else 0.0
    else:
        z = 0.0

    # Two-tailed p-value from standard normal distribution
    p_value = float(2.0 * stats.norm.sf(np.abs(z)))
    
    # Kendall's tau
    tau = float(s / (0.5 * n * (n - 1)))

    # Sen's slope: median of all pairwise slopes
    if len(slopes) > 0:
        sen_slope = float(np.median(slopes))
        # 95% Confidence Interval for Sen's Slope
        k_ci = int(np.round(1.96 * np.sqrt(var_s)))
        slopes_sorted = np.sort(slopes)
        m = len(slopes_sorted)
        idx_lower = max(0, int((m - k_ci) / 2))
        idx_upper = min(m - 1, int((m + k_ci) / 2))
        ci_lower = float(slopes_sorted[idx_lower])
        ci_upper = float(slopes_sorted[idx_upper])
    else:
        sen_slope = 0.0
        ci_lower = 0.0
        ci_upper = 0.0

    # Intercept = median(values - sen_slope * times)
    intercept = float(np.median(values - sen_slope * times))

    # Annual rate of change:
    # If `times` is already in years (e.g. 2015.0, 2015.0833...), sen_slope is directly change per year!
    annual_rate = sen_slope

    # Variability Normalization
    mean_val = float(np.mean(values))
    std_val = float(np.std(values)) if np.std(values) > 0 else 1.0
    
    # Relative percentage change per year
    if abs(mean_val) > 1e-6:
        rel_annual_pct = float((annual_rate / abs(mean_val)) * 100.0)
    else:
        rel_annual_pct = float(annual_rate * 100.0)

    # Standardized slope (Z-slope per year)
    standardized_slope = float(annual_rate / std_val)

    return {
        "s": float(s),
        "var_s": float(var_s),
        "z": float(z),
        "p_value": p_value,
        "tau": tau,
        "sen_slope": sen_slope,
        "annual_rate_of_change": annual_rate,
        "intercept": intercept,
        "ci_95": (ci_lower, ci_upper),
        "mean_val": mean_val,
        "std_val": std_val,
        "relative_annual_change_pct": rel_annual_pct,
        "standardized_slope": standardized_slope,
    }


def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Applies the Benjamini-Hochberg (BH) False Discovery Rate (FDR) procedure
    for multiple hypothesis testing correction across discovered variables.
    
    Args:
        p_values: List of raw p-values from each variable's Mann-Kendall test.
        alpha: Nominal false discovery rate threshold (default 0.05).
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags)
    """
    m = len(p_values)
    if m == 0:
        return [], []
    if m == 1:
        p_adj = min(1.0, p_values[0])
        return [p_adj], [p_adj < alpha]

    # Convert to numpy array with original indices
    p_arr = np.array(p_values, dtype=float)
    sort_indices = np.argsort(p_arr)
    sorted_p = p_arr[sort_indices]

    # Calculate Benjamini-Hochberg adjusted p-values
    # p_adj(i) = min(1, min_{k >= i} (m / k * p(k)))
    ranks = np.arange(1, m + 1)
    adjusted_factors = sorted_p * (m / ranks)
    
    # Cumulative minimum from the right
    cummin = np.minimum.accumulate(adjusted_factors[::-1])[::-1]
    adjusted_sorted = np.clip(cummin, 0.0, 1.0)

    # Map back to original order
    adjusted_p_values = np.empty(m, dtype=float)
    adjusted_p_values[sort_indices] = adjusted_sorted

    significant = adjusted_p_values < alpha
    return adjusted_p_values.tolist(), significant.tolist()


def rank_and_analyze_variables(
    variable_series_list: List[Dict[str, Any]],
    alpha: float = 0.05
) -> List[StatisticalResult]:
    """
    Performs full multi-variable trend discovery across all retrieved variables:
    1. Validates observations & coverage.
    2. Runs Mann-Kendall test & Sen's slope estimator.
    3. Computes variability normalizations.
    4. Applies False Discovery Rate (FDR) correction across all tests.
    5. Classifies trend directions.
    6. Produces fitted trend lines and plain-language scientific summaries.
    7. Ranks variables by absolute standardized rate of change and statistical significance.
    """
    preliminary_results = []
    raw_p_values = []

    for item in variable_series_list:
        v_code = item["variable_code"]
        v_name = item["variable_name"]
        source_name = item["official_source_name"]
        unit = item["measurement_units"]
        dates = item["dates"]  # List of "YYYY-MM" or "YYYY-MM-DD"
        raw_values = item["values"]  # List of float or None
        
        # Check temporal coverage
        total_obs = len(raw_values)
        
        # Filter valid observations (exclude None and NaN)
        valid_pairs = [
            (i, d, val) for i, (d, val) in enumerate(zip(dates, raw_values))
            if val is not None and not np.isnan(val)
        ]
        valid_obs = len(valid_pairs)
        missing_obs = total_obs - valid_obs
        coverage_ratio = valid_obs / total_obs if total_obs > 0 else 0.0
        
        if len(dates) > 0:
            coverage_period = f"{dates[0]} to {dates[-1]}"
        else:
            coverage_period = "N/A"

        # Check minimum observation requirement
        if valid_obs < 6:
            # Insufficient observations for statistically valid trend test
            result = StatisticalResult(
                variable_code=v_code,
                variable_name=v_name,
                official_source_name=source_name,
                trend_direction="Insufficient observations (<6)",
                sens_slope=0.0,
                annual_rate_of_change=0.0,
                original_measurement_unit=unit,
                p_value=1.0,
                fdr_adjusted_p_value=1.0,
                is_statistically_significant=False,
                kendall_tau=0.0,
                z_score=0.0,
                s_statistic=0.0,
                valid_observations_count=valid_obs,
                total_observations_count=total_obs,
                missing_observations_count=missing_obs,
                data_coverage_period=coverage_period,
                coverage_ratio=coverage_ratio,
                relative_annual_change_pct=0.0,
                standardized_slope=0.0,
                intercept=0.0,
                confidence_interval_95=(0.0, 0.0),
                fitted_trend_line=[],
                scientific_summary=f"Insufficient valid data points ({valid_obs}/{total_obs}) to perform a mathematically valid Mann-Kendall trend test."
            )
            preliminary_results.append(result)
            raw_p_values.append(1.0)
            continue

        # Convert dates to fractional decimal years for proper physical scaling
        decimal_years = []
        clean_vals = []
        for _, d_str, val in valid_pairs:
            try:
                # Handle YYYY-MM-DD or YYYY-MM or YYYY
                parts = d_str.split("-")
                year = float(parts[0])
                month = float(parts[1]) if len(parts) > 1 else 1.0
                day = float(parts[2]) if len(parts) > 2 else 1.0
                dec_yr = year + (month - 1) / 12.0 + (day - 1) / 365.25
            except Exception:
                dec_yr = float(len(decimal_years))
            decimal_years.append(dec_yr)
            clean_vals.append(float(val))

        vals_arr = np.array(clean_vals, dtype=float)
        years_arr = np.array(decimal_years, dtype=float)

        stats_dict = compute_mann_kendall(vals_arr, years_arr)
        raw_p_values.append(stats_dict["p_value"])

        # Compute fitted trend line points across the date span
        fitted_line = []
        for i, (orig_idx, d_str, _) in enumerate(valid_pairs):
            t_val = years_arr[i]
            y_fit = float(stats_dict["intercept"] + stats_dict["sen_slope"] * t_val)
            fitted_line.append({
                "date": d_str,
                "fitted_value": round(y_fit, 4)
            })

        preliminary_results.append({
            "variable_code": v_code,
            "variable_name": v_name,
            "official_source_name": source_name,
            "unit": unit,
            "total_obs": total_obs,
            "valid_obs": valid_obs,
            "missing_obs": missing_obs,
            "coverage_period": coverage_period,
            "coverage_ratio": coverage_ratio,
            "stats": stats_dict,
            "fitted_line": fitted_line,
        })

    # Apply Benjamini-Hochberg FDR correction across all variables
    adj_p_values, sig_flags = apply_fdr_correction(raw_p_values, alpha=alpha)

    final_results: List[StatisticalResult] = []

    for i, item in enumerate(preliminary_results):
        if isinstance(item, StatisticalResult):
            final_results.append(item)
            continue

        stats_dict = item["stats"]
        p_val = stats_dict["p_value"]
        p_adj = adj_p_values[i]
        is_sig = sig_flags[i]
        sen_slope = stats_dict["sen_slope"]
        annual_rate = stats_dict["annual_rate_of_change"]
        unit = item["unit"]
        v_name = item["variable_name"]
        source_name = item["official_source_name"]

        # Classify trend direction
        if is_sig:
            if annual_rate > 0:
                direction = "Increasing trend"
            else:
                direction = "Decreasing trend"
        else:
            direction = "No statistically significant trend"

        # Construct scientific plain-language summary
        direction_word = "increasing" if annual_rate > 0 else "decreasing"
        abs_rate = abs(annual_rate)
        rel_pct = stats_dict["relative_annual_change_pct"]
        
        if is_sig:
            summary = (
                f"{v_name} from {source_name} exhibits a statistically significant {direction_word} trend "
                f"(Sen's slope = {annual_rate:+.4f} {unit}/year, relative change = {rel_pct:+.2f}%/yr, "
                f"Kendall's tau = {stats_dict['tau']:.3f}, p_adj = {p_adj:.4e} < {alpha}). "
                f"The trend was confirmed under False Discovery Rate (FDR) control across {len(preliminary_results)} "
                f"tested variables over {item['coverage_period']}."
            )
        else:
            summary = (
                f"{v_name} from {source_name} shows no statistically significant monotonic trend "
                f"(Sen's slope = {annual_rate:+.4f} {unit}/year, Kendall's tau = {stats_dict['tau']:.3f}, "
                f"raw p = {p_val:.4f}, p_adj = {p_adj:.4f} >= {alpha}). Natural inter-annual variability "
                f"dominates the observed time series."
            )

        stat_res = StatisticalResult(
            variable_code=item["variable_code"],
            variable_name=v_name,
            official_source_name=source_name,
            trend_direction=direction,
            sens_slope=round(sen_slope, 5),
            annual_rate_of_change=round(annual_rate, 5),
            original_measurement_unit=unit,
            p_value=round(p_val, 6),
            fdr_adjusted_p_value=round(p_adj, 6),
            is_statistically_significant=is_sig,
            kendall_tau=round(stats_dict["tau"], 4),
            z_score=round(stats_dict["z"], 4),
            s_statistic=round(stats_dict["s"], 2),
            valid_observations_count=item["valid_obs"],
            total_observations_count=item["total_obs"],
            missing_observations_count=item["missing_obs"],
            data_coverage_period=item["coverage_period"],
            coverage_ratio=round(item["coverage_ratio"], 4),
            relative_annual_change_pct=round(rel_pct, 2),
            standardized_slope=round(stats_dict["standardized_slope"], 4),
            intercept=round(stats_dict["intercept"], 4),
            confidence_interval_95=(round(stats_dict["ci_95"][0], 5), round(stats_dict["ci_95"][1], 5)),
            fitted_trend_line=item["fitted_line"],
            scientific_summary=summary,
        )
        final_results.append(stat_res)

    # Rank results:
    # 1. Statistically significant trends first (True before False)
    # 2. Then by descending absolute standardized slope (magnitude of change normalized by variability)
    # 3. Then by ascending adjusted p-value
    final_results.sort(
        key=lambda r: (
            1 if r.is_statistically_significant else 0,
            abs(r.standardized_slope) if r.is_statistically_significant else -r.fdr_adjusted_p_value
        ),
        reverse=True
    )

    return final_results
