# cboe-data-pipeline
A serverless pipeline that fetches JSON data from the CBOE delayed quotes API every 5 minutes, converts it to Parquet, and stores it in Amazon S3 with filenames reflecting the last trade time.
