# Database Setup Implementation Plan

## Objective
Implement the database foundation for the Spendly Expense Tracker according to the specifications in `.gemini/specs/database-setup.md`.

## Key Files & Context
- `database/db.py`: Where the database logic will reside.
- `app.py`: Where the database initialization will be called on startup.

## Implementation Steps

### 1. `database/db.py`
**Imports:**
- `import sqlite3`
- `from werkzeug.security import generate_password_hash`

**Constants:**
- `DB_NAME = "spendly.db"`

**Functions:**
- **`get_db()`**:
  - Connect to `DB_NAME` using `sqlite3.connect()`.
  - Set `row_factory = sqlite3.Row`.
  - Execute `PRAGMA foreign_keys = ON;`.
  - Return the connection.

- **`init_db()`**:
  - Open a connection using `get_db()`.
  - Create the `users` table:
    - `id` INTEGER PRIMARY KEY AUTOINCREMENT
    - `name` TEXT NOT NULL
    - `email` TEXT UNIQUE NOT NULL
    - `password_hash` TEXT NOT NULL
    - `created_at` TEXT DEFAULT CURRENT_TIMESTAMP
  - Create the `expenses` table:
    - `id` INTEGER PRIMARY KEY AUTOINCREMENT
    - `user_id` INTEGER NOT NULL (FOREIGN KEY referencing `users.id`)
    - `amount` REAL NOT NULL
    - `category` TEXT NOT NULL
    - `date` TEXT NOT NULL
    - `description` TEXT
    - `created_at` TEXT DEFAULT CURRENT_TIMESTAMP
  - Commit and close the connection.

- **`seed_db()`**:
  - Open a connection using `get_db()`.
  - Check if any users exist (`SELECT COUNT(*) FROM users`). If count > 0, return early.
  - Insert Demo User:
    - name: "Demo User"
    - email: "demo@spendly.com"
    - password_hash: `generate_password_hash("demo123")`
  - Get the inserted user's ID.
  - Insert 8 sample expenses for this user with various fixed categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other), spread across current month dates in `YYYY-MM-DD` format.
  - Commit and close.

### 2. `app.py`
- **Imports:** Add `from database.db import init_db, seed_db` to the top of the file.
- **Startup Logic:**
  - Create an app context (`with app.app_context():`) and call `init_db()` and `seed_db()` right after the Flask app is initialized (before the routes).

## Verification & Testing
- Run `python app.py` to ensure the server starts without errors.
- Verify `spendly.db` is created in the project root.
- Use the SQLite CLI (`sqlite3 spendly.db`) to verify schema, foreign key enforcement, and seeded data.
- Ensure restarting `app.py` does not duplicate seed data.
