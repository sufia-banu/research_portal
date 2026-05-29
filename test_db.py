import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Try to insert 'Journal'
try:
    # Get a random faculty
    res = client.table("profiles").select("id").limit(1).execute()
    if not res.data:
        print("No profiles found")
        sys.exit()
    fid = res.data[0]['id']
    
    # Try inserting
    client.table("research_entries").insert({
        "faculty_id": fid,
        "title": "Test Journal Entry",
        "research_type": "Journal",
        "status": "Submitted"
    }).execute()
    print("SUCCESS: Inserted Journal")
    
    # Clean up
    client.table("research_entries").delete().eq("title", "Test Journal Entry").execute()
except Exception as e:
    print(f"FAILED: {e}")
