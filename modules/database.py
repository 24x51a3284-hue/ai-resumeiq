# ============================================================
# modules/database.py
# Handles all database operations using SQLite
# SQLite is a simple file-based database — perfect for beginners!
# Your data is saved in a file called "resume_matcher.db"
# ============================================================

import sqlite3
from flask import g  # g = global object that Flask provides per request

# The database file will be created in the project folder
DATABASE = 'resume_matcher.db'


def get_db():
    """
    Get a connection to the database.
    Flask's 'g' object stores the connection during a request,
    so we don't open multiple connections.
    """
    if 'db' not in g:
        # Connect to the database file (creates it if it doesn't exist)
        g.db = sqlite3.connect(DATABASE)

        # This makes results return as dictionary-like objects
        # So you can do: result['username'] instead of result[0]
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Close the database connection when the request ends"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Create all the database tables if they don't exist yet.
    This is called once when the app starts.
    """
    # We need to import app here to avoid circular imports
    from flask import current_app

    # Use a direct connection for initialization
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # ---- TABLE 1: users ----
    # Stores login information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL,
            role       TEXT DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    ''')
    # Explanation:
    # INTEGER PRIMARY KEY AUTOINCREMENT = auto-numbered ID (1, 2, 3...)
    # TEXT NOT NULL = required text field
    # UNIQUE = no two users can have the same email
    # DEFAULT 'user' = everyone is a regular user unless specified

    # ---- TABLE 2: analyses ----
    # Stores each resume analysis result
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            resume_filename  TEXT NOT NULL,
            ats_score        REAL NOT NULL,
            matched_skills   TEXT,
            missing_skills   TEXT,
            job_description  TEXT,
            created_at       TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # REAL = decimal number (like 75.5)
    # TEXT = we store JSON strings for skill lists
    # FOREIGN KEY = links this table to the users table

    # ---- Create default admin user ----
    # Check if admin already exists
    existing_admin = cursor.execute(
        'SELECT id FROM users WHERE email = ?', ('admin@resumematcher.com',)
    ).fetchone()

    if not existing_admin:
        from datetime import datetime
        cursor.execute(
            'INSERT INTO users (username, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)',
            ('admin', 'admin@resumematcher.com', 'admin123', 'admin', datetime.now().isoformat())
        )
        print("✅ Default admin created: admin@resumematcher.com / admin123")

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")
