import sqlite3

DB_PATH = "audio.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            audio_link TEXT NOT NULL UNIQUE,
            file_id TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_audio(name, audio_link, file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO audios (name, audio_link, file_id) VALUES (?, ?, ?)", (name, audio_link, file_id))
    conn.commit()
    conn.close()

def search_audios(query):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    words = query.lower().split()
    like_clause = " AND ".join(["name LIKE ?"] * len(words))
    params = ['%' + word + '%' for word in words]

    c.execute(f"""
        SELECT name, audio_link FROM audios
        WHERE {like_clause}
        LIMIT 50
    """, params)

    results = c.fetchall()
    conn.close()
    return results




def get_audio_by_name(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT name, audio_link FROM audios
        WHERE name = ?
        LIMIT 1
    """, (name,))
    result = c.fetchone()
    conn.close()
    return result


def get_all_audios():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, audio_link FROM audios")
    results = c.fetchall()
    conn.close()
    return results