import time
from database.connection import get_supabase_admin_client

def fix_auth():
    print("Connecting to Supabase Admin...")
    admin = get_supabase_admin_client()
    
    emails_to_fix = [
        "rd_demo@hkbk.edu", 
        "faculty_demo@hkbk.edu", 
        "hod_demo@hkbk.edu", 
        "aiml_demo@hkbk.edu", 
        "ise_demo@hkbk.edu"
    ]
    
    # 1. Fetch user IDs from the public.profiles table (bypassing auth list_users issue)
    try:
        res = admin.table('profiles').select('id, email').execute()
        profiles = res.data
        print(f"Found {len(profiles)} profiles in the database.")
    except Exception as e:
        print(f"Failed to query profiles: {e}")
        return

    # 2. Update passwords via GoTrue Admin API using the retrieved IDs
    for p in profiles:
        if p['email'] in emails_to_fix:
            uid = p['id']
            print(f"Updating credentials for {p['email']} (ID: {uid})...")
            try:
                admin.auth.admin.update_user_by_id(
                    uid, 
                    {"password": "password123", "email_confirm": True}
                )
                print(f"Successfully fixed login for {p['email']}")
            except Exception as e:
                print(f"Failed to fix {p['email']}: {e}")
            time.sleep(0.5)

    print("\nAuthentication fix complete! You can now log in.")

if __name__ == '__main__':
    fix_auth()
