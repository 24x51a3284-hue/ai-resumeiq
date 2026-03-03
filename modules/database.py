# modules/database.py — Updated with email verification columns
import psycopg2
import psycopg2.extras
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def close_db(conn):
    if conn:
        conn.close()

def init_db():
    conn = get_db()
    cur  = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            username      VARCHAR(100) NOT NULL,
            email         VARCHAR(200) UNIQUE NOT NULL,
            password      VARCHAR(200) NOT NULL,
            is_admin      BOOLEAN DEFAULT FALSE,
            is_verified   BOOLEAN DEFAULT FALSE,
            verify_token  VARCHAR(200),
            token_expires VARCHAR(50),
            created_at    VARCHAR(50)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER REFERENCES users(id),
            resume_filename  VARCHAR(300),
            ats_score        FLOAT,
            matched_skills   TEXT,
            missing_skills   TEXT,
            career_suggestions TEXT,
            resume_tips      TEXT,
            job_description  TEXT,
            created_at       VARCHAR(50)
        )
    ''')

    # Add new columns if they don't exist (for existing databases)
    for col, definition in [
        ('is_verified',   'BOOLEAN DEFAULT FALSE'),
        ('verify_token',  'VARCHAR(200)'),
        ('token_expires', 'VARCHAR(50)')
    ]:
        try:
            cur.execute(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {definition}')
        except Exception:
            pass

    # Create default admin (already verified)
    cur.execute('SELECT id FROM users WHERE email = %s', ('24x51a3284@srecnandyal.edu.in',))
    if not cur.fetchone():
        cur.execute(
            '''INSERT INTO users (username, email, password, is_admin, is_verified, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)''',
            ('admin', '24x51a3284@srecnandyal.edu.in', 'Naik@2007', True, True,
             __import__('datetime').datetime.now().isoformat())
        )
    else:
        # Make sure existing admin is verified
        cur.execute(
            'UPDATE users SET is_verified = TRUE WHERE email = %s',
            ('24x51a3284@srecnandyal.edu.in',)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized with email verification support")