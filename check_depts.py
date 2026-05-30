import sys
sys.path.append('.')
from database.queries import fetch_departments

depts = fetch_departments()
for d in depts:
    print(d)
