from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, timedelta
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

# Attendance time window (IST = UTC+05:30)
OPEN_TIME_H, OPEN_TIME_M   = 7, 30
CLOSE_TIME_H, CLOSE_TIME_M = 9, 45

# Admin credentials (use env vars in production)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234")


# ----------------------------
# DB Initialisation Helper
# ----------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Add status column if it doesn't exist (safe migration)."""
    conn = get_db()
    cursor = conn.cursor()
    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            reg_no TEXT PRIMARY KEY,
            name   TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT NOT NULL,
            date   TEXT NOT NULL,
            time   TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'present'
        )
    """)
    # Safe migration: add status column to existing db if missing
    try:
        cursor.execute("ALTER TABLE attendance ADD COLUMN status TEXT NOT NULL DEFAULT 'present'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()


init_db()


# ----------------------------
# Home Page
# ----------------------------
@app.route("/")
def index():
    now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).time()
    open_str  = f"{OPEN_TIME_H:02d}:{OPEN_TIME_M:02d} {'AM' if OPEN_TIME_H < 12 else 'PM'}"
    close_str = f"{CLOSE_TIME_H % 12 or 12:02d}:{CLOSE_TIME_M:02d} {'AM' if CLOSE_TIME_H < 12 else 'PM'}"
    if now.hour < OPEN_TIME_H or (now.hour == OPEN_TIME_H and now.minute < OPEN_TIME_M):
        return render_template("closed.html", open_time=open_str, close_time=close_str)
    if now.hour > CLOSE_TIME_H or (now.hour == CLOSE_TIME_H and now.minute > CLOSE_TIME_M):
        return render_template("closed.html", open_time=open_str, close_time=close_str)
    return render_template("index.html")


# ----------------------------
# Get Name from Register No
# ----------------------------
@app.route("/get_name")
def get_name():
    reg_no = request.args.get("reg_no", "").upper().strip()
    if not reg_no:
        return {"name": ""}
    conn = get_db()
    student = conn.execute(
        "SELECT name FROM students WHERE reg_no=?", (reg_no,)
    ).fetchone()
    conn.close()
    return {"name": student["name"] if student else ""}


# ----------------------------
# Mark Attendance (Present or Absent)
# ----------------------------
@app.route("/mark", methods=["POST"])
def mark():
    reg_no = request.form.get("reg_no", "").upper().strip()
    status = request.form.get("status", "present")  # 'present' or 'absent'

    if status not in ("present", "absent"):
        status = "present"

    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = str(now.date())
    now_time = now.strftime("%H:%M:%S")

    conn = get_db()

    student = conn.execute(
        "SELECT name FROM students WHERE reg_no=?", (reg_no,)
    ).fetchone()

    if not student:
        conn.close()
        return render_template("invalid.html")

    existing = conn.execute(
        "SELECT status FROM attendance WHERE reg_no=? AND date=?",
        (reg_no, today)
    ).fetchone()

    if existing:
        conn.close()
        return render_template("already_marked.html", prev_status=existing["status"])

    conn.execute(
        "INSERT INTO attendance(reg_no, date, time, status) VALUES(?,?,?,?)",
        (reg_no, today, now_time, status)
    )
    conn.commit()
    conn.close()

    return render_template("success.html", name=student["name"], status=status)


# ----------------------------
# Admin Login
# ----------------------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        error = "Invalid username or password."
    return render_template("admin_login.html", error=error)


# ----------------------------
# Admin Dashboard
# ----------------------------
@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/admin_login")

    today = str((datetime.utcnow() + timedelta(hours=5, minutes=30)).date())
    # Accept date filter from query param; default to today
    filter_date = request.args.get("date", today)

    conn = get_db()

    # Total students
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    # Present students (status = 'present')
    present = conn.execute("""
        SELECT s.reg_no, s.name, a.time
        FROM attendance a
        JOIN students s ON a.reg_no = s.reg_no
        WHERE a.date = ? AND a.status = 'present'
        ORDER BY s.reg_no
    """, (filter_date,)).fetchall()

    # Self-marked absent students (status = 'absent')
    absent_marked = conn.execute("""
        SELECT s.reg_no, s.name, a.time
        FROM attendance a
        JOIN students s ON a.reg_no = s.reg_no
        WHERE a.date = ? AND a.status = 'absent'
        ORDER BY s.reg_no
    """, (filter_date,)).fetchall()

    # Students who haven't posted anything
    not_posted = conn.execute("""
        SELECT reg_no, name
        FROM students
        WHERE reg_no NOT IN (
            SELECT reg_no FROM attendance WHERE date = ?
        )
        ORDER BY reg_no
    """, (filter_date,)).fetchall()

    conn.close()

    present_count    = len(present)
    absent_count     = len(absent_marked)
    not_posted_count = len(not_posted)

    percentage = round((present_count / total_students) * 100, 2) if total_students > 0 else 0

    return render_template(
        "admin.html",
        present=present,
        absent_marked=absent_marked,
        not_posted=not_posted,
        total_students=total_students,
        present_count=present_count,
        absent_count=absent_count,
        not_posted_count=not_posted_count,
        percentage=percentage,
        filter_date=filter_date,
        today=today,
    )


# ----------------------------
# Logout
# ----------------------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin_login")


# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
