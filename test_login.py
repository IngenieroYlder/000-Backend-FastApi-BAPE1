import urllib.request
import urllib.parse
import json

url = "http://localhost:8000/auth/login"
data = {
    "username": "admin@bape.com",
    "password": "admin"
}
encoded_data = urllib.parse.urlencode(data).encode('utf-8')

try:
    print(f"Sending login request to {url}...")
    req = urllib.request.Request(url, data=encoded_data, method='POST')
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.status}")
        print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.HTTPError as e:
    print(f"Request failed: {e.code} {e.reason}")
    print(f"Error Response: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Request failed: {e}")
