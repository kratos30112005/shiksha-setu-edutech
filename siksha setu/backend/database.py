import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shikshasetu.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_data TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cognitive_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cognitive_score INTEGER,
            difficulty_level TEXT,
            average_accuracy REAL,
            total_attempts INTEGER,
            weak_topics TEXT,
            strong_topics TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER,
            total_questions INTEGER,
            topic TEXT,
            difficulty TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question TEXT,
            subject TEXT,
            topic TEXT,
            correct_answer TEXT,
            user_answer TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            text_content TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def create_user(name, email, password, default_profile):
    conn = get_db()
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        profile_json = json.dumps(default_profile)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, profile_data) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, profile_json)
        )
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Email already exists"
    finally:
        conn.close()

def verify_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return True, dict(user)
    return False, "Invalid email or password"

def get_user_profile(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, profile_data FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

def update_user_profile(email, profile_data):
    conn = get_db()
    cursor = conn.cursor()
    profile_json = json.dumps(profile_data)
    cursor.execute(
        "UPDATE users SET profile_data = ? WHERE email = ?",
        (profile_json, email)
    )
    conn.commit()
    conn.close()


def save_profile_to_db(email, profile):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    user_id = row["id"] if isinstance(row, sqlite3.Row) or hasattr(row, "__getitem__") else row[0]

    weak_topics = json.dumps(profile.get("weak_topics", {}))
    strong_topics = json.dumps(profile.get("strong_topics", {}))

    cursor.execute(
        """
        INSERT OR REPLACE INTO cognitive_profiles (
            id, user_id, cognitive_score, difficulty_level, average_accuracy, total_attempts, weak_topics, strong_topics
        ) VALUES (
            (SELECT id FROM cognitive_profiles WHERE user_id = ?),
            ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            user_id,
            user_id,
            profile.get("cognitive_score"),
            profile.get("difficulty_level"),
            profile.get("average_accuracy"),
            profile.get("total_attempts"),
            weak_topics,
            strong_topics,
        ),
    )

    conn.commit()
    conn.close()
    return True


def load_profile_from_db(email):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    user_id = row["id"] if isinstance(row, sqlite3.Row) or hasattr(row, "__getitem__") else row[0]

    cursor.execute("SELECT * FROM cognitive_profiles WHERE user_id = ?", (user_id,))
    prof_row = cursor.fetchone()
    conn.close()

    if not prof_row:
        return None

    weak_topics = prof_row["weak_topics"]
    strong_topics = prof_row["strong_topics"]

    return {
        "cognitive_score": prof_row["cognitive_score"],
        "difficulty_level": prof_row["difficulty_level"],
        "average_accuracy": prof_row["average_accuracy"],
        "total_attempts": prof_row["total_attempts"],
        "weak_topics": json.loads(weak_topics) if weak_topics else {},
        "strong_topics": json.loads(strong_topics) if strong_topics else {},
    }


# Initialize DB on import
init_db()
