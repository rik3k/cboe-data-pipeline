# CBOE Data Pipeline

A serverless pipeline that fetches JSON data from the CBOE delayed quotes API every 5 minutes, converts it to Parquet, and stores it in Amazon S3 using AWS Lambda.

## Overview

This pipeline fetches delayed quotes data for market indices (e.g., SPX, VIX, NDX) and other tickers via CBOE's public API. While currently configured to handle these indices, it can be easily adapted to fetch data for other tickers as needed. The data is stored in Parquet format for efficient querying and analysis.

## Data Source

The pipeline uses CBOE's delayed quotes API. Note that CBOE requires an underscore (_) prefix before each ticker symbol for indices:
```
https://cdn.cboe.com/api/global/delayed_quotes/{ticker}.json
```

Example endpoints:
- SPX: https://cdn.cboe.com/api/global/delayed_quotes/_SPX.json
- VIX: https://cdn.cboe.com/api/global/delayed_quotes/_VIX.json
- NDX: https://cdn.cboe.com/api/global/delayed_quotes/_NDX.json
- TSLA: https://cdn.cboe.com/api/global/delayed_quotes/TSLA.json

## JSON Data Structure

The API returns comprehensive market data in the following structure:

```json
{
    "timestamp": "2024-11-21 01:52:50",
    "data": {
        "options": [
            {
                "option": "SPX241220C00200000",  // Option contract identifier
                "bid": 5691.1,                   // Bid price
                "bid_size": 2.0,                 // Bid size
                "ask": 5698.4,                   // Ask price
                "ask_size": 2.0,                 // Ask size
                "iv": 4.1223,                    // Implied volatility
                "open_interest": 5288.0,         // Open interest
                "volume": 1.0,                   // Trading volume
                "delta": 1.0,                    // Delta
                "gamma": 0.0,                    // Gamma
                "vega": 0.0009,                  // Vega
                "theta": 0.0,                    // Theta
                "rho": 0.1767,                   // Rho
                "theo": 5694.189,                // Theoretical price
                "change": -19.38,                // Price change
                "open": 5689.92,                 // Opening price
                "high": 5689.92,                 // High price
                "low": 5689.92,                  // Low price
                "tick": "up",                    // Tick direction
                "last_trade_price": 5689.92,     // Last trade price
                "last_trade_time": "2024-11-20T12:06:25",  // Last trade timestamp
                "percent_change": -0.339447,     // Percent change
                "prev_day_close": 5709.30004882812  // Previous day's closing price
            }
            // ... more options
        ],
        "symbol": "^SPX",                    // Index symbol
        "security_type": "index",            // Security type
        "exchange_id": 5,                    // Exchange identifier
        "current_price": 5917.1099,          // Current index price
        "price_change": 0.1299,              // Price change
        "price_change_percent": 0.0022,      // Price change percentage
        "bid": 5872.3999,                    // Index bid price
        "ask": 5978.3398,                    // Index ask price
        "bid_size": 1,                       // Index bid size
        "ask_size": 1,                       // Index ask size
        "open": 5914.3398,                   // Opening price
        "high": 5920.6699,                   // High price
        "low": 5860.5601,                    // Low price
        "close": 5917.1099,                  // Closing price
        "prev_day_close": 5917.1099,         // Previous day's close
        "volume": 0,                         // Trading volume
        "iv30": 13.373,                      // 30-day implied volatility
        "iv30_change": 0.0,                  // IV change
        "iv30_change_percent": 0.0,          // IV change percentage
        "seqno": 25163915812,               // Sequence number
        "last_trade_time": "2024-11-20T16:14:59",  // Last trade timestamp
        "tick": "down"                       // Tick direction
    },
    "symbol": "_SPX"                         // Index symbol
}
```

## Project Structure

```
cboe-data-pipeline/
├── process_cboe_data.py    # Main Lambda function
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── ticker.txt            # List of indices to process
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
└── README.md            # Documentation
```

## Configuration

### Environment Variables (.env)
```bash
# AWS Configuration
S3_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1  # Change to your desired region
```

### Ticker Configuration (ticker.txt)
```bash
# Verify tickers here: https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json
# Add any desired tickers to this file, ensuring to prefix each with an underscore (_)
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
    │   └── _SPX_20241120_161459.parquet   # {ticker}_{last_trade_time}.parquet
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
  - Options chain data (strikes, greeks, prices)
  - Current market data (price, volume, changes)
  - Trading metrics (IV, volume, tick)
- `raw_json`: Backup of complete JSON response

## Prerequisites

- AWS Account with appropriate permissions
- Docker installed locally
- Access to CBOE delayed quotes API (public access)
- Python 3.9+

## Setup and Deployment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cboe-data-pipeline.git
cd cboe-data-pipeline
```

2. Configure environment:
   - Copy `.env.example` to `.env`
   - Set your AWS S3 bucket and region

3. Build the Docker container:
```bash
docker build -t cboe-data-pipeline .
```

4. Tag and push to Amazon ECR:
```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag cboe-data-pipeline:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cboe-data-pipeline:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cboe-data-pipeline:latest
```

5. Create Lambda Function:
   - Create new function from container image
   - Set environment variables from `.env`
   - Configure IAM role with S3 permissions

6. Configure Lambda Trigger:
   - Add EventBridge (CloudWatch Events) trigger
   - Set schedule to run every 5 minutes
   - Enable trigger

## IAM Policy Requirements

The Lambda function requires these permissions:
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

The pipeline includes comprehensive error handling for:
- API connection issues
- Missing or invalid data
- S3 upload failures
- File system operations

All errors are:
- Logged to CloudWatch Logs
- Included in Lambda function response
- Tracked per-ticker for detailed monitoring

## Monitoring

Monitor the pipeline using:
- CloudWatch Logs for Lambda execution logs
- CloudWatch Metrics for Lambda metrics
- S3 bucket monitoring for storage metrics
- Lambda function responses for per-ticker success/failure

## Data Usage

The stored parquet files can be analyzed using:
- Amazon Athena for SQL queries
- AWS Glue for ETL jobs
- Python pandas for local analysis
- Any tool supporting parquet format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
