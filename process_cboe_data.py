import os
import json
import requests
import pandas as pd
import boto3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_cboe_data(ticker):
    """
    Fetch delayed quotes data from CBOE API for a given ticker
    """
    # CBOE delayed quotes endpoint
    url = f"https://cdn.cboe.com/api/global/delayed_quotes/{ticker}.json"
    
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None

def process_ticker(ticker, s3_bucket):
    """
    Process a single ticker and upload results to S3
    """
    # Get data from CBOE API
    data = get_cboe_data(ticker)
    
    if not data:
        return
    
    # Extract last trade time from the correct path in JSON
    last_trade_time = data.get('data', {}).get('last_trade_time')
    if not last_trade_time:
        print(f"No last_trade_time found for {ticker}")
        return
    
    # Create DataFrame with the complete JSON data
    df = pd.DataFrame([{
        'ticker': ticker,
        'timestamp': data.get('timestamp'),
        'data': data.get('data'),  # This will store the entire data structure
        'raw_json': json.dumps(data)  # Backup of complete raw JSON
    }])
    
    # Format filename using ticker and last_trade_time from the data
    # Convert last_trade_time to a filename-friendly format
    formatted_time = last_trade_time.replace(':', '').replace('-', '').replace('T', '_')
    filename = f"{ticker}_{formatted_time}.parquet"
    
    # Save locally first (Lambda has /tmp available for temporary storage)
    df.to_parquet(f"/tmp/{filename}")
    
    # Upload to S3
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(
            f"/tmp/{filename}",
            s3_bucket,
            f"cboe_data/{ticker}/{filename}"
        )
        print(f"Successfully uploaded {filename} to S3")
    except Exception as e:
        print(f"Error uploading {filename} to S3: {str(e)}")
    
    # Clean up local file
    os.remove(f"/tmp/{filename}")

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    """
    # Get S3 bucket from environment variable
    s3_bucket = os.getenv('S3_BUCKET_NAME')
    if not s3_bucket:
        return {
            'statusCode': 500,
            'body': 'S3_BUCKET_NAME environment variable not set'
        }
    
    # Read tickers from file
    try:
        with open('ticker.txt', 'r') as f:
            # Strip comments and empty lines
            tickers = [line.split('#')[0].strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error reading ticker.txt: {str(e)}'
        }
    
    # Process each ticker
    processed_tickers = []
    failed_tickers = []
    for ticker in tickers:
        try:
            process_ticker(ticker, s3_bucket)
            processed_tickers.append(ticker)
        except Exception as e:
            print(f"Error processing ticker {ticker}: {str(e)}")
            failed_tickers.append(ticker)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(processed_tickers)} tickers',
            'processed': processed_tickers,
            'failed': failed_tickers
        })
    }

if __name__ == "__main__":
    lambda_handler(None, None)
