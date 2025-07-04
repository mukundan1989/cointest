import json
from lib.adf_test import adf_test # Import the pure Python ADF test
import requests
import csv
import io

def handler(event, context):
    """
    Vercel Serverless Function handler for the pure Python ADF test.
    Receives CSV URLs, fetches data, extracts prices, and performs ADF test.
    """
    try:
        # Parse the request body
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Request body is missing."})
            }
        
        request_data = json.loads(event['body'])
        tcs_url = request_data.get('tcs_url')
        hcl_url = request_data.get('hcl_url')
        lags = request_data.get('lags', 0) # Default lags to 0 for basic ADF

        if not tcs_url or not hcl_url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Missing TCS or HCLTECH CSV URLs"})
            }

        # Fetch and parse CSV data for TCS
        tcs_prices = fetch_prices_from_csv_url(tcs_url)
        if tcs_prices is None:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Failed to fetch or parse TCS.NS data."})
            }

        # Fetch and parse CSV data for HCLTECH
        hcl_prices = fetch_prices_from_csv_url(hcl_url)
        if hcl_prices is None:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Failed to fetch or parse HCLTECH.NS data."})
            }

        results = {}
        try:
            results['tcs'] = adf_test(tcs_prices, lags=lags)
        except ValueError as e:
            results['tcs'] = {"error": str(e)}
        except Exception as e:
            results['tcs'] = {"error": f"ADF test failed for TCS.NS: {str(e)}"}

        try:
            results['hcltech'] = adf_test(hcl_prices, lags=lags)
        except ValueError as e:
            results['hcltech'] = {"error": str(e)}
        except Exception as e:
            results['hcltech'] = {"error": f"ADF test failed for HCLTECH.NS: {str(e)}"}

        return {
            "statusCode": 200,
            "headers": {'Content-Type': 'application/json'},
            "body": json.dumps(results)
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

def fetch_prices_from_csv_url(url):
    """
    Fetches CSV data from a given URL and extracts prices.
    Assumes CSV format: Date, Symbol, Price (no header row).
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        csv_content = io.StringIO(response.text)

        reader = csv.reader(csv_content)
        prices = []
        for row in reader:
            if len(row) > 2: # Ensure row has at least 3 columns
                try:
                    price = float(row[2]) # Price is at index 2
                    prices.append(price)
                except ValueError:
                    # Skip rows with non-numeric price values
                    continue
        
        if not prices:
            return None # No valid numerical data found

        return prices
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing CSV data from {url}: {e}")
        return None
