import jwt
import datetime

__MY__SECRET__ = "THIS IS MY SECRET--CHANGE-ME"

def authorizer_handler(event, context):
    print(event)
    principal_id = extract_principal_from_jwt(event['headers']['Authorization'])
    if principal_id is None:
        return deny_policy(event)
    policy = allow_policy(event, principal_id)
    print(policy)
    return policy

def deny_policy(event):
    return generate_policy('user', 'Deny', event['methodArn'])

def allow_policy(event, principal_id):
    return generate_policy(principal_id, 'Allow', event['methodArn'])

def generate_policy(principal_id, effect, arn):
    auth_response = {}
    auth_response['principalId'] = principal_id
    if effect and arn:
        tmp = arn.split(':')
        apiGatewayArnTmp = tmp[5].split('/')
        awsAccountId = tmp[4]
        regionId = tmp[3]
        restApiId = apiGatewayArnTmp[0]
        stage = apiGatewayArnTmp[1]
        # method = apiGatewayArnTmp[2] not used for this example
        policy_document = {}
        policy_document['Version'] = '2012-10-17'
        policy_document['Statement'] = []
        for httpVerb in ["POST","PATCH"]:
            resource = f"arn:aws:execute-api:{regionId}:{awsAccountId}:{restApiId}/{stage}/{httpVerb}/"
            statement_one = {}
            statement_one['Action'] = 'execute-api:Invoke'
            statement_one['Effect'] = effect
            statement_one['Resource'] = resource
            policy_document['Statement'].append(statement_one)
        auth_response['policyDocument'] = policy_document
    return auth_response

def extract_principal_from_jwt(jwt_token):
    token = jwt.decode(jwt_token, __MY__SECRET__, algorithms=['HS256'])
    aid=token['aid']
    if aid in principals:
        return principals[aid]['principal']
    return None

principals = dict()
principals['aid1'] = dict()
principals['aid1']['principal'] = "user1"
principals['aid2'] = dict()
principals['aid2']['principal'] = "user2"

def create_jwt_from_principal(aid):
    return jwt.encode({"aid":aid,"role":"owner","ca":datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            __MY__SECRET__, 
            algorithm='HS256')