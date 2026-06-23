from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.secret_key = "secret123"

# ================= DATABASE =================
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


# ================= ROLE CHECK =================
def cek_admin():
    return session.get('role') == 'admin'

def cek_petugas():
    return session.get('role') == 'petugas'


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():

    error = None

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

            session['username'] = user['username']
            session['role'] = user['role']

            return redirect('/')

        error = "Username atau password salah"

    return render_template('login.html', error=error)


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ================= DASHBOARD =================
@app.route('/')
def index():

    if 'username' not in session:
        return redirect('/login')

    conn = get_db()

    q = request.args.get('q')

    if q:
        data = conn.execute(
            "SELECT * FROM penerima WHERE nama LIKE ? OR nik LIKE ?",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        data = conn.execute("SELECT * FROM penerima").fetchall()

    conn.close()

    return render_template(
        'index.html',
        data=data,
        role=session['role']
    )


# ================= TAMBAH DATA =================
@app.route('/tambah', methods=['GET', 'POST'])
def tambah():

    if not cek_admin():
        return "Akses ditolak!"

    if request.method == 'POST':

        nama = request.form['nama']
        nik = request.form['nik']
        alamat = request.form['alamat']
        jenis = request.form['jenis']

        conn = get_db()

        conn.execute(
            "INSERT INTO penerima (nama, nik, alamat, jenis_bantuan, status) VALUES (?,?,?,?,?)",
            (nama, nik, alamat, jenis, "Belum Disalurkan")
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('tambah.html')


# ================= UPDATE STATUS =================
@app.route('/update/<int:id>')
def update(id):

    if not cek_petugas():
        return "Akses ditolak!"

    conn = get_db()

    conn.execute(
        "UPDATE penerima SET status='Sudah Disalurkan' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')


# ================= HAPUS =================
@app.route('/hapus/<int:id>')
def hapus(id):

    if not cek_admin():
        return "Akses ditolak!"

    conn = get_db()

    conn.execute(
        "DELETE FROM penerima WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')


# ================= LAPORAN =================
@app.route('/laporan')
def laporan():

    conn = get_db()

    data = conn.execute("SELECT * FROM penerima").fetchall()

    total = conn.execute("SELECT COUNT(*) FROM penerima").fetchone()[0]

    sudah = conn.execute(
        "SELECT COUNT(*) FROM penerima WHERE status='Sudah Disalurkan'"
    ).fetchone()[0]

    belum = conn.execute(
        "SELECT COUNT(*) FROM penerima WHERE status='Belum Disalurkan'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "laporan.html",
        data=data,
        total=total,
        sudah=sudah,
        belum=belum
    )


# ================= DOWNLOAD CSV =================
@app.route('/download')
def download():

    conn = get_db()
    data = conn.execute("SELECT * FROM penerima").fetchall()
    conn.close()

    def generate():
        yield 'Nama,NIK,Alamat,Jenis,Status\n'
        for d in data:
            yield f"{d['nama']},{d['nik']},{d['alamat']},{d['jenis_bantuan']},{d['status']}\n"

    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=laporan.csv"}
    )


# ================= RUN =================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)