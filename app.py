import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "safeher.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            relationship TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS sos_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            latitude REAL,
            longitude REAL,
            message TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Recorded',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Submitted',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)


def current_user():
    if "user_id" not in session:
        return None
    with get_db() as db:
        return db.execute("SELECT id, name, email, role FROM users WHERE id=?",
                          (session["user_id"],)).fetchone()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_user():
    return {"logged_user": current_user()}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                    (name, email, generate_password_hash(password), "user", datetime.now().isoformat(timespec="seconds"))
                )
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back!", "success")
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    with get_db() as db:
        contacts = db.execute("SELECT * FROM contacts WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
        alerts = db.execute("SELECT * FROM sos_alerts WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],)).fetchall()
        reports = db.execute("SELECT * FROM reports WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],)).fetchall()
    return render_template("dashboard.html", contacts=contacts, alerts=alerts, reports=reports)


@app.route("/contacts", methods=["GET", "POST"])
@login_required
def contacts():
    user = current_user()
    with get_db() as db:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            relationship = request.form.get("relationship", "").strip()
            if name and phone:
                db.execute("INSERT INTO contacts(user_id,name,phone,relationship) VALUES(?,?,?,?)",
                           (user["id"], name, phone, relationship))
                flash("Emergency contact added.", "success")
            else:
                flash("Name and phone number are required.", "danger")
            return redirect(url_for("contacts"))
        rows = db.execute("SELECT * FROM contacts WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
    return render_template("contacts.html", contacts=rows)


@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
@login_required
def delete_contact(contact_id):
    with get_db() as db:
        db.execute("DELETE FROM contacts WHERE id=? AND user_id=?", (contact_id, session["user_id"]))
    flash("Contact deleted.", "info")
    return redirect(url_for("contacts"))


@app.route("/sos", methods=["POST"])
@login_required
def sos():
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data["latitude"]) if data.get("latitude") is not None else None
        lon = float(data["longitude"]) if data.get("longitude") is not None else None
    except (TypeError, ValueError):
        return jsonify(success=False, message="Invalid coordinates."), 400
    message = (data.get("message") or "Emergency alert recorded by user.")[:500]
    with get_db() as db:
        db.execute(
            "INSERT INTO sos_alerts(user_id,latitude,longitude,message,created_at) VALUES(?,?,?,?,?)",
            (session["user_id"], lat, lon, message, datetime.now().isoformat(timespec="seconds"))
        )
    return jsonify(success=True, message="SOS alert recorded in SafeHer. This demo has not contacted emergency services.")


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        if not category or len(description) < 10:
            flash("Choose a category and provide at least 10 characters of description.", "danger")
        else:
            with get_db() as db:
                db.execute("INSERT INTO reports(user_id,category,description,location,created_at) VALUES(?,?,?,?,?)",
                           (session["user_id"], category, description, location,
                            datetime.now().isoformat(timespec="seconds")))
            flash("Your report has been submitted.", "success")
            return redirect(url_for("dashboard"))
    return render_template("report.html")


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    with get_db() as db:
        users = db.execute("SELECT id,name,email,role,created_at FROM users ORDER BY id DESC").fetchall()
        alerts = db.execute("""SELECT sos_alerts.*, users.name AS user_name, users.email
                               FROM sos_alerts JOIN users ON users.id=sos_alerts.user_id
                               ORDER BY sos_alerts.id DESC""").fetchall()
        reports = db.execute("""SELECT reports.*, users.name AS user_name, users.email
                                FROM reports JOIN users ON users.id=reports.user_id
                                ORDER BY reports.id DESC""").fetchall()
    return render_template("admin.html", users=users, alerts=alerts, reports=reports)


@app.route("/admin/report-status/<int:report_id>", methods=["POST"])
@login_required
@admin_required
def update_report_status(report_id):
    status = request.form.get("status", "Submitted")
    if status not in ("Submitted", "Under Review", "Resolved"):
        abort(400)
    with get_db() as db:
        db.execute("UPDATE reports SET status=? WHERE id=?", (status, report_id))
    flash("Report status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page you requested was not found."), 404


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
