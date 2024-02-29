import os

import boto3
import pytest
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestApiGateway:

    @pytest.fixture()
    def api_gateway_url(self):
       return "https://llnmq566ea.execute-api.us-east-1.amazonaws.com/live/"

    def test_api_gateway_store(self, api_gateway_url):
        """ Call the API Gateway endpoint and check the response """
        response = requests.post(api_gateway_url, json={
            "elements": {
                "givename":{
                    "value":"my name", "classification":"name"},
                "contact1":{
                    "value":"email@other.com", "classification":"email"}}})

        assert response.status_code == 200
        body = response.json()
        validate_alias_in_body_data_elements(body, "elements", "givenname")
        validate_alias_in_body_data_elements(body, "elements", "contact1")


    def test_api_gateway_remove(self, api_gateway_url):
        """ Call the API Gateway endpoint and check the response """
        data_tokens = self.invoke_store_data(api_gateway_url, "givenname", "givenname", "name")
        data_element = validate_alias_in_data_elements(data_tokens, "givenname")
        
        assert "token" in data_element , f"Expected token but got on response data element: {data_element}"
        
        response = requests.patch(api_gateway_url, json={
            "elements": {
                "givenname": data_element["token"]}})

        assert response.status_code == 200
        body = response.json()
        data_element = validate_alias_in_body_data_elements(body,'elements', "givenname")


    def invoke_store_data(self, api_gateway_url, alias, value, classification):
        data_elements = {}
        data_elements[alias] = {"value":value, "classification":classification}
        response = requests.post(api_gateway_url, json={
            "elements": data_elements})

        assert response.status_code == 200
        body = response.json()
        validate_alias_in_body_data_elements(body,"elements", alias)
        return body["elements"]
    
def validate_alias_in_body_data_elements(body, container, alias):
    assert container in body
    data_elements = body[container]
    return validate_alias_in_data_elements(data_elements, alias)

def validate_alias_in_data_elements(data_elements, alias):
    assert alias in data_elements
    return data_elements[alias]
