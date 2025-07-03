from flask import Flask, request, jsonify
import pandas as pd
import requests
from statsmodels.tsa.stattools import adfuller
import io

app = Flask(__name__)

def fetch_csv_data(url):
    """Fetches CSV data from a given URL and returns it as a pandas DataFrame."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        csv_content = io.StringIO(response.text)
        # Assuming no header, and columns are Date, Symbol, Price
        df = pd.read_csv(csv_content, header=None, names=['Date', 'Symbol', 'Price'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce') # Coerce errors to NaN
        df.dropna(subset=['Price'], inplace=True) # Drop rows where price is NaN
        df = df.sort_values(by='Date') # Ensure data is sorted by date
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing CSV data from {url}: {e}")
        return None

def perform_adf_test_logic(series, stock_name):
    """Performs the Augmented Dickey-Fuller test on a time series and returns results."""
    if series.empty:
        return {"error": f"No valid price data for {stock_name}."}

    try:
        result = adfuller(series)
        p_value = result[1]
        is_stationary = p_value <= 0.05

        conclusion = ""
        if is_stationary:
            conclusion = f"The p-value ({p_value:.4f}) is less than or equal to 0.05. We reject the null hypothesis. Therefore, the time series for {stock_name} is likely stationary."
        else:
            conclusion = f"The p-value ({p_value:.4f}) is greater than 0.05. We fail to reject the null hypothesis. Therefore, the time series for {stock_name} is likely non-stationary (has a unit root)."

        return {
            "stockName": stock_name,
            "adfStatistic": f"{result[0]:.4f}",
            "pValue": f"{p_value:.4f}",
            "criticalValues": {k: f"{v:.4f}" for k, v in result[4].items()},
            "isStationary": is_stationary,
            "conclusion": conclusion
        }
    except Exception as e:
        return {"error": f"Error performing ADF test for {stock_name}: {str(e)}"}

@app.route('/api/adf-test', methods=['POST'])
def adf_test_endpoint():
    data = request.get_json()
    tcs_url = data.get('tcs_url')
    hcl_url = data.get('hcl_url')

    if not tcs_url or not hcl_url:
        return jsonify({"error": "Missing TCS or HCLTECH CSV URLs"}), 400

    tcs_df = fetch_csv_data(tcs_url)
    hcl_df = fetch_csv_data(hcl_url)

    results = {}
    if tcs_df is not None:
        results['tcs'] = perform_adf_test_logic(tcs_df['Price'], "TCS.NS")
    else:
        results['tcs'] = {"error": "Failed to fetch or process TCS.NS data."}

    if hcl_df is not None:
        results['hcltech'] = perform_adf_test_logic(hcl_df['Price'], "HCLTECH.NS")
    else:
        results['hcltech'] = {"error": "Failed to fetch or process HCLTECH.NS data."}

    return jsonify(results)

# This block is for local development only. Vercel handles routing in production.
if __name__ == '__main__':
    app.run(debug=True, port=5328)
