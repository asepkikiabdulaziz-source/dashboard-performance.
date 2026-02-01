import os
import sys
import traceback
import uvicorn

# ==========================================
# DIAGNOSTIC BOOTSTRAP
# This script helps debug why Cloud Run 
# fails to import the 'main' module.
# ==========================================

print("🚀 Starting Diagnostic Bootstrap...")
print(f"📂 Current Directory: {os.getcwd()}")
print(f"📂 Directory Contents: {os.listdir('.')}")
print(f"🐍 Python Executable: {sys.executable}")
print(f"🐍 Python Path: {sys.path}")

try:
    print("🔄 Attempting to import 'main' module...")
    import main
    print("✅ Successfully imported 'main' module!")
    
    if not hasattr(main, 'app'):
        print("❌ ERROR: 'main' module has no 'app' attribute!")
        sys.exit(1)
    
    print("✅ Found 'app' in 'main'. Ready to start uvicorn.")

except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    print("--- FULL TRACEBACK ---")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ UNEXPECTED STARTUP ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting uvicorn on port {port}...")
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info", proxy_headers=True)
    except Exception as e:
        print(f"❌ UVICORN CRASHED: {e}")
        traceback.print_exc()
        sys.exit(1)
