# init_db.py (run once to create admin user and db)
from app import init_db, add_user
init_db()
# add_user('user1','userpass','user')  # call as needed
print("DB initialized")
