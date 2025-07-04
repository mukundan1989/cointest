# lib/adf_test.py – pure Python ADF test for Vercel or serverless

def mean(values):
    if not values:
        return 0
    return sum(values) / len(values)

def variance(values):
    if len(values) < 2:
        return 0
    m = mean(values)
    return sum((x - m) ** 2 for x in values)

def covariance(x, y):
    if len(x) != len(y) or not x:
        return 0
    xm = mean(x)
    ym = mean(y)
    return sum((xi - xm) * (yi - ym) for xi, yi in zip(x, y))

def ols_regression(x, y):
    if len(x) < 2 or variance(x) == 0:
        # Handle cases where regression is not possible (e.g., constant x)
        return 0, 0, [yi - mean(y) for yi in y] # alpha=mean(y), beta=0, residuals are just deviations from mean y

    beta = covariance(x, y) / variance(x)
    alpha = mean(y) - beta * mean(x)
    residuals = [yi - (alpha + beta * xi) for xi, yi in zip(x, y)]
    return alpha, beta, residuals

def standard_error(x, residuals):
    n = len(x)
    if n < 2: # Need at least 2 points for regression
        return float('inf') # Cannot calculate standard error
    
    sx = sum((xi - mean(x)) ** 2 for xi in x)
    if sx == 0: # Avoid division by zero if x is constant
        return float('inf')

    se2 = sum(r**2 for r in residuals) / (n - 2)
    if se2 < 0: # Should not happen with real numbers, but for robustness
        se2 = 0
    return (se2 / sx) ** 0.5

def get_critical_values(n):
    # Approximate critical values based on sample size
    # These are simplified approximations and not from a precise statistical table.
    # For more accurate values, a full statistical library is needed.
    if n <= 25:
        return {'1%': -3.75, '5%': -3.00, '10%': -2.63}
    elif n <= 50:
        return {'1%': -3.58, '5%': -2.93, '10%': -2.60}
    elif n <= 100:
        return {'1%': -3.50, '5%': -2.89, '10%': -2.58}
    else:
        return {'1%': -3.46, '5%': -2.88, '10%': -2.57}

def adf_test(series, lags=0):
    n = len(series)
    if n < 20: # Minimum recommended for ADF test
        raise ValueError("Series too short for ADF test (minimum 20 data points recommended).")
    if lags < 0:
        raise ValueError("Lags cannot be negative.")
    if lags >= n - 1:
        raise ValueError("Lags must be less than series length - 1.")

    # First differences (delta y_t)
    diff = [series[i] - series[i - 1] for i in range(1, n)]

    # Lagged levels (y_{t-1})
    y_lag = series[:-1]
    
    # Prepare data for regression: delta y_t = alpha + beta * y_{t-1} + sum(gamma_i * delta y_{t-i})
    # For simplicity, this pure Python version implements the basic ADF without lagged differences
    # unless 'lags' is used to truncate the series for the main regression.
    # A full ADF with lagged differences would be significantly more complex to implement from scratch.

    # Let's stick to the basic regression: dy = alpha + beta * y_lag
    # The `lags` parameter in the original `adf_test.py` was used to truncate.
    # We'll use it to ensure enough data points after differencing and potential truncation.
    
    if lags > 0:
        if len(diff) <= lags:
            raise ValueError("Not enough data points after differencing for specified lags.")
        y = diff[lags:]
        x = y_lag[lags:]
    else:
        y = diff
        x = y_lag

    if len(x) < 2:
        raise ValueError("Not enough data points for regression after differencing and lags.")

    alpha, beta, residuals = ols_regression(x, y)
    se = standard_error(x, residuals)
    
    if se == 0: # Avoid division by zero if standard error is zero (e.g., perfect fit)
        t_stat = float('inf') if beta != 0 else 0
    else:
        t_stat = beta / se
    
    crit = get_critical_values(n) # Use original series length for critical values

    return {
        "t_stat": round(t_stat, 4),
        "alpha": round(alpha, 4),
        "beta": round(beta, 4),
        "lag_used": lags,
        "critical_values": crit,
        "series_length": n
    }

# Example for test (not executed in serverless context)
if __name__ == "__main__":
    import random
    print("Running example test for adf_test.py")
    series = [0]
    for _ in range(100):
        series.append(series[-1] + random.gauss(0, 1))  # random walk
    try:
        result = adf_test(series)
        print("Random Walk ADF Result:", result)
    except ValueError as e:
        print(f"Error in random walk test: {e}")

    # Stationary series (e.g., white noise)
    stationary_series = [random.gauss(0, 1) for _ in range(100)]
    try:
        result_stationary = adf_test(stationary_series)
        print("Stationary Series ADF Result:", result_stationary)
    except ValueError as e:
        print(f"Error in stationary series test: {e}")
