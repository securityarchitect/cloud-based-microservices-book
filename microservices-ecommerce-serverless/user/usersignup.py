import json
import boto3  
from botocore.exceptions import ClientError
import avinit, random, time
import io


REGION="us-west-2"
USER_POOL_ID="us-west-2_QAxrQRq1H"
CLIENT_ID="6egeuf4gpmv878phrcf8pvbl5i"

cognitoclient = boto3.client('cognito-idp', region_name=REGION)

s3 = boto3.client('s3')
BUCKET_NAME='microservices-ecommerce-app'
CLOUDFRONT_URL = 'https://dn2aztcn1xe1u.cloudfront.net'

def lambda_handler(event, context):
    body = event['body'].strip()
    body=body.replace('\n','')
    body=json.loads(body)
    
    username=body['username']
    password=body['password']
    given_name=body['given_name']
    family_name=body['family_name']
    email=body['email']
    
    
    name=given_name+' '+ family_name
    filename = "user"+str(int(time.time()*1000))+".png"
    imgpath='/tmp/'+filename
    r = lambda: random.randint(0,255)
    colors=[]
    colors.append('#%02X%02X%02X' % (r(),r(),r()))
    #image_data = avinit.get_svg_avatar(name, colors=colors)
    avinit.get_png_avatar(name, output_file=imgpath, colors=colors)
    path_filename_s3 = "photos/" + filename
    with open(imgpath, 'rb') as f:
        s3.upload_fileobj(f, BUCKET_NAME, path_filename_s3)
    
    #image_object = io.BytesIO(image_data)
    
    #s3.upload_fileobj(image_object, BUCKET_NAME, path_filename_s3)
    url = CLOUDFRONT_URL+'/'+path_filename_s3
    
    
    picture=url #body['picture']
    
    result=False
    message=""
    response={}
    returndata={} 
    userdata={}
    #try:
    response = cognitoclient.sign_up(
        ClientId=CLIENT_ID,
        Username=username,
        Password=password,
        UserAttributes=[
            {
                'Name': 'given_name',
                'Value': given_name
            },
            {
                'Name': 'family_name',
                'Value': family_name
            },
            {
                'Name': 'email',
                'Value': email
            },
            {
                'Name': 'picture',
                'Value': picture
            },
        ]
    )
    result=True
    message="Signup successful"
    

    #except ClientError as e:
    #    if e.response['Error']['Code'] == 'UsernameExistsException':
    #        result=False
    #        message="User already exists"
    #    if e.response['Error']['Code'] == 'ParamValidationError':
    #        result=False
    #        message="Param Validation Error"
    
    
    response = cognitoclient.admin_confirm_sign_up(
        UserPoolId=USER_POOL_ID,
        Username=username
    )
    
    userdata['username']=username
    userdata['given_name']=given_name
    userdata['family_name']=family_name
    userdata['picture']=picture
    userdata['email']=email
    returndata['result']=result
    returndata['message']=message
    returndata['userdata']=userdata
    
    return {
        "statusCode": 200,
        "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Methods" : "*" 
            },
        "body": json.dumps(returndata)
    }