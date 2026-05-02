from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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

    conn.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    if not conn.execute("SELECT * FROM user WHERE username='admin'").fetchone():
        conn.execute(
            "INSERT INTO user (username, password, role) VALUES (?,?,?)",
            ("admin", generate_password_hash("123"), "admin")
        )

    if not conn.execute("SELECT * FROM user WHERE username='petugas'").fetchone():
        conn.execute(
            "INSERT INTO user (username, password, role) VALUES (?,?,?)",
            ("petugas", generate_password_hash("123"), "petugas")
        )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)