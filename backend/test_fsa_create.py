import requests
import json

# Test creating a project
url = "http://localhost:8001/api/fsa/projects/"
data = {
    "name": "Test FSA Project",
    "description": "Testing the new FSA domain",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59"
}

print(f"POST {url}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=5)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.Timeout:
    print("\nRequest timed out")
except Exception as e:
    print(f"\nError: {e}")
