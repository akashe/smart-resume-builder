import json
import sqlite3

DB_PATH = 'resume_data.db'


def init_database():
    """Initialize SQLite database for storing resume data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS resume_sections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  section_name TEXT,
                  content TEXT,
                  bullet_points TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS resume_profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  name TEXT,
                  resume_json TEXT)''')

    # Backfill session_id for databases created before profiles were session-scoped
    c.execute("PRAGMA table_info(resume_profiles)")
    columns = {row[1] for row in c.fetchall()}
    if 'session_id' not in columns:
        c.execute("ALTER TABLE resume_profiles ADD COLUMN session_id TEXT")

    conn.commit()
    conn.close()


def save_resume_to_db(session_id, resume_data, profile_id=None, profile_name=None):
    """Save resume data to database, scoped to the current browser session.

    If profile_id is provided, update that profile (only if it belongs to this
    session). Otherwise save/update by name within this session.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    resume_json = json.dumps(resume_data)

    if profile_id is not None:
        c.execute(
            "UPDATE resume_profiles SET resume_json=? WHERE id=? AND session_id=?",
            (resume_json, profile_id, session_id)
        )
        updated_rows = c.rowcount
        conn.commit()
        conn.close()
        return updated_rows > 0
    else:
        name = profile_name or resume_data.get('contact', {}).get('name', 'Unknown')

        c.execute("SELECT id FROM resume_profiles WHERE name=? AND session_id=?", (name, session_id))
        row = c.fetchone()
        if row:
            c.execute("UPDATE resume_profiles SET resume_json=? WHERE id=?", (resume_json, row[0]))
        else:
            c.execute(
                "INSERT INTO resume_profiles (session_id, name, resume_json) VALUES (?, ?, ?)",
                (session_id, name, resume_json)
            )
        conn.commit()
        conn.close()
        return True


def load_resume_profiles(session_id):
    """List saved profiles belonging to this browser session only"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM resume_profiles WHERE session_id=?", (session_id,))
    profiles = c.fetchall()
    conn.close()
    return profiles


def get_resume_by_id(session_id, profile_id):
    """Load a profile's resume data, scoped to this browser session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT resume_json FROM resume_profiles WHERE id=? AND session_id=?", (profile_id, session_id))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


def save_resume_as_new_profile(session_id, resume_data, profile_name):
    """Save resume data as a new profile with specified name, scoped to this session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    resume_json = json.dumps(resume_data)

    c.execute("SELECT id FROM resume_profiles WHERE name=? AND session_id=?", (profile_name, session_id))
    row = c.fetchone()
    if row:
        conn.close()
        return False, "Profile name already exists"

    c.execute(
        "INSERT INTO resume_profiles (session_id, name, resume_json) VALUES (?, ?, ?)",
        (session_id, profile_name, resume_json)
    )
    conn.commit()
    profile_id = c.lastrowid
    conn.close()
    return True, profile_id
