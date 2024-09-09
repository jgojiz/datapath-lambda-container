# datapath-lambda-container
Python image for a lambda function triggered by S3 event. 
Retrieves S3 object key, to store the file in Lambda's temp folder,
then process it. Finally, stores the transformed data into another S3 bucket.
Uses a python 3.12 image with logging module to monitor in CloudWatch.
