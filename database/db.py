import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_NAME = os.environ.get("DB_NAME", "spendly.db")

def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def seed_db():
    """Inserts sample data for development."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Insert demo user
    password_hash = generate_password_hash("demo123")
    cursor.execute('''
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    ''', ("Demo User", "demo@spendly.com", password_hash))
    
    user_id = cursor.lastrowid

    # Insert 8 sample expenses
    sample_expenses = [
        (user_id, 45.50, "Food", "2026-06-01", "Grocery shopping"),
        (user_id, 15.00, "Transport", "2026-06-02", "Bus fare"),
        (user_id, 120.00, "Bills", "2026-06-05", "Electricity bill"),
        (user_id, 30.00, "Health", "2026-06-07", "Pharmacy"),
        (user_id, 50.00, "Entertainment", "2026-06-10", "Movie night"),
        (user_id, 85.20, "Shopping", "2026-06-11", "New shoes"),
        (user_id, 10.00, "Other", "2026-06-12", "Donation"),
        (user_id, 25.00, "Food", "2026-06-13", "Lunch with friend")
    ]

    cursor.executemany('''
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_expenses)

    conn.commit()
    conn.close()

def create_user(name, email, password):
    """
    Hashes the password and inserts a new user into the database.
    Returns True on success, False if email already exists (IntegrityError).
    """
    password_hash = generate_password_hash(password)
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        ''', (name, email, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    """
    Retrieves a user by their email address.
    Returns the sqlite3.Row if found, or None otherwise.
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Retrieves a user by their ID."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def get_user_expenses(user_id):
    """Fetches all expenses for a user, ordered by date descending."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM expenses 
            WHERE user_id = ? 
            ORDER BY date DESC
        ''', (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def get_user_stats(user_id):
    """Calculates total spent, transaction count, and top category."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                COALESCE(SUM(amount), 0) as total_spent,
                COUNT(id) as count,
                (SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1) as top_category
            FROM expenses
            WHERE user_id = ?
        ''', (user_id, user_id))
        return cursor.fetchone()
    finally:
        conn.close()

def get_category_breakdown(user_id):
    """
    Step 5: Fetch category breakdown and calculate percentages.
    Calculates total spent per category and percentages, ensuring they sum to 100.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT category as name, SUM(amount) as amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY amount DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        
        total = sum(row['amount'] for row in rows)
        if total == 0:
            return []

        # Initial percentages calculation
        breakdown = []
        for row in rows:
            # Use floating point for precision before final adjustment
            percent = (row['amount'] / total) * 100
            breakdown.append({
                'name': row['name'],
                'amount': row['amount'],
                'percent': int(percent), # Initial integer floor
                'remainder': percent - int(percent),
                'class': row['name'].lower().replace(' ', '-')
            })
        
        # Adjust percentages to sum to exactly 100
        current_sum = sum(b['percent'] for b in breakdown)
        diff = 100 - current_sum
        
        # Sort by remainder to distribute the difference
        if diff > 0:
            breakdown.sort(key=lambda x: x['remainder'], reverse=True)
            for i in range(int(diff)):
                breakdown[i]['percent'] += 1
        
        # Re-sort by amount descending for the UI
        breakdown.sort(key=lambda x: x['amount'], reverse=True)
        
        # Remove temporary 'remainder' key
        for b in breakdown:
            del b['remainder']
            
        return breakdown
    finally:
        conn.close()
