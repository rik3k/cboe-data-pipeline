# CBOE Data Pipeline

A containerized AWS Lambda function that processes CBOE delayed quotes data and stores it in S3 as parquet files. This pipeline fetches market data for specified indices (SPX, VIX, NDX) and preserves the complete data structure in an easily queryable format.

## Data Structure

The CBOE delayed quotes API returns data in the following structure:

```json
{
    "timestamp": "2024-11-21 01:52:50",
    "data": {
        "options": [
            {
                "option": "SPX241220C00200000",
                "bid": 5691.1,
                "bid_size": 2.0,
                "ask": 5698.4,
                "ask_size": 2.0,
                "iv": 4.1223,
                "open_interest": 5288.0,
                "volume": 1.0,
                "delta": 1.0,
                "gamma": 0.0,
                "vega": 0.0009,
                "theta": 0.0,
                "rho": 0.1767,
                "theo": 5694.189,
                "change": -19.38,
                "open": 5689.92,
                "high": 5689.92,
                "low": 5689.92,
                "tick": "up",
                "last_trade_price": 5689.92,
                "last_trade_time": "2024-11-20T12:06:25",
                "percent_change": -0.339447,
                "prev_day_close": 5709.30004882812
            }
            // ... more options
        ],
        "symbol": "^SPX",
        "security_type": "index",
        "exchange_id": 5,
        "current_price": 5917.1099,
        "price_change": 0.1299,
        "price_change_percent": 0.0022,
        "bid": 5872.3999,
        "ask": 5978.3398,
        "bid_size": 1,
        "ask_size": 1,
        "open": 5914.3398,
        "high": 5920.6699,
        "low": 5860.5601,
        "close": 5917.1099,
        "prev_day_close": 5917.1099,
        "volume": 0,
        "iv30": 13.373,
        "iv30_change": 0.0,
        "iv30_change_percent": 0.0,
        "seqno": 25163915812,
        "last_trade_time": "2024-11-20T16:14:59",
        "tick": "down"
    },
    "symbol": "_SPX"
}
```

## Prerequisites

- AWS Account with appropriate permissions
- Docker installed locally
- Access to CBOE delayed quotes API (public access)

## Project Structure

```
cboe-data-pipeline/
├── process_cboe_data.py    # Main Lambda function
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── ticker.txt            # List of indices to process
└── .env                  # Environment variables
```

## Environment Variables

Create a `.env` file with:
```
# AWS Configuration
S3_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1  # Change to your desired region

# Optional: Lambda Configuration
LAMBDA_MEMORY=512
LAMBDA_TIMEOUT=300  # 5 minutes in seconds
```

## Ticker Configuration

Edit `ticker.txt` to specify which indices to process. The file supports comments:
```
# Verify tickers here: https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json
# Major Indices
_SPX    # S&P 500 Index
_VIX    # CBOE Volatility Index
_NDX    # Nasdaq 100 Index
```

## Output Format

### S3 Storage Structure
```
s3://your-bucket/
└── cboe_data/
    ├── _SPX/
    │   └── _SPX_20241120_161459.parquet
    ├── _VIX/
    │   └── _VIX_20241120_161502.parquet
    └── _NDX/
        └── _NDX_20241120_161505.parquet
```

### Parquet File Structure
Each parquet file contains:
- `ticker`: Index symbol
- `timestamp`: API response timestamp
- `data`: Complete nested data structure including:
  - Options chain data
  - Current market data
  - Trading metrics
- `raw_json`: Backup of complete JSON response

## Setup and Deployment

1. Build the Docker container:
```bash
docker build -t cboe-data-pipeline .
```

2. Tag and push to Amazon ECR:
```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag cboe-data-pipeline:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cboe-data-pipeline:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cboe-data-pipeline:latest
```

3. Create Lambda Function:
   - Create new function from container image
   - Set environment variables
   - Configure memory and timeout
   - Set up IAM role with S3 write permissions

## IAM Policy Requirements

The Lambda function needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## Error Handling

The script includes error handling for:
- API connection issues
- Missing or invalid data
- S3 upload failures
- File system operations

Failed operations are logged and reported in the Lambda function response.
