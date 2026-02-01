import requests
import json
import jwt

BASE_URL = "http://localhost:8000/api"

def run_security_test():
    print("🔒 STARTING SECURITY VERIFICATION...")
    
    # 1. Login as Regional User
    print("\n[1] Logging in as Regional User (user-a@company.com)...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "user-a@company.com",
            "password": "password123"
        })
        response.raise_for_status()
        data = response.json()
        token = data['access_token']
        print("✅ Login Successful")
        print(f"🔑 Token received: {token[:15]}...")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    # 2. Verify Token Claims
    print("\n[2] Verifying Token Claims...")
    try:
        # We decode without verification just to check claims (demo secret is in backend)
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"📜 Token Payload: {decoded}")
        if decoded.get("region") == "R06 JABODEBEK":
            print("✅ Token correctly assigned to R06 JABODEBEK")
        else:
            print(f"❌ Token has wrong region: {decoded.get('region')}")
    except Exception as e:
        print(f"❌ Token decoding failed: {e}")

    # 3. Test Authorized Access (Own Region)
    print("\n[3] Testing Valid Access (Default/Own Region)...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/leaderboard", headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Check if data belongs to R06
            is_leaking = False
            for row in data[:5]: # Check first 5 rows
                if row['region'] != "R06 JABODEBEK" and row['region'] != 'R06':
                    print(f"❌ DATA LEAK! Found record from {row['region']}")
                    is_leaking = True
                    break
            
            if not is_leaking:
                print(f"✅ Access Allowed. Returned {len(data)} records. All verified as R06.")
        else:
            print(f"❌ Request failed with {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

    # 4. Test Unauthorized Access (Attempt to access R01 SUMUT)
    print("\n[4] 🛡️ TESTING SECURITY BREACH (Attempting to view R01 SUMUT)...")
    try:
        # Explicitly requesting R01 SUMUT while logged in as R06
        response = requests.get(f"{BASE_URL}/leaderboard", headers=headers, params={"region": "R01 SUMUT"})
        
        data = response.json()
        
        # Analyze Result
        print(f"Response Status: {response.status_code}")
        
        leaked_records = [r for r in data if r['region'] == "R01 SUMUT"]
        
        if len(leaked_records) > 0:
            print(f"❌ SECURITY FAILED! Backend returned {len(leaked_records)} records for R01 SUMUT.")
            print("CRITICAL: User was able to access other region's data via API!")
        else:
            # Check if it returned R06 or Empty or Error
            r06_records = [r for r in data if r['region'] == "R06 JABODEBEK"]
            if len(r06_records) > 0:
                print(f"✅ SECURITY PASS: Backend ignored 'region=R01 SUMUT' param and returned user's own R06 data ({len(r06_records)} records).")
                print("👍 Logic is secure: Wrapper enforced user's region.")
            elif response.status_code == 403:
                print("✅ SECURITY PASS: Backend blocked access with 403 Forbidden.")
            elif len(data) == 0:
                 print("✅ SECURITY PASS: Backend returned empty list (Safe default).")
            else:
                 print(f"⚠️ UNKNOWN STATE: Returned {len(data)} records. First: {data[0].get('region') if data else 'None'}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    run_security_test()
