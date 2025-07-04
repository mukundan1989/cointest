import requests
from statsmodels.tsa.stattools import adfuller
import io
import csv
import numpy as np
import json # Import json for manual JSON parsing and serialization

# This is the entry point for Vercel Serverless Functions
# The 'event' parameter contains the request details (headers, body, etc.)
# The 'context' parameter contains environment information (not used here)
def handler(event, context):
    try:
        # Parse the incoming JSON body from the event
        # Vercel's event structure puts the request body in event['body']
        # and it's usually a string that needs to be parsed.
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Request body is missing."})
            }
        
        data = json.loads(event['body'])
        tcs_url = data.get('tcs_url')
        hcl_url = data.get('hcl_url')

        if not tcs_url or not hcl_url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Missing TCS or HCLTECH CSV URLs"})
            }

        tcs_prices = fetch_csv_data_no_pandas(tcs_url)
        hcl_prices = fetch_csv_data_no_pandas(hcl_url)

        results = {}
        if tcs_prices is not None:
            results['tcs'] = perform_adf_test_logic(tcs_prices, "TCS.NS")
        else:
            results['tcs'] = {"error": "Failed to fetch or process TCS.NS data."}

        if hcl_prices is not None:
            results['hcltech'] = perform_adf_test_logic(hcl_prices, "HCLTECH.NS")
        else:
            results['hcltech'] = {"error": "Failed to fetch or process HCLTECH.NS data."}

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(results) # Manually serialize results to JSON string
        }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Invalid JSON in request body."})
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Internal Server Error: {str(e)}"})
        }

def fetch_csv_data_no_pandas(url):
    """
    Fetches CSV data from a given URL and returns prices as a numpy array.
    Assumes CSV format: Date, Symbol, Price (no header row).
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        csv_content = io.StringIO(response.text)

        reader = csv.reader(csv_content)
        prices = []
        for row in reader:
            # Assuming price is the third column (index 2)
            if len(row) > 2:
                try:
                    price = float(row[2])
                    prices.append(price)
                except ValueError:
                    # Skip rows with non-numeric price values
                    print(f"Skipping non-numeric price value: {row[2]}")
                    continue
        
        if not prices:
            print(f"No valid numerical data found for URL: {url}")
            return None

        return np.array(prices)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing CSV data from {url}: {e}")
        return None

def perform_adf_test_logic(series, stock_name):
    """Performs the Augmented Dickey-Fuller test on a time series and returns results."""
    if series is None or series.size == 0:
        return {"error": f"No valid price data for {stock_name} to perform ADF test."}

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
