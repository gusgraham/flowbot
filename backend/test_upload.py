import requests

# Test upload endpoint
url = "http://localhost:8001/api/analysis/projects/1/upload"
file_path = r"D:\antigravity\flowbot_hub\_TestData\biddmh01.fdv"

print(f"Testing upload of: {file_path}")
print(f"To endpoint: {url}")
print("-" * 60)

try:
    with open(file_path, 'rb') as f:
        files = {'file': ('biddmh01.fdv', f, 'application/octet-stream')}
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\n✅ Upload successful!")
        print("Check backend console for background processing logs")
    else:
        print(f"\n❌ Upload failed: {response.text}")
        
except FileNotFoundError:
    print(f"❌ File not found: {file_path}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend. Is it running on port 8001?")
except Exception as e:
    print(f"❌ Error: {e}")
