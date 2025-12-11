import requests
import time
import io

BASE_URL = "http://localhost:8001/api"

def test_wq_flow():
    print("🚀 Starting WQ Module Test Flow...")

    # 0. Login
    print("\n[0] Logging in...")
    login_res = requests.post(f"{BASE_URL}/token", data={
        "username": "admin@flowbot.com",
        "password": "admin123"
    })
    if login_res.status_code != 200:
        print(f"❌ Failed to log in: {login_res.text}")
        return
    access_token = login_res.json().get("access_token")
    if not access_token:
        print(f"❌ Login successful but no access_token found: {login_res.text}")
        return
    print(f"✅ Logged in successfully. Token: {access_token[:10]}...")
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Create Project
    print("\n[1] Creating Project...")
    proj_res = requests.post(f"{BASE_URL}/wq/projects", json={
        "name": "Test WQ Project",
        "job_number": "TEST-001",
        "client": "Test Client"
    }, headers=headers)
    if proj_res.status_code != 200:
        print(f"❌ Failed to create project: {proj_res.text}")
        return
    project = proj_res.json()
    project_id = project['id']
    print(f"✅ Created Project ID: {project_id}")

    # 2. Upload File
    print("\n[2] Uploading Dataset...")
    file_path = r"d:\antigravity\flowbot_hub\_TestData\2336_S0001_WQ_COND_WQ_DO_WQ_DO_SAT_WQ_NH4_WQ_PH_WQ_TEMP_102822_000000.csv"
    
    with open(file_path, 'rb') as f:
        files = {'file': ('test_data.csv', f, 'text/csv')}
        upload_res = requests.post(f"{BASE_URL}/wq/projects/{project_id}/datasets/upload", files=files, headers=headers)
    
    if upload_res.status_code != 200:
        print(f"❌ Failed to upload: {upload_res.text}")
        return
    dataset_info = upload_res.json()
    dataset_id = dataset_info['dataset_id']
    print(f"✅ Uploaded Dataset ID: {dataset_id}")
    print(f"   Headers: {dataset_info['headers']}")
    
    detected_name = dataset_info.get("details", {}).get("detected_monitor_name")
    print(f"   Detected Monitor: {detected_name}")
    
    # 3. Process Import (Mapping)
    print("\n[3] Processing Import...")
    # Attempt to auto-map based on headers found
    mapping = {"Date": "DateTime"} # Start with assumption
    
    # Simple keyword mapping for test
    known_vars = ["pH", "DO", "Temp", "Cond", "NH4"]
    for h in dataset_info['headers']:
        for v in known_vars:
            if v.upper() in h.upper():
                mapping[v] = h
    
    print(f"   Using Mapping: {mapping}")

    process_res = requests.post(f"{BASE_URL}/wq/datasets/{dataset_id}/import", json={
        "mapping": mapping,
        "monitor_name": detected_name or "Site A"
    }, headers=headers)
    if process_res.status_code != 200:
        print(f"❌ Failed to process: {process_res.text}")
        return
    monitor_info = process_res.json()
    monitor_id = monitor_info['monitor_id']
    print(f"✅ Created Monitor ID: {monitor_id}")

    # 4. Get Data
    print("\n[4] Retrieving Graph Data...")
    data_res = requests.get(f"{BASE_URL}/wq/monitors/{monitor_id}/data")
    if data_res.status_code != 200:
        print(f"❌ Failed to retrieve data: {data_res.text}")
        return
    data = data_res.json()
    
    if "pH" in data and len(data["pH"]) == 3:
        print(f"✅ Data Retrieved Successfully: {len(data['pH'])} points for pH")
        print(f"   Sample: {data['pH'][0]}")
    else:
        print(f"❌ Unexpected data format: {data}")

if __name__ == "__main__":
    try:
        test_wq_flow()
    except Exception as e:
        print(f"❌ Test Crashed: {e}")
