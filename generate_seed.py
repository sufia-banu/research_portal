import random
from datetime import datetime
import uuid
import json
import time

from database.connection import get_supabase_admin_client

DEPARTMENTS = ["CSE", "ISE", "AIML", "ECE", "EEE", "ME", "CE", "BT"]
DEPT_FULL = {
    "CSE": "Computer Science and Engineering",
    "ISE": "Information Science and Engineering",
    "AIML": "Artificial Intelligence and Machine Learning",
    "ECE": "Electronics and Communication Engineering",
    "EEE": "Electrical and Electronics Engineering",
    "ME": "Mechanical Engineering",
    "CE": "Civil Engineering",
    "BT": "Biotechnology"
}

ROLES = ["faculty", "hod", "rd_coordinator", "admin"]
INDEXING = ["Scopus", "SCI", "Web of Science", "IEEE", "Springer", "Elsevier"]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
               "Ananya", "Diya", "Avni", "Kavya", "Saanvi", "Neha", "Riya", "Aisha", "Pooja", "Meera",
               "John", "David", "Michael", "Chris", "Sarah", "Emily", "Jessica", "Lisa"]
LAST_NAMES = ["Sharma", "Patil", "Reddy", "Gowda", "Kumar", "Singh", "Das", "Rao", "Iyer", "Nair", "Smith", "Johnson", "Williams"]

def generate_users_config():
    users = []
    # Create 1 admin
    users.append({
        "full_name": "System Admin",
        "email": "iqac@hkbk.edu",
        "password": "password123",
        "department": DEPT_FULL["CSE"],
        "role": "admin"
    })
    # Create 1 R&D
    users.append({
        "full_name": "Dr. R&D Head",
        "email": "rd@hkbk.edu",
        "password": "password123",
        "department": DEPT_FULL["CSE"],
        "role": "rd_coordinator"
    })
    # Create HODs
    for code, full in DEPT_FULL.items():
        users.append({
            "full_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} (HOD)",
            "email": f"hod.{code.lower()}@hkbk.edu",
            "password": "password123",
            "department": full,
            "role": "hod"
        })
    # Create Faculty
    for i in range(1, 15): # Limiting to 15 to prevent API rate limiting for demo
        dept = random.choice(list(DEPT_FULL.values()))
        users.append({
            "full_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "email": f"faculty{i}@hkbk.edu",
            "password": "password123",
            "department": dept,
            "role": "faculty"
        })
    return users

def generate_entries(user_records):
    entries = []
    faculty_users = [u for u in user_records if u["role"] in ["faculty", "hod", "rd_coordinator"]]
    
    pub_titles = ["Deep Learning for ", "IoT based ", "Machine Learning in ", "Blockchain applied to ", "Cloud Computing for ", "Optimization of ", "Novel approach to ", "Smart System for "]
    pub_topics = ["Healthcare", "Agriculture", "Smart Cities", "Autonomous Vehicles", "Cyber Security", "Renewable Energy", "Robotics", "Data Mining", "Wireless Sensor Networks", "Image Processing"]
    
    pat_titles = ["System and method for ", "An apparatus for ", "A smart device for ", "IoT based monitoring system for "]
    prop_titles = ["Research on ", "Development of ", "Investigation of ", "A framework for "]

    for u in faculty_users:
        # Each faculty has 2-5 entries
        num_entries = random.randint(2, 5)
        for _ in range(num_entries):
            rtype = random.choices(["Publication", "Patent", "Research Proposal"], weights=[0.7, 0.15, 0.15])[0]
            year = random.randint(2022, 2026)
            month = random.randint(1, 12)
            
            # Ensure academic year logic matches DB
            if month >= 6:
                ay = f"{year}-{str(year+1)[-2:]}"
            else:
                ay = f"{year-1}-{str(year)[-2:]}"
                
            entry = {
                "faculty_id": u["id"],
                "research_type": rtype,
                "month": month,
                "year": year,
                "academic_year": ay,
                "department": u["department"],
                "status": "Published" if rtype == "Publication" else ("Granted" if rtype == "Patent" else "Funded"),
                "is_nba_relevant": random.choice([True, False])
            }
            
            if rtype == "Publication":
                entry["title"] = random.choice(pub_titles) + random.choice(pub_topics) + " using " + random.choice(["AI", "ML", "IoT", "CNN", "RNN", "Big Data"])
                entry["journal_or_patent_office"] = random.choice(["IEEE Access", "International Journal of Computer Science", "Springer Nature", "Elsevier IoT", "ACM Transactions"])
                entry["indexing"] = random.choice(INDEXING)
                entry["impact_factor"] = round(random.uniform(0.5, 9.5), 2)
                entry["doi"] = f"10.10{random.randint(10,99)}/{random.randint(1000,9999)}.20{year}"
                entry["authors"] = f"{u['full_name']}, {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            elif rtype == "Patent":
                entry["title"] = random.choice(pat_titles) + random.choice(pub_topics)
                entry["journal_or_patent_office"] = random.choice(["US", "IN", "EP"]) + str(random.randint(1000000, 9999999))
                entry["patent_number"] = entry["journal_or_patent_office"]
            else: # Proposal
                entry["title"] = random.choice(prop_titles) + random.choice(pub_topics)
                entry["funding_agency"] = random.choice(["AICTE", "UGC", "DST", "VGST", "DRDO", "ISRO"])
                entry["funding_amount"] = random.randint(50, 500) * 1000
                entry["status"] = random.choice(["Under Review", "Funded", "Rejected"])
                
            entries.append(entry)
    return entries

def seed_supabase():
    print("Connecting to Supabase Admin...")
    admin_client = get_supabase_admin_client()
    users_config = generate_users_config()
    
    created_users = []
    
    print(f"Creating {len(users_config)} valid Supabase Auth users...")
    for u in users_config:
        try:
            # 1. Create real auth user
            res = admin_client.auth.admin.create_user({
                "email": u["email"],
                "password": u["password"],
                "email_confirm": True, # Automatically verified
                "user_metadata": {
                    "full_name": u["full_name"],
                    "department": u["department"],
                    "role": u["role"]
                }
            })
            if res.user:
                created_users.append({
                    "id": res.user.id,
                    "full_name": u["full_name"],
                    "department": u["department"],
                    "role": u["role"]
                })
                print(f"Created User: {u['email']} (Role: {u['role']})")
        except Exception as e:
            err = str(e)
            if "already exists" in err.lower() or "already registered" in err.lower():
                print(f"User {u['email']} already exists. Skipping auth creation.")
                # We need to fetch the existing user id to link entries.
                # Simplest way is to just generate the entries for those that succeed.
            else:
                print(f"Error creating {u['email']}: {e}")
        time.sleep(0.1) # slight delay to prevent rate limit
        
    print("Waiting 3 seconds for database triggers to generate profiles...")
    time.sleep(3)
    
    print(f"Generating realistic research entries...")
    entries = generate_entries(created_users)
    
    print(f"Inserting {len(entries)} entries into Supabase...")
    # Insert in batches of 50
    batch_size = 50
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i+batch_size]
        try:
            admin_client.table("research_entries").insert(batch).execute()
            print(f"Inserted batch {i//batch_size + 1} ({len(batch)} entries)")
        except Exception as e:
            print(f"Error inserting batch: {e}")
            
    print("\nDEMO SEEDING COMPLETE!")
    print("\nCredentials:")
    print("Password for ALL users: password123")
    print("Admin: iqac@hkbk.edu")
    print("R&D: rd@hkbk.edu")
    print("HoDs: hod.cse@hkbk.edu, hod.me@hkbk.edu, etc.")
    print("Faculty: faculty1@hkbk.edu to faculty14@hkbk.edu")

if __name__ == '__main__':
    seed_supabase()
