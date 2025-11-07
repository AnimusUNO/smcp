#!/usr/bin/env python3

import hmac
import hashlib
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv('.env')
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET_KEY')

print("=== Testing Signature Generation ===")

# Test 1: Exact example from documentation
print("\n1. Testing documentation example:")
query_string = 'symbol=BNBUSDT&side=BUY&type=LIMIT&timeInForce=GTC&quantity=5&price=1.1&recvWindow=5000&timestamp=1756187806000'
secret = 'fdde510a2b71fa43a43bff3e3cf7819c8c66df34633d338050f4f59664b3b313'
expected_signature = 'e09169bf6c02ec4b29fa1bdc3a967f92c8c6cfcde0551ba1d477b2d3cf4c51b0'

signature = hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
print(f"Expected: {expected_signature}")
print(f"Got:      {signature}")
print(f"Match: {signature == expected_signature}")

# Test 2: Our API key with simple parameters
print("\n2. Testing our API key with simple parameters:")
timestamp = int(time.time() * 1000)
params = {
    'timestamp': timestamp,
    'recvWindow': 5000
}

query_string = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
print(f"Query string: {query_string}")
signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
print(f"Signature: {signature}")

# Test 3: Test account endpoint
print("\n3. Testing account endpoint:")
params['signature'] = signature
headers = {'X-MBX-APIKEY': api_key}

response = requests.get('https://sapi.asterdex.com/api/v1/account', headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test 4: Test with string values
print("\n4. Testing with string values:")
params_str = {
    'timestamp': str(timestamp),
    'recvWindow': '5000'
}

query_string_str = '&'.join([f'{k}={v}' for k, v in sorted(params_str.items())])
print(f"Query string (str): {query_string_str}")
signature_str = hmac.new(api_secret.encode('utf-8'), query_string_str.encode('utf-8'), hashlib.sha256).hexdigest()
print(f"Signature (str): {signature_str}")

params_str['signature'] = signature_str
response_str = requests.get('https://sapi.asterdex.com/api/v1/account', headers=headers, params=params_str)
print(f"Status (str): {response_str.status_code}")
print(f"Response (str): {response_str.text}")
