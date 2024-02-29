import json

def lambda_handler(event, context):
    print(json.dumps(event))
    method = event["httpMethod"].casefold()
    if "post" == method:
        return store_data(event,context)
    elif "patch" == method:
        return remove_data(event, context)
    return {"statusCode": 400, "body": f"Bad request. {method}"}
def store_data(event, context):
    elements = extract_elements(event)
    results = {}
    for k,v in elements.items():
        results[k] = {}
        results[k]["token"] = v["value"]
        results[k]["success"] = True

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            "elements": results
        }),
    }

def remove_data(event, context):
    elements = extract_elements(event)
    results = {}
    for k,v in elements.items():
        results[k] = {}
        results[k]["token"] = v
        results[k]["success"] = True
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            "elements": results
        }),
    }
def extract_elements(event):
    body=json.loads(event["body"])
    return body["elements"]