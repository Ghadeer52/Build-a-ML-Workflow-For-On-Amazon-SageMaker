"""the first lambda function"""
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the S3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']
    
    # Download the data from S3 to /tmp/image.png
    s3.download_file(bucket, key, '/tmp/image.png')
    
    # Read the data from a file and base64 encode it
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')  # Ensure it's decoded for readability
    
    # Pass the data back as a Python dictionary
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []  # Placeholder for inferences
        }
    }


"""the second lambda function"""
import io
import boto3
import json
import base64

# setting the environment variables
ENDPOINT_NAME = 'image-classification-2024-09-21-07-32-12-269'
runtime = boto3.client('sagemaker-runtime')
def lambda_handler(event, context):

    # Log the received event structure for debugging purposes
    print(f"Received event: {json.dumps(event)}")

    # Decode the image data (Note: no "body" key in the event)
    image = base64.b64decode(event["image_data"])

    # Make a prediction
    predictor = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType='application/x-image',
        Body=image
    )

    # Add inferences to the event
    event["inferences"] = json.loads(predictor['Body'].read().decode('utf-8'))
    
    # Return the data back to the Step Function
    return {
        'statusCode': 200,
        'body': {
            "image_data": event['image_data'],
            "s3_bucket": event['s3_bucket'],
            "s3_key": event['s3_key'],
            "inferences": event['inferences'],
        }
    }


"""the thierd lambda function"""
import json

# Define the threshold
THRESHOLD = 0.95  # Adjust this threshold based on your requirements

def lambda_handler(event, context):
    # Extract inferences from the event body
    inferences = event["inferences"]

    # Check if any value in inferences exceeds the threshold
    meets_threshold = any(inference >= THRESHOLD for inference in inferences)

    # If the threshold is met, return the event
    if meets_threshold:
        return {
            'statusCode': 200,
            'body': json.dumps(event)
        }
    else:
        # Raise an error if no inference meets the threshold
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")

