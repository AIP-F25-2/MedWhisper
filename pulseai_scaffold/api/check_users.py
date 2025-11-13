#!/usr/bin/env python3
"""
Utility script to check users in the database.
WARNING: This is a development/testing script. Do not use in production.
"""

import os
import sys
from dotenv import load_dotenv
from database import UserDatabase

# Load environment variables
load_dotenv()

# Create a new database instance
db = UserDatabase()

# Get all users
users = db.conn.execute("SELECT id, email, full_name FROM users").fetchall()
print("All users in database:")
for user in users:
    print(f"ID: {user[0]}, Email: {user[1]}, Name: {user[2]}")

# Test authentication - use environment variables or command line arguments
if len(sys.argv) >= 3:
    email = sys.argv[1]
    password = sys.argv[2]
else:
    # Use environment variables if available, otherwise skip test
    email = os.getenv("TEST_EMAIL")
    password = os.getenv("TEST_PASSWORD")
    
    if not email or not password:
        print("\nTo test authentication, provide email and password as arguments:")
        print("  python check_users.py <email> <password>")
        print("\nOr set TEST_EMAIL and TEST_PASSWORD environment variables.")
        sys.exit(0)

auth_result = db.authenticate_user(email, password)
print(f"\nAuthentication for {email}: {'SUCCESS' if auth_result else 'FAILED'}")
