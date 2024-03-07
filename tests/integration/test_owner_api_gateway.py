import os

import boto3
import pytest
import requests
import os
from authorizer import authorizer

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""

dir()

class TestApiGateway:

    @pytest.fixture()
    def api_gateway_url(self):
       return os.environ["VAULT_API_URL"]
    
    # fixture to return user 1 authorization
    @pytest.fixture()
    def user1_auth(self):
        return authorizer.create_jwt_from_principal('aid1')
    
    @pytest.fixture()
    def user2_auth(self):
        return authorizer.create_jwt_from_principal('aid2')


    def test_api_gateway_store(self, api_gateway_url, user1_auth):
        """ Call the API Gateway endpoint and check the response """
        response = requests.post(api_gateway_url, 
            headers={"Authorization": user1_auth, "Content-Type":"application/json"}, 
            json={
            "elements": {
                "givenname":{
                    "value":"my name", "classification":"name"},
                "contact1":{
                    "value":"email@other.com", "classification":"email"},
                "phone1":{
                        "value":"+521234567890", "classification":"phone"}}})

        assert response.status_code == 200, f"Response: {response.content}"
        body = response.json()

        given_name = validate_alias_in_body_data_elements(body, "elements", "givenname")
        validate_token_in_element(given_name)
        contact = validate_alias_in_body_data_elements(body, "elements", "contact1")
        validate_token_in_element(contact)


    def test_api_gateway_remove(self, api_gateway_url, user1_auth):
        """ Call the API Gateway endpoint and check the response """
        data_tokens = self.invoke_store_data(api_gateway_url, "givenname", "givenname", "name", user1_auth)

        data_element = validate_alias_in_data_elements(data_tokens, "givenname")
        token = validate_token_in_element(data_element)
        
        response = self.invoke_remove_data(api_gateway_url, "givenname", token, user1_auth)

        assert response.status_code == 200, f"Response: {response.content}"
        body = response.json()
        assert "success" in data_element, f"Data element: {data_element}"
        assert data_element["success"] == True
        assert token in data_element['token'], f"Data element: {data_element}"

    def test_api_gateway_remove_with_different_user(self, api_gateway_url, user1_auth, user2_auth):
        """ Call the API Gateway endpoint and check the response """
        data_tokens = self.invoke_store_data(api_gateway_url, "givenname", "givenname", "name", user1_auth)

        data_element = validate_alias_in_data_elements(data_tokens, "givenname")
        token = validate_token_in_element(data_element)

        response = self.invoke_remove_data(api_gateway_url, "givenname", token, user2_auth)

        assert response.status_code == 400, f"Response: {response.content}"
        body = response.json()
        assert "message" in body, f"Body: {body}"
        assert body["message"] == "error"


    def invoke_store_data(self, api_gateway_url, alias, value, classification, authorization):
        data_elements = dict()
        data_elements[alias] = {"value":value, "classification":classification}
        response = requests.post(api_gateway_url,
            headers={"Authorization": authorization, "Content-Type":"application/json"}, 
            json={
                "elements": data_elements})

        assert response.status_code == 200, f"Response: {response.content}"

        body = response.json()
        validate_alias_in_body_data_elements(body,"elements", alias)
        return body["elements"]

    def invoke_remove_data(self, api_gateway_url, alias, token, authorization):
        response = requests.patch(f"{api_gateway_url}",
            headers={"Authorization":authorization, "Content-Type":"application/json"},
            json={"token":  token})
        return response
def validate_alias_in_body_data_elements(body, container, alias):
    assert container in body
    data_elements = body[container]
    return validate_alias_in_data_elements(data_elements, alias)

def validate_alias_in_data_elements(data_elements, alias):
    assert alias in data_elements, f"Alias: {alias}, Data elements: {data_elements}"
    return data_elements[alias]

def validate_token_in_element(element):
    assert "token" in element
    return element["token"]