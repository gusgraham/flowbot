import requests
import sys

try:
    response = requests.get("http://localhost:8001/api/fsa/projects/")
    if response.status_code == 200:
        print("Successfully connected to FSA Projects endpoint.")
        print("Response:", response.json())
    else:
        print(f"Failed to connect. Status Code: {response.status_code}")
        print("Response:", response.text)
        sys.exit(1)
except Exception as e:
    print(f"Error connecting to backend: {e}")
    sys.exit(1)
