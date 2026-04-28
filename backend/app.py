from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.secret_key = "secret123"

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

def cek_login():
    return 'login' in session

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "123":
            session['login'] = True
            return redirect('/')
        else:
            return "Login gagal!"

    return render_template("login.html")

@app.route('/')
def index():
    if not cek_login():
        return redirect('/login')

    return "Dashboard"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)