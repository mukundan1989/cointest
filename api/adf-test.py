import requests
import io
import csv
import numpy as np
import json
from arch.unitroot import ADF # Import ADF from arch

def handler(event, context):
    try:
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
            'body': json.dumps(results)
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
        response.raise_for_status()
        csv_content = io.StringIO(response.text)

        reader = csv.reader(csv_content)
        prices = []
        for row in reader:
            if len(row) > 2:
                try:
                    price = float(row[2])
                    prices.append(price)
                except ValueError:
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
    """Performs the Augmented Dickey-Fuller test on a time series using arch and returns results."""
    if series is None or series.size == 0:
        return {"error": f"No valid price data for {stock_name} to perform ADF test."}

    try:
        # Use arch.unitroot.ADF
        # The default regression is 'c' (constant), which is common.
        # You can specify 'ct' (constant and trend) or 'ctt' (constant, trend, and quadratic trend)
        # if your data suggests it.
        adf = ADF(series) 
        
        p_value = adf.pvalue
        is_stationary = p_value <= 0.05

        conclusion = ""
        if is_stationary:
            conclusion = f"The p-value ({p_value:.4f}) is less than or equal to 0.05. We reject the null hypothesis."
            conclusion += f" Therefore, the time series for {stock_name} is likely stationary."
        else:
            conclusion = f"The p-value ({p_value:.4f}) is greater than 0.05. We fail to reject the null hypothesis."
            conclusion += f" Therefore, the time series for {stock_name} is likely non-stationary (has a unit root)."

        # arch.unitroot.ADF provides critical values directly
        critical_values = {
            '1%': f"{adf.critical_values['1%']:.4f}",
            '5%': f"{adf.critical_values['5%']:.4f}",
            '10%': f"{adf.critical_values['10%']:.4f}"
        }

        return {
            "stockName": stock_name,
            "adfStatistic": f"{adf.stat:.4f}", # Use adf.stat for the test statistic
            "pValue": f"{p_value:.4f}",
            "criticalValues": critical_values,
            "isStationary": is_stationary,
            "conclusion": conclusion
        }
    except Exception as e:
        return {"error": f"Error performing ADF test for {stock_name}: {str(e)}"}
