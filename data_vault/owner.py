import json
import os
import uuid
import boto3
import botocore
from dynamodb_encryption_sdk.material_providers import CryptographicMaterialsProvider
from dynamodb_encryption_sdk.encrypted.table import EncryptedTable
from dynamodb_encryption_sdk.structures import AttributeActions
from dynamodb_encryption_sdk.identifiers import CryptoAction
from dynamodb_encryption_sdk.material_providers.aws_kms import AwsKmsCryptographicMaterialsProvider

def create_table(table_name, key_id):
    return create_secure_table(table_name, key_id)

def ddb():
    return boto3.resource('dynamodb')

def create_table_without_encryption(table_name):
    return ddb().Table(table_name)

def create_secure_table(table_name, key_id):
    materials_provider = create_materials_provider(key_id)
    return create_encrypted_table(table_name, materials_provider)

def create_materials_provider(key_id):
    return AwsKmsCryptographicMaterialsProvider(key_id)

def create_encrypted_table(table_name, materials_provider):
    table = boto3.resource('dynamodb').Table(table_name)
    attribute_actions = AttributeActions(
        default_action=CryptoAction.DO_NOTHING,
        attribute_actions={
            'enc_value': CryptoAction.ENCRYPT_AND_SIGN
        }
    )
    return EncryptedTable(table, materials_provider, attribute_actions=attribute_actions)

res = ddb()
table = create_table(os.environ["TABLE_NAME"], os.environ["KEY_ID"])


def lambda_handler(event, context):
    method = event["httpMethod"].casefold()
    if "post" == method:
        results = store_data(event, context)
        body = create_body("success", results)
        return create_response(body)
    elif "patch" == method:
        results, err = remove_data(event, context)
        print(f"results: {results}, err: {err}")
        if err is not None:
            return create_response(create_body("error", results), err)
        body = create_body("success", results)
        return create_response(body)
    return {"statusCode": 400, "body": f"Bad request. {method}"}

def store_data(event, context):
    """Store Private data and respond with corresponding tokens"""
    elements = extract_elements(event)
    results = dict()
    principal_id = extract_principal_id(event)
    for k,v in elements.items():
        token = tokenize(v)
        ddresult = table.put_item(Item={
                "pk": get_pk(principal_id, token), 
                "owned_by":principal_id, 
                "token": token,
                "data_class": v["classification"],
                "enc_value": v["value"] 
            })
        if ddresult["ResponseMetadata"]["HTTPStatusCode"] != 200:
            results[k] = dict()
            results[k]["success"] = False
            continue
        results[k] = dict()
        results[k]["token"] = token
        results[k]["success"] = True
    return results

def tokenize(value):
    return uuid.uuid4().hex

def get_pk(owner, token):
    return f"PD#{owner}#{token}"

def remove_data(event, context):
    """Remove private data by tokens"""
    principal_id = extract_principal_id(event)
    results = dict()
    token = extract_token(event)
    results["token"] = token
    try:
        ddresult = table.delete_item(Key={"pk": get_pk(principal_id, token)}, 
                                    ConditionExpression="owned_by = :val",
                                    ExpressionAttributeValues={":val": principal_id})
        if ddresult["ResponseMetadata"]["HTTPStatusCode"] != 200:       
            results["success"] = False
            results["message"] = "Could not process request."
        else:
            results["success"] = True
            results["message"] = "Successfully Removed"

    except res.meta.client.exceptions.ConditionalCheckFailedException as e: 
        results["success"] = False
        results["message"] = "Could not process request"
        return results, e
        
    return results, None

def extract_principal_id(event):
    return event["requestContext"]["authorizer"]["principalId"]

def create_body(message, elements):
    retValue = {
        "message": message,
        "elements": elements
    }
    print(retValue)
    return retValue

def create_response(body, err=None):
    status_code = 200
    if err:
        status_code = 400
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
    }

def extract_elements(event):
    body=json.loads(event["body"])
    return body["elements"]

def extract_token(event):
    body=json.loads(event["body"])
    return body["token"]