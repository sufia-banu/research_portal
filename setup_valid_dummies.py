import time
from database.connection import get_supabase_admin_client

def create_valid_dummies():
    admin = get_supabase_admin_client()
    
    users_to_create = [
        {"email": "demo.aiml@hkbk.edu", "name": "Dr. AI Expert", "dept": "Artificial Intelligence and Machine Learning", "role": "faculty"},
        {"email": "demo.ise@hkbk.edu", "name": "Dr. ISE Scholar", "dept": "Information Science and Engineering", "role": "faculty"},
        {"email": "demo.rd@hkbk.edu", "name": "Dr. RD Demo", "dept": "Computer Science and Engineering", "role": "rd_coordinator"},
        {"email": "demo.hod@hkbk.edu", "name": "Dr. HOD Demo", "dept": "Computer Science and Engineering", "role": "hod"}
    ]
    
    created_uids = {}
    
    print("Creating valid GoTrue accounts via API...")
    for u in users_to_create:
        try:
            res = admin.auth.admin.create_user({
                "email": u["email"],
                "password": "password123",
                "email_confirm": True,
                "user_metadata": {
                    "full_name": u["name"],
                    "department": u["dept"],
                    "role": u["role"]
                }
            })
            if res.user:
                print(f"Created {u['email']}")
                created_uids[u["email"]] = res.user.id
        except Exception as e:
            err = str(e)
            if "already exists" in err.lower():
                print(f"User {u['email']} already exists.")
                created_uids[u["email"]] = None # Indicate it exists but we don't know ID here
            else:
                print(f"Error creating {u['email']}: {e}")
                
    time.sleep(2)
    print("\nInserting Research Data...")
    
    if "demo.aiml@hkbk.edu" in created_uids:
        aiml_id = created_uids["demo.aiml@hkbk.edu"]
        admin.table("research_entries").insert([
            {"faculty_id": aiml_id, "title": "Deep Learning for Medical Image Classification", "research_type": "Publication", "status": "Published", "year": 2024, "month": 2, "academic_year": "2023-24", "department": "Artificial Intelligence and Machine Learning", "is_nba_relevant": True, "indexing": "Scopus", "impact_factor": 3.8},
            {"faculty_id": aiml_id, "title": "Transformers in NLP", "research_type": "Publication", "status": "Presented", "year": 2023, "month": 11, "academic_year": "2023-24", "department": "Artificial Intelligence and Machine Learning", "is_nba_relevant": True, "indexing": "IEEE"}
        ]).execute()
        
    if "demo.ise@hkbk.edu" in created_uids:
        ise_id = created_uids["demo.ise@hkbk.edu"]
        admin.table("research_entries").insert([
            {"faculty_id": ise_id, "title": "Blockchain for Supply Chain", "research_type": "Publication", "status": "Published", "year": 2023, "month": 9, "academic_year": "2023-24", "department": "Information Science and Engineering", "is_nba_relevant": True, "indexing": "Web of Science", "impact_factor": 4.2}
        ]).execute()

    print("\nDone! You can now log in with the new 'demo.*@hkbk.edu' accounts.")

if __name__ == '__main__':
    create_valid_dummies()
