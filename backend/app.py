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

def cek_login():
    return 'login' in session

def cek_admin():
    return session.get('role') == 'admin'

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM user WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['login'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/')
        else:
            return render_template("login.html", error="Login gagal!")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if not cek_login():
        return redirect('/login')

    return "Dashboard"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)