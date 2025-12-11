
file_path = r"d:\antigravity\flowbot_hub\_TestData\2336_S0001_WQ_COND_WQ_DO_WQ_DO_SAT_WQ_NH4_WQ_PH_WQ_TEMP_102822_000000.csv"

try:
    with open(file_path, 'r') as f:
        print("--- File Content (First 5 lines) ---")
        for i in range(5):
            print(f"Line {i}: {f.readline().strip()}")
except Exception as e:
    print(f"Error: {e}")
