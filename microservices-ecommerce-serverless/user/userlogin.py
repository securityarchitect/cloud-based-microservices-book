import json
import boto3   
from botocore.exceptions import ClientError
import jwt
import datetime

REGION="us-west-2"
USER_POOL_ID="us-west-2_QAxrQRq1H"
CLIENT_ID="6egeuf4gpmv878phrcf8pvbl5i"
JWT_SECRET = 'mysecretkey'

cognitoclient = boto3.client('cognito-idp', region_name=REGION)
                            
def lambda_handler(event, context):
    body = event['body'].strip()
    body=body.replace('\n','')
    body=json.loads(body)

    username=body['username']
    password=body['password']
    result=False
    message=""
    response={}
    returndata={} 
    userdata={}
    #try:
    response = cognitoclient.admin_initiate_auth(
        UserPoolId=USER_POOL_ID,
        ClientId=CLIENT_ID,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password
        }
    )
    print(response)
    
    #except ClientError as e:
    #    message="Error in logging in"
    #    if e.response['Error']['Code'] == 'UserNotFoundException':
    #        result=False
    #        message=="Can't Find user by Email"
    #    if e.response['Error']['Code'] == 'NotAuthorizedException':
    #        result=False
    #        message="Incorrect username or password"
    #    if e.response['Error']['Code'] == 'UserNotConfirmedException':
    #        result=False
    #        message="User is not confirmed"

    if 'ResponseMetadata' in response:
        if response['ResponseMetadata']['HTTPStatusCode']==200:        
            result=True
            message="Login successful"
            response = cognitoclient.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=username
            )
            
            # Generate JWT with user info and expiry
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, JWT_SECRET, algorithm='HS256') 
        
            # Return token
            userdata['token'] = token
            
            for item in response['UserAttributes']:
                if item['Name']=='given_name':
                    userdata['given_name']=item['Value']
                elif item['Name']=='family_name':
                    userdata['family_name']=item['Value']
                elif item['Name']=='email':
                    userdata['email']=item['Value']
                elif item['Name']=='picture':
                    userdata['picture']=item['Value']
        else:
            return False
            message="Something went wrong"
            
    userdata['username']=username
    returndata['result']=result
    returndata['message']=message
    returndata['userdata']=userdata
    
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*",
            "Access-Control-Allow-Methods" : "*" 
          },
        "body": json.dumps(returndata)
    }