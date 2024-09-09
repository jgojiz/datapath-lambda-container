import os
from io import StringIO
import logging
import json

import pandas as pd
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def read_csv_from_s3(bucket_name, key) -> pd.DataFrame:
    # Download the CSV file from S3 to the /tmp directory
    local_path = '/tmp/' + os.path.basename(key)
    s3_client.download_file(bucket_name, key, local_path)
    
    # Load the data into a pandas DataFrame
    logger.info(f"Reading data from S3 bucket: {bucket_name}, key: {key}")
    data = pd.read_csv(local_path)
    
    logger.info(f"Data loaded successfully with {len(data)} records.")
    
    return data

def transform_data(data: pd.DataFrame) -> pd.DataFrame:
    
    # drop unneeded columns
    fraud = data.drop(columns=['trans_num', 'lat', 'long'])
    
    # rename columns
    fraud = fraud.rename(columns={'trans_date_trans_time': 'datetime', 'amt': 'transaction_amount', 
                              'dob': 'birth_date', 'city_pop': 'city_population'})
    
    # transform datetime data type
    datetime_format = '%d-%m-%Y %H:%M'
    fraud['datetime'] = pd.to_datetime(fraud['datetime'], format=datetime_format)  

    # create date and time columns
    fraud['date'] = fraud['datetime'].dt.strftime('%d/%m/%Y')
    fraud['time_24h'] = fraud['datetime'].dt.strftime('%H:%M') 

    logger.info(f"Data transformed successfully with {len(fraud)} records.")
    
    return fraud

def save_transformed_data_to_s3(data, bucket_name, output_key) -> bool:
    # Convert the DataFrame to CSV
    csv_buffer = StringIO()
    data.to_csv(csv_buffer, index=False)
    
    logger.info(f"Saving transformed data to S3 bucket: {bucket_name}, key: {output_key}")
    
    # Upload the CSV to S3
    try:
        s3_client.put_object(Bucket=bucket_name, Key=output_key, Body=csv_buffer.getvalue())
        logger.info(f"Transformed data successfully saved to S3 bucket: {bucket_name}, key: {output_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to save transformed data to S3: {str(e)}")
        return False

def lambda_handler(event, context):
    
    #print the event object received by Lambda
    # print("Received event: " + json.dumps(event, indent=2))

    # Extract the bucket name and file key from the S3 event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(f'key of source: ', key)

    # Read CSV data from S3
    data = read_csv_from_s3(bucket_name, key)

    # Apply transformations
    transformed_data = transform_data(data)
    
    # Define output S3 bucket and path
    output_bucket_name = 'serving-cc-fraud'  # New destination bucket
    output_key = os.path.basename(key)
    
    # Save the transformed data back to S3
    response = save_transformed_data_to_s3(transformed_data, output_bucket_name, output_key)
    
    if response:
        # Return the S3 path of the transformed data
        return {
            "statusCode": 200
        }
    else:
        return {
            "statusCode": 500
        }

if __name__ == "__main__":
    # dataset: https://www.kaggle.com/datasets/neharoychoudhury/credit-card-fraud-data/data
    data = transform_data('fraud_data.csv')
    print(data.shape)
