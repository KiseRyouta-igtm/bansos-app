from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
            status TEXT,
            pendapatan INTEGER,
            pekerjaan TEXT,
            usia INTEGER,
            lansia TEXT,
            foto_ktp TEXT,
            foto_rumah TEXT
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

def cek_admin():
    return session.get('role') == 'admin'

def cek_petugas():
    return session.get('role') == 'petugas'


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


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/')
def index():

    if 'username' not in session:
        return redirect('/login')

    conn = get_db()

    data = conn.execute("SELECT * FROM penerima").fetchall()

    conn.close()

    return render_template(
        'index.html',
        data=data,
        role=session['role']
    )

@app.route('/tambah', methods=['GET', 'POST'])
def tambah():

    if not cek_admin():
        return "Akses ditolak!"

    if request.method == 'POST':

        nama = request.form['nama']
        nik = request.form['nik']
        alamat = request.form['alamat']
        jenis = request.form['jenis']
        pendapatan = request.form['pendapatan']
        pekerjaan = request.form['pekerjaan']
        usia = int(request.form['usia'])

        if usia >= 60:
            lansia = "Ya"
        else:
            lansia = "Tidak"

        foto_ktp = request.files['foto_ktp']
        foto_rumah = request.files['foto_rumah']

        ktp_name = str(uuid.uuid4()) + "_" + secure_filename(foto_ktp.filename)
        rumah_name = str(uuid.uuid4()) + "_" + secure_filename(foto_rumah.filename)

        foto_ktp.save(os.path.join(app.config['UPLOAD_FOLDER'], ktp_name))
        foto_rumah.save(os.path.join(app.config['UPLOAD_FOLDER'], rumah_name))

        conn = get_db()

        conn.execute("""
            INSERT INTO penerima
            (
                nama,
                nik,
                alamat,
                jenis_bantuan,
                status,
                pendapatan,
                pekerjaan,
                usia,
                lansia,
                foto_ktp,
                foto_rumah
            )
            VALUES
            (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            nama,
            nik,
            alamat,
            jenis,
            "Belum Disalurkan",
            pendapatan,
            pekerjaan,
            usia,
            lansia,
            ktp_name,
            rumah_name
        ))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('tambah.html')

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

@app.route('/detail/<int:id>')
def detail(id):

    if 'username' not in session:
        return redirect('/login')

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM penerima WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    if data is None:
        return "Data tidak ditemukan"

    return render_template("detail.html", data=data)

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)