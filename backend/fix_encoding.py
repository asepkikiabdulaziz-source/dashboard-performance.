
import os

def fix_file(filepath):
    print(f"Fixing {filepath}...")
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            
        # Strip null bytes
        new_content = content.replace(b'\x00', b'')
        
        # Also clean up any potential BOM or weird ending if evident, 
        # but null byte removal is the critical fix for "source code string cannot contain null bytes"
        
        with open(filepath, 'wb') as f:
            f.write(new_content)
            
        print("✅ File fixed.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_file("d:/PROJECT/dashboard-performance/backend/main.py")
