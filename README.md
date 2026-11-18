# SafeHer – Women Safety Management System

SafeHer is a Flask + SQLite web application for managing emergency contacts, recording SOS alerts with optional GPS coordinates, and submitting safety incident reports.

## Features
- User registration, login and logout
- Password hashing
- User dashboard
- Emergency contact management
- SOS alert recording with browser geolocation
- Leaflet/OpenStreetMap location display
- Incident reporting
- Admin dashboard for users, SOS records and reports
- Admin report-status updates

## Important safety limitation
This is an academic/demo project. The SOS button records an alert in the SafeHer database. It does **not** call police, send SMS, notify emergency contacts, or guarantee emergency response. Do not rely on this demo in a real emergency. In an emergency in India, call 112 directly.

## Requirements
- Python 3.10+
- VS Code (recommended)
- Git

## Run locally (Windows PowerShell)
```powershell
cd safeher_project
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## Create an admin account
Open a second terminal in the project folder, activate the same virtual environment, then run:
```powershell
python create_admin.py
```
Enter the admin name, email and password when prompted. Do not make a normal user an admin by changing a public signup form.

## GitHub upload
1. Create a new empty repository on GitHub, for example `SafeHer-Women-Safety-Management`.
2. Open a terminal in this project folder.
3. Run:
```bash
git init
git add .
git commit -m "Initial SafeHer women safety management system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/SafeHer-Women-Safety-Management.git
git push -u origin main
```
Replace `YOUR-USERNAME` with your GitHub username.

Never upload `safeher.db`, `.env`, passwords, or API keys. `.gitignore` excludes the local database and environment files.

## Deploying on Render (optional)
- Push the project to GitHub.
- In Render, create a new **Web Service** and connect the repository.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add environment variable `SECRET_KEY` with a long random value.
- Set `FLASK_DEBUG` to `0` or leave it unset.

**Database note:** SQLite stored on an ordinary ephemeral Render filesystem can be lost on redeploy/restart. For a persistent deployed app, migrate to a managed PostgreSQL database or configure a persistent disk and back up data. Browser geolocation generally requires HTTPS in deployment (localhost is also permitted by modern browsers).

## Project structure
```text
safeher_project/
├── app.py
├── create_admin.py
├── requirements.txt
├── Procfile
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── contacts.html
│   ├── report.html
│   ├── admin.html
│   └── error.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Security notes before real-world use
This is a learning project, not a production emergency-response service. Before handling real users or sensitive incident data, add CSRF protection, rate limiting, secure account recovery, audit logging, stronger privacy controls, encrypted backups, retention/deletion policies, and a real notification provider with consent and tested delivery. Never promise that an SOS alert has reached authorities unless that integration has been implemented and verified.
