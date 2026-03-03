# modules/database.py
# PostgreSQL version — works permanently on Render
# No more data loss on restart!

import os
import psycopg2
import psycopg2.extras
from datetime import datetime

# Render gives you a DATABASE_URL environment variable automatically
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db():
    """Open a new PostgreSQL connection."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def close_db(conn):
    """Close the connection."""
    if conn:
        conn.close()


def init_db():
    """Create tables if they don't exist, and create default admin."""
    conn = get_db()
    cur = conn.cursor()

    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')

    # Create analyses table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            resume_filename TEXT,
            ats_score REAL,
            matched_skills TEXT,
            missing_skills TEXT,
            career_suggestions TEXT,
            resume_tips TEXT,
            created_at TEXT
        )
    ''')

    # Create default admin if not exists
    cur.execute("SELECT id FROM users WHERE email = '24x51a3284@srecnandyal.edu.in'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, email, password, is_admin, created_at) VALUES (%s, %s, %s, %s, %s)",
            ('admin', '24x51a3284@srecnandyal.edu.in', 'Naik@2007', 1, datetime.now().isoformat())
        )
        print("✅ Default admin created: 24x51a3284@srecnandyal.edu.in / Naik@2007")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ PostgreSQL database initialized successfully")
