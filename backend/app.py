from flask import Flask
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS penerima (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            nik TEXT,
            alamat TEXT,
            jenis_bantuan TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)