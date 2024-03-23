import jwt
import os

# Specify the JWT secret
JWT_SECRET = 'mysecretkey'

def lambda_handler(event, context):
    print(event)
    # Get the Auth header
    print(event)
    token = event['headers']['authorization']
    print("Token", token)
    
    validate_token = lambda token: jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    try:
        payload = validate_token(token)
        print('Token valid') 
        # Return a policy 
        return {
          "principalId": "user", 
          "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Action": "execute-api:Invoke", 
                "Effect": "Allow",
                "Resource": event["methodArn"]  
              }
            ]
          }
        }

    except jwt.ExpiredSignatureError:
        print('Token expired') 
        return {"response":"Invalid token"}
    except jwt.InvalidTokenError:
        print('Invalid token')
        return {"response":"Invalid token"}