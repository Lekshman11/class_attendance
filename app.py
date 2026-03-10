from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, time ,timedelta
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

app = Flask(__name__)
app.secret_key = "attendance_secret"

# Attendance time window
OPEN_TIME = time(7, 30)
CLOSE_TIME = time(9, 45)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"


# ----------------------------
# Home Page
# ----------------------------
@app.route("/")
def index():
    now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).time()
    if now < OPEN_TIME or now > CLOSE_TIME:
        return render_template("closed.html")

    return render_template("index.html")


# ----------------------------
# Get Name from Register No
# ----------------------------
@app.route("/get_name")
def get_name():

    reg_no = request.args.get("reg_no").upper()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM students WHERE reg_no=?",
        (reg_no,)
    )

    student = cursor.fetchone()
    conn.close()

    if student:
        return {"name": student[0]}

    return {"name": ""}


# ----------------------------
# Mark Attendance
# ----------------------------
@app.route("/mark", methods=["POST"])
def mark():

    reg_no = request.form["reg_no"].upper()

    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = str(ist_now.date())
    now_time = ist_now.strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if student exists
    cursor.execute(
        "SELECT name FROM students WHERE reg_no=?",
        (reg_no,)
    )

    student = cursor.fetchone()

    if not student:
        conn.close()
        return render_template("invalid.html")

    # Check duplicate attendance
    cursor.execute(
        "SELECT * FROM attendance WHERE reg_no=? AND date=?",
        (reg_no, today)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return render_template("already_marked.html")

    # Insert attendance
    cursor.execute(
        "INSERT INTO attendance(reg_no,date,time) VALUES(?,?,?)",
        (reg_no, today, now_time)
    )

    conn.commit()
    conn.close()

    return render_template("success.html", name=student[0])


# ----------------------------
# Admin Login
# ----------------------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

        return "Invalid Login"

    return render_template("admin_login.html")


# ----------------------------
# Admin Dashboard
# ----------------------------
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin_login")
        
        
    today = str((datetime.utcnow() + timedelta(hours=5, minutes=30)).date())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # present students
    cursor.execute("""
SELECT students.reg_no, students.name, attendance.time
FROM attendance
JOIN students
ON attendance.reg_no = students.reg_no
WHERE attendance.date = ?
ORDER BY students.reg_no
""", (today,))

    present = cursor.fetchall()

    present_count = len(present)

    # absent students
    cursor.execute("""
    SELECT reg_no, name
    FROM students
    WHERE reg_no NOT IN
    (
        SELECT reg_no
        FROM attendance
        WHERE date = ?
    )
    """, (today,))

    absent = cursor.fetchall()

    absent_count = len(absent)

    # attendance percentage
    if total_students > 0:
        percentage = round((present_count / total_students) * 100, 2)
    else:
        percentage = 0

    conn.close()

    return render_template(
        "admin.html",
        present=present,
        absent=absent,
        total_students=total_students,
        present_count=present_count,
        absent_count=absent_count,
        percentage=percentage
    )

# ----------------------------
# Logout
# ----------------------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin_login")

@app.route("/check-time")
def check_time():
    from datetime import datetime
    return str(datetime.utcnow() + timedelta(hours=5, minutes=30))

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
