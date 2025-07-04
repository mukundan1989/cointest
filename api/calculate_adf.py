# api/calculate_adf.py (Example for Vercel Python Serverless Function)

from http.server import BaseHTTPRequestHandler
import json
import numpy as np
from arch.unitroot import ADF
from datetime import datetime
import csv
from io import StringIO

# Re-use the data loading and ADF calculation functions from the previous script
# Make sure to handle input data from the request body

def load_close_prices_from_string(csv_content):
    """Loads and sorts close prices from a CSV content string without pandas."""
    dates = []
    prices = []
    reader = csv.reader(StringIO(csv_content))
    for row in reader:
        if row:
            try:
                date_obj = datetime.strptime(row[0], '%Y-%m-%d')
                close_price = float(row[5])
                dates.append(date_obj)
                prices.append(close_price)
            except (ValueError, IndexError):
                continue # Skip malformed rows

    # Sort by date
    sorted_indices = np.argsort(dates)
    sorted_dates = [dates[i] for i in sorted_indices]
    sorted_prices = np.array([prices[i] for i in sorted_indices])
    return sorted_dates, sorted_prices


def run_ols_and_adf_arch_api(tcs_csv_content, hcltech_csv_content, window=60):
    # This function will now take CSV content as strings
    tcs_dates, tcs_prices = load_close_prices_from_string(tcs_csv_content)
    hcltech_dates, hcltech_prices = load_close_prices_from_string(hcltech_csv_content)

    # Align data based on dates
    aligned_data = []
    tcs_dict = dict(zip(tcs_dates, tcs_prices))
    hcltech_dict = dict(zip(hcltech_dates, hcltech_prices))

    all_dates = sorted(list(set(tcs_dates).intersection(set(hcltech_dates))))

    for date in all_dates:
        if date in tcs_dict and date in hcltech_dict:
            aligned_data.append({
                'Date': date,
                'Close_TCS': tcs_dict[date],
                'Close_HCLTECH': hcltech_dict[date]
            })
    aligned_data.sort(key=lambda x: x['Date']) # Ensure sorted by date

    if len(aligned_data) < window:
        return {"error": f"Not enough aligned data points ({len(aligned_data)}) for a {window}-day window."}, None

    results = []
    last_adf_statistic = None

    for i in range(window - 1, len(aligned_data)):
        window_data = aligned_data[i - window + 1 : i + 1]

        y_hcltech = np.array([d['Close_HCLTECH'] for d in window_data])
        x_tcs = np.array([d['Close_TCS'] for d in window_data])

        X_ols = np.vstack([np.ones(len(x_tcs)), x_tcs]).T

        try:
            beta_hat, residuals_ols, rank, s = np.linalg.lstsq(X_ols, y_hcltech, rcond=None)
            alpha = beta_hat[0]
            beta = beta_hat[1]
        except np.linalg.LinAlgError:
            continue

        current_tcs_close = aligned_data[i]['Close_TCS']
        current_hcltech_close = aligned_data[i]['Close_HCLTECH']
        spread_value = current_hcltech_close - (alpha + beta * current_tcs_close)

        window_spreads = []
        for k in range(len(window_data)):
            window_spreads.append(window_data[k]['Close_HCLTECH'] - (alpha + beta * window_data[k]['Close_TCS']))

        spread_series = np.array(window_spreads)

        z_score = np.nan
        if len(spread_series) > 1:
            rolling_mean_spread = np.mean(spread_series)
            rolling_std_dev_spread = np.std(spread_series)
            if rolling_std_dev_spread != 0:
                z_score = (spread_value - rolling_mean_spread) / rolling_std_dev_spread

        adf_statistic = np.nan
        if len(spread_series) > 10 and not np.all(spread_series == spread_series[0]):
            try:
                adf_test = ADF(spread_series, lags=None, trend='c', max_lags=12, method='aic')
                adf_statistic = adf_test.stat
            except Exception:
                pass

        last_adf_statistic = adf_statistic

        results.append({
            'Date': aligned_data[i]['Date'].strftime('%Y-%m-%d'),
            'symbol1close': aligned_data[i]['Close_TCS'],
            'symbol2close': aligned_data[i]['Close_HCLTECH'],
            'Alpha (α)': alpha,
            'Hedge Ratio (β)': beta,
            'Spread': spread_value,
            'Z-score': z_score,
            'ADF Test Statistic': adf_statistic
        })

    return {"results": results, "last_adf_statistic": last_adf_statistic}, None


# Vercel Serverless Function entry point
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_body = self.rfile.read(content_length)
        data = json.loads(post_body)

        tcs_csv_content = data.get('tcs_csv_content')
        hcltech_csv_content = data.get('hcltech_csv_content')
        window = data.get('window', 60)

        if not tcs_csv_content or not hcltech_csv_content:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing CSV content in request"}).encode())
            return

        response_data, error = run_ols_and_adf_arch_api(tcs_csv_content, hcltech_csv_content, window)

        if error:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": error}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
