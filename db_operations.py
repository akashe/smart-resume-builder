import json
import sqlite3


def init_database():
    """Initialize SQLite database for storing resume data"""
    conn = sqlite3.connect('resume_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS resume_sections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  section_name TEXT,
                  content TEXT,
                  bullet_points TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS resume_profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  resume_json TEXT)''')
    
    conn.commit()
    conn.close()

def save_resume_to_db(resume_data):
    conn = sqlite3.connect('resume_data.db')
    c = conn.cursor()
    name = resume_data.get('contact', {}).get('name', 'Unknown')
    resume_json = json.dumps(resume_data)
    
    # Check if profile with this name exists
    c.execute("SELECT id FROM resume_profiles WHERE name=?", (name,))
    row = c.fetchone()
    if row:
        # Update existing profile
        c.execute("UPDATE resume_profiles SET resume_json=? WHERE name=?", (resume_json, name))
    else:
        # Insert new profile
        c.execute("INSERT INTO resume_profiles (name, resume_json) VALUES (?, ?)", (name, resume_json))
    conn.commit()
    conn.close()

def load_resume_profiles():
    conn = sqlite3.connect('resume_data.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM resume_profiles")
    profiles = c.fetchall()
    conn.close()
    return profiles

def get_resume_by_id(profile_id):
    conn = sqlite3.connect('resume_data.db')
    c = conn.cursor()
    c.execute("SELECT resume_json FROM resume_profiles WHERE id=?", (profile_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None