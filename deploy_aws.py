import boto3
import json
import time
import os

iam = boto3.client('iam')
lmbda = boto3.client('lambda')
apigw = boto3.client('apigatewayv2')

ROLE_NAME = 'ReachForwardLambdaRole'
LAMBDA_NAME = 'reach_forward_agent'
API_NAME = 'ReachForwardAPI'

print("Starting deployment...")

# 1. Create IAM Role
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow"}]
}
try:
    role = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
    role_arn = role['Role']['Arn']
    print("Created role:", role_arn)
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')
    
    # Inline policy for Bedrock and SSM
    inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": ["bedrock:InvokeModel", "bedrock:Converse"], "Resource": "*"},
            {"Effect": "Allow", "Action": ["ssm:GetParameter", "ssm:PutParameter"], "Resource": "*"}
        ]
    }
    iam.put_role_policy(RoleName=ROLE_NAME, PolicyName='ReachForwardInlinePolicy', PolicyDocument=json.dumps(inline_policy))
    print("Sleeping 10s for IAM propagation...")
    time.sleep(10)
except Exception as e:
    if 'EntityAlreadyExists' in str(e):
        role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
        print("Role already exists:", role_arn)
    else:
        raise

# 2. Create Lambda
with open('deploy_package.zip', 'rb') as f:
    zipped_code = f.read()

try:
    res = lmbda.create_function(
        FunctionName=LAMBDA_NAME,
        Runtime='python3.12',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zipped_code},
        Timeout=300,
        MemorySize=512
    )
    lambda_arn = res['FunctionArn']
    print("Created Lambda:", lambda_arn)
except Exception as e:
    if 'ResourceConflictException' in str(e):
        res = lmbda.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zipped_code)
        lmbda.update_function_configuration(FunctionName=LAMBDA_NAME, Timeout=300, MemorySize=512)
        lambda_arn = lmbda.get_function(FunctionName=LAMBDA_NAME)['Configuration']['FunctionArn']
        print("Updated existing Lambda:", lambda_arn)
    else:
        print("Retrying lambda creation in 5s due to:", str(e))
        time.sleep(5)
        res = lmbda.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime='python3.12',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zipped_code},
            Timeout=300,
            MemorySize=512
        )
        lambda_arn = res['FunctionArn']
        print("Created Lambda:", lambda_arn)

# 3. Create API Gateway
try:
    api = apigw.create_api(Name=API_NAME, ProtocolType='HTTP')
    api_id = api['ApiId']
    api_endpoint = api['ApiEndpoint']
    print("Created API Gateway:", api_endpoint)
    
    # 4. Create Integration
    integration = apigw.create_integration(
        ApiId=api_id,
        IntegrationType='AWS_PROXY',
        IntegrationUri=lambda_arn,
        PayloadFormatVersion='2.0'
    )
    integration_id = integration['IntegrationId']
    
    # 5. Create Route
    apigw.create_route(
        ApiId=api_id,
        RouteKey='POST /',
        Target=f'integrations/{integration_id}'
    )
    
    # 6. Create Stage
    apigw.create_stage(
        ApiId=api_id,
        StageName='$default',
        AutoDeploy=True
    )
    
    # 7. Grant permission to API Gateway
    aws_account_id = role_arn.split(':')[4]
    lmbda.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId='apigw-invoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}:{aws_account_id}:{api_id}/*/*"
    )
    
    print("\n" + "="*50)
    print("SUCCESSFULLY DEPLOYED!")
    print(f"API URL: {api_endpoint}/")
    print("="*50)
    
except Exception as e:
    print("API Gateway creation issue (might already exist):", e)
