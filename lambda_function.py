import json
import run_pipeline
import boto3

def lambda_handler(event, context):
    print("Lambda started! Event:", event)
    
    if 'requestContext' in event:
        # This is a synchronous call from API Gateway. Invoke self asynchronously and return immediately.
        lmbda = boto3.client('lambda', region_name='us-east-1')
        async_event = event.copy()
        del async_event['requestContext'] # Remove this so next invocation knows it's the async worker
        lmbda.invoke(
            FunctionName=context.function_name,
            InvocationType='Event',
            Payload=json.dumps(async_event)
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Agent pipeline started asynchronously. Result will appear in Box.'})
        }
        
    # Extract goal from API Gateway POST body, or use default
    goal = event.get('goal')
    if not goal and 'body' in event:
        try:
            body = json.loads(event['body'])
            goal = body.get('goal')
        except:
            pass
            
    if not goal:
        goal = (
            "We need to find 1 highly qualified STEM or robotics grant in Washington State. "
            "Use apify_search to find candidates. Read their summaries. "
            "Then extract the data of the best candidate. "
            "If it is a 'single-grant' or 'potential-sponsor', draft an email for it. "
            "Stop once you have successfully drafted up to 5 emails."
        )
        
    print("Running pipeline with goal:", goal)
    
    # Run the Bedrock autonomous agent
    run_pipeline.run_agent(goal)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Agent pipeline finished successfully.'})
    }
