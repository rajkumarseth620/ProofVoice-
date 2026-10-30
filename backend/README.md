# PROOFVOICE Backend — Django REST API & Multi-Tenant Platform

> **"Your Voice. Your Campus. Your Solution."**
> Enterprise-grade Django REST backend powering the ProofVoice grievance resolution platform. Transforms student campus complaints into formal applications addressed to the Dean or designated authorities, supports review-before-submit workflows, and integrates with Gnani AI for voice complaints.

---

## 1. Architecture & Tech Stack

- **Framework**: Python 3.12+ / Python 3.13 + Django 6.0 + Django REST Framework 3.18
- **Primary Database**: MySQL 8.0+ via `mysqlclient` (dual-mode with SQLite for instant local test suites)
- **Authentication**: Token-based REST Authentication (`rest_framework.authtoken`) & Session Authentication
- **Multi-Tenancy**: Isolated multi-institutional architecture (Apex Tech, Horizon Univ, Greenfield Poly)
- **AI Integration**: Gnani AI Prisma Speech-to-Text (`/stt/v3`) & Timbre Text-to-Speech (`/api/v1/tts/inference`)
- **CORS/Security**: `django-cors-headers` configured for localhost:3000 & localhost:5173

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── init_db.sql                # MySQL DB and user initialization script
├── config/                    # Project settings & URL routing
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/              # Custom User, StudentProfile, AdministratorProfile
│   ├── institutions/          # Multi-tenant Institutions, Departments, Categories, Recipient Config
│   ├── complaints/            # Grievances, Status History, Attachments, Formal Letter Generator
│   ├── notifications/         # Real-time lifecycle alerts
│   ├── integrations/          # Gnani AI Prisma STT, Timbre TTS & Audit Logging
│   └── analytics/             # Student, Admin, and Institutional Metrics
└── tests/                     # 15 automated security, boundary, and workflow tests
```

---

## 2. Prerequisites

- **Python**: 3.12 or 3.13 (Python 3.13.7 verified)
- **MySQL Server**: MySQL 8.0+ (Service name: `MySQL80`)
- **Node.js**: Optional (frontend static server running on port 3000)

---

## 3. Installation & Database Setup (Windows PowerShell)

### Step 1: Clone / Navigate to Backend
```powershell
cd c:\Users\RAJ\OneDrive\Desktop\ProofVoice\backend
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create venv
python -m venv venv

# Activate venv in PowerShell
.\venv\Scripts\Activate.ps1
```
*(On Linux/macOS: `python3 -m venv venv && source venv/bin/activate`)*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure MySQL Database
Run the provided `init_db.sql` script using MySQL command line client:
```powershell
# Using MySQL CLI with your root password
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < init_db.sql
```
This script executes:
```sql
CREATE DATABASE IF NOT EXISTS proofvoice_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'proofvoice_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON proofvoice_db.* TO 'proofvoice_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Ensure `.env` matches your database credentials:
```ini
DJANGO_SECRET_KEY=proofvoice-dev-secret-key-super-secure-2026-v1
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DB_ENGINE=django.db.backends.mysql
DB_NAME=proofvoice_db
DB_USER=proofvoice_user
DB_PASSWORD=your_mysql_password_here
DB_HOST=127.0.0.1
DB_PORT=3306

# Set to True for testing without running MySQL, False for primary MySQL database
USE_SQLITE_FOR_TESTS=False

FRONTEND_ORIGIN=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173

# Gnani AI (https://docs.gnani.ai/)
GNANI_API_KEY=your_gnani_api_key_here
GNANI_API_BASE_URL=https://api.vachana.ai
```

---

## 4. Running Migrations & Seeding Demo Data

```powershell
# Run all Django migrations
python manage.py migrate

# Seed sample universities, departments, categories, admins, students & complaints
python manage.py seed_demo_data
```

### Default Seed Accounts
| Role | Email | Password | Affiliation / Details |
|---|---|---|---|
| **Superadmin** | `superadmin@proofvoice.edu` | `Admin@12345` | Platform-wide root access |
| **Admin** | `admin@apex.edu` | `Admin@12345` | Apex Institute of Technology (Dean) |
| **Admin** | `admin@horizon.edu` | `Admin@12345` | Horizon State University (Registrar) |
| **Student** | `student@apex.edu` | `Student@12345` | Priya Sharma (B.Tech CSE, Sem 6, AJU/22/0451) |
| **Student** | `student@horizon.edu` | `Student@12345` | Rahul Verma (B.Sc Physics, Sem 4, HSU/23/1029) |

---

## 5. Starting the Backend Server

```powershell
python manage.py runserver 127.0.0.1:8000
```
API Root: `http://127.0.0.1:8000/api/v1/`  
Admin Panel: `http://127.0.0.1:8000/admin/`

---

## 6. Starting the Frontend

In a separate terminal:
```powershell
cd c:\Users\RAJ\OneDrive\Desktop\ProofVoice
npx serve -l 3000 .
```
Frontend URL: `http://localhost:3000/`

---

## 7. REST API Endpoints Overview

### Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/register/student/` — Register new student (auto-creates StudentProfile)
- `POST /api/v1/auth/register/institution-admin/` — Register admin access request (status PENDING)
- `POST /api/v1/auth/login/` — Authenticate and receive auth token
- `POST /api/v1/auth/logout/` — Invalidate auth token
- `GET /api/v1/auth/me/` — Current user context and profile
- `GET / PATCH /api/v1/auth/profile/` — View or update user profile

### Multi-Tenancy & Institutions (`/api/v1/institutions/`)
- `GET /api/v1/institutions/` — List active verified institutions
- `GET /api/v1/institutions/me/` — Current user's institution
- `GET /api/v1/institutions/me/departments/` — Institution's departments
- `GET /api/v1/institutions/me/categories/` — Institution's complaint categories
- `POST /api/v1/institutions/registration-requests/` — Apply to register a new institution
- `POST /api/v1/institutions/registration-requests/<id>/approve/` — Superadmin approve institution
- `POST /api/v1/institutions/admin-access-requests/` — Apply to join existing institution
- `POST /api/v1/institutions/admin-access-requests/<id>/approve/` — Approve admin access

### Student Complaints & Letter Generation (`/api/v1/complaints/`)
- `GET /api/v1/complaints/` — List student's own complaints
- `POST /api/v1/complaints/` — Create new complaint (as DRAFT or SUBMITTED)
- `GET /api/v1/complaints/<id>/` — View full complaint details
- `PATCH /api/v1/complaints/<id>/` — Update draft complaint
- `POST /api/v1/complaints/generate-application/` — Preview formal letter to The Dean before submission
- `POST /api/v1/complaints/<id>/submit/` — Formally submit complaint after student review
- `GET /api/v1/complaints/<id>/timeline/` — View status progression (internal notes omitted for students)
- `POST /api/v1/complaints/<id>/reopen/` — Reopen unresolved complaint
- `POST /api/v1/complaints/<id>/attachments/` — Upload photos or PDFs (max 5MB)

### Administrator Desk (`/api/v1/admin/`)
- `GET /api/v1/admin/complaints/` — Institutional complaints desk
- `POST /api/v1/admin/complaints/<id>/assign/` — Assign to department and staff
- `POST /api/v1/admin/complaints/<id>/status/` — Update status (`UNDER_REVIEW`, `IN_PROGRESS`, etc.)
- `POST /api/v1/admin/complaints/<id>/remarks/` — Add public remark for student
- `POST /api/v1/admin/complaints/<id>/internal-notes/` — Add confidential admin note
- `POST /api/v1/admin/complaints/<id>/resolution/` — Close complaint with resolution details

### Gnani AI Integration (`/api/v1/ai/`)
- `GET /api/v1/ai/status/` — Live connection status of Gnani AI voice services
- `POST /api/v1/ai/speech-to-text/` — Proxies audio to Gnani Prisma STT (`/stt/v3`)
- `POST /api/v1/ai/text-to-speech/` — Proxies application text to Gnani Timbre TTS (`/api/v1/tts/inference`)

### Dashboards & Analytics (`/api/v1/`)
- `GET /api/v1/dashboard/student/` — Student grievance metrics and drafts
- `GET /api/v1/dashboard/admin/` — Administrator desk volume and urgent cases
- `GET /api/v1/analytics/institution/` — Department distribution and resolution rate

---

## 8. Running Automated Tests

Run the complete 15-test automated test suite covering security, tenant boundaries, permissions, and letter generation:
```powershell
python manage.py test tests
```
Output:
```
Ran 15 tests in 30.827s
OK
```

---

## 9. Gnani AI Configuration

Official Documentation: [https://docs.gnani.ai/](https://docs.gnani.ai/)

To activate live speech recognition and audio readout:
1. Obtain an API key from the Gnani AI developer portal (`vachana.ai`).
2. Add the key to `backend/.env`:
   ```ini
   GNANI_API_KEY=your_live_gnani_api_key
   GNANI_API_BASE_URL=https://api.vachana.ai
   ```
3. Restart the Django development server.
4. When `GNANI_API_KEY` is not present, the backend transparently returns HTTP 503 (`service_unavailable`), and the frontend activates its built-in Web Speech API audio synthesis and demo transcription with a clear indicator. No false transcription is ever fabricated.

---

## 10. Production Checklist

- [ ] Set `DJANGO_DEBUG=False` in `.env`.
- [ ] Generate a cryptographically random secret key using `secrets.token_urlsafe(50)`.
- [ ] Configure `DJANGO_ALLOWED_HOSTS` with production domain names.
- [ ] Ensure `USE_SQLITE_FOR_TESTS=False` so MySQL is strictly used.
- [ ] Configure Nginx / Gunicorn with HTTPS/TLS certificates.
- [ ] Configure `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, and `CSRF_COOKIE_SECURE = True`.
- [ ] Serve static files with WhiteNoise or AWS S3 / CloudFront.
