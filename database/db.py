import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_NAME = "spendly.db"

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
