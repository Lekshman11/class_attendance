# 🎓 AI&DS Attendance Portal

A mobile-first web attendance system for the **AI & Data Science** department, built with **Flask** and **SQLite**.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?style=flat-square&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

- 📱 **Mobile-first UI** — designed for phone users, works perfectly on any screen size
- ⚡ **Live name lookup** — enter your register number and your name auto-fills instantly
- 🛡️ **Duplicate prevention** — each student can mark attendance only once per day
- ⏰ **Time-gated access** — portal is only open during configured hours (8 AM – 4:45 PM)
- 📊 **Admin dashboard** — real-time stats (total / present / absent / %), with side-by-side tables
- 🔐 **Admin login** — protected session-based admin area

---

## 🖼️ Screenshots

| Student Page | Admin Dashboard |
|---|---|
| Centered card with register input, auto-filled name, and large Mark Attendance button | Sticky topbar, 4-stat grid, present & absent tables side by side |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/attendance_portal.git
cd attendance_portal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open your browser at **http://localhost:5000**

---

## 📁 Project Structure

```
attendance_portal/
├── app.py                  # Flask backend — all routes and logic
├── attendance.db           # SQLite database (students + attendance tables)
├── requirements.txt        # Python dependencies
├── render.yaml             # Render.com deployment config
├── static/
│   └── style.css           # Complete CSS design system
└── templates/
    ├── index.html          # Student attendance page
    ├── admin_login.html    # Admin login page
    ├── admin.html          # Admin dashboard
    ├── success.html        # Attendance confirmed page
    └── closed.html         # Portal closed page
```

---

## 🛣️ Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Student attendance page (time-gated) |
| `/get_name` | GET | JSON API — fetch student name by register number |
| `/mark` | POST | Submit attendance |
| `/admin_login` | GET / POST | Admin login |
| `/admin` | GET | Admin dashboard (session-protected) |
| `/logout` | GET | Admin logout |

---

## 🗄️ Database Schema

```sql
-- Students table
CREATE TABLE students (
    reg_no TEXT PRIMARY KEY,
    name   TEXT NOT NULL
);

-- Attendance table
CREATE TABLE attendance (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_no TEXT NOT NULL,
    date   TEXT NOT NULL,
    time   TEXT NOT NULL
);
```

---

## ☁️ Deploying to Render

1. Push this repo to GitHub
2. On [Render.com](https://render.com), create a new **Web Service**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml` and configure the build

> **Note:** Render's free tier uses an ephemeral filesystem — the SQLite database resets on each deploy. For production use, migrate to [Render PostgreSQL](https://render.com/docs/databases) or another persistent database.

---

## ⚙️ Configuration

Edit these constants at the top of `app.py` to customise the portal:

```python
OPEN_TIME  = time(8, 0)    # Portal opens at 8:00 AM
CLOSE_TIME = time(16, 45)  # Portal closes at 4:45 PM

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"    # Change this before deploying!
```

---

## 📦 Dependencies

```
Flask
gunicorn
```

---

## 📄 License

MIT — free to use and modify.
