import random
import string
from werkzeug.security import generate_password_hash
from database.db import get_db

def generate_indian_user():
    first_names = ["Rahul", "Priya", "Amit", "Sunita", "Vikram", "Ananya", "Arjun", "Kavita", "Rohan", "Meera", "Siddharth", "Ishani", "Karan", "Zara", "Aditya"]
    last_names = ["Sharma", "Gupta", "Patel", "Reddy", "Singh", "Kumar", "Joshi", "Nair", "Iyer", "Das", "Chatterjee", "Kulkarni", "Malhotra", "Verma", "Choudhury"]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    name = f"{first_name} {last_name}"
    
    suffix = random.randint(10, 999)
    email_base = f"{first_name.lower()}.{last_name.lower()}{suffix}"
    email = f"{email_base}@gmail.com"
    
    return name, email

def seed_user():
    conn = get_db()
    cursor = conn.cursor()
    
    while True:
        name, email = generate_indian_user()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is None:
            break
            
    password_hash = generate_password_hash("password123")
    
    cursor.execute('''
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    ''', (name, email, password_hash))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"User Seeded Successfully:")
    print(f"ID: {user_id}")
    print(f"Name: {name}")
    print(f"Email: {email}")

if __name__ == "__main__":
    seed_user()
