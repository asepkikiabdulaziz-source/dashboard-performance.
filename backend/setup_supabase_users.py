
from supabase_client import get_supabase_client
import time

def create_users():
    supabase = get_supabase_client()
    
    users = [
        {
            "email": "admin@company.com",
            "password": "admin123",
            "data": {
                "name": "Admin User",
                "role": "admin",
                "region": "ALL"
            }
        },
        {
            "email": "user-a@company.com",
            "password": "password123",
            "data": {
                "name": "Jabodebek User",
                "role": "viewer",
                "region": "R06 JABODEBEK"
            }
        },
        {
            "email": "user-b@company.com",
            "password": "password123",
            "data": {
                "name": "Sumut User",
                "role": "viewer",
                "region": "R01 SUMUT"
            }
        },
         {
            "email": "user-c@company.com",
            "password": "password123",
            "data": {
                "name": "Jatim User",
                "role": "viewer",
                "region": "R14 JATIM SELATAN"
            }
        }
    ]

    print("🚀 Starting User Creation Migration...")
    
    for u in users:
        print(f"\nCreating user: {u['email']}...")
        try:
            # Sign up with metadata
            res = supabase.auth.sign_up({
                "email": u["email"],
                "password": u["password"],
                "options": {
                    "data": u["data"]
                }
            })
            
            if res.user:
                print(f"✅ Created successfully (ID: {res.user.id})")
                if not res.user.confirmed_at:
                    print("⚠️  Warning: User needs email confirmation (check Supabase settings to disable 'Confirm email')")
            elif res.session:
                 print(f"✅ Logged in (User already exists?)")
            else:
                print(f"⚠️  Result ambiguous: {res}")
                
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            if "User already registered" in str(e):
                print("   (User already exists, skipping)")

    print("\n✨ Migration Completed.")
    print("NOTE: If 'Enable Email Confirmations' is ON in Supabase, users cannot login until confirmed.")

if __name__ == "__main__":
    create_users()
