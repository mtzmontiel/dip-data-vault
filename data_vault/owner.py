import json


def lambda_handler(event, context):
    method = event["httpMethod"].casefold()
    if "post" == method:
        results = store_data(event, context)
        body = create_body("success", results)
        return create_response(body)
    elif "patch" == method:
        results = remove_data(event, context)
        body = create_body("success", results)
        return create_response(body)
    return {"statusCode": 400, "body": f"Bad request. {method}"}


def store_data(event, context):
    """Store Private data and respond with corresponding tokens"""
    elements = extract_elements(event)
    results = dict()
    for k,v in elements.items():
        results[k] = dict()
        results[k]["token"] = v["value"]
        results[k]["success"] = True
    return results


def remove_data(event, context):
    """Remove private data by tokens"""
    elements = extract_elements(event)
    results = dict()
    for k,v in elements.items():
        results[k] = dict()
        results[k]["token"] = v
        results[k]["success"] = True
    return results


def create_body(message, elements):
    return {
        "message": message,
        "elements": elements
    }

def create_response(body):
    return {
        "statusCode": 200,
        "body": json.dumps(body),
    }

def extract_elements(event):
    body=json.loads(event["body"])
    return body["elements"]