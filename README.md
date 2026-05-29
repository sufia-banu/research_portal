# 🎓 Research Information Collection Portal

A **production-grade ERP web application** for universities and engineering colleges to manage research publications, patents, proposals, NBA accreditation reporting, and analytics — built with **Streamlit + Supabase**.

---

## 📸 Features

| Module | Description |
|--------|-------------|
| 🔐 Authentication | Supabase Auth — Login, Register, Password Reset, Session Persistence |
| 👨‍🏫 Faculty Dashboard | Submit, edit, delete research entries + personal analytics |
| 🏢 HoD Dashboard | Department-wide analytics, faculty performance, export |
| 🔬 R&D Coordinator | Institution-wide KPIs, department comparison, trend analysis |
| 🏅 NBA Module | Accreditation-ready reports, academic year filters, bulk export |
| ⚙️ Admin Center | User management, department CRUD, reminders, full analytics |

---

## 🗂️ Project Structure

```
research-portal/
├── app.py                    # Main entry point
├── config.py                 # App-wide constants
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml           # Streamlit theme + server config
├── database/
│   ├── connection.py         # Supabase client management
│   ├── queries.py            # All CRUD operations
│   ├── schema.sql            # Full PostgreSQL schema + RLS
│   └── sample_data.sql       # Sample data insertion guide
├── services/
│   ├── auth_service.py       # Authentication logic
│   └── export_service.py     # CSV / Excel export utilities
├── pages/
│   ├── auth_page.py          # Login / Register / Reset UI
│   ├── faculty_dashboard.py  # Faculty module
│   ├── hod_dashboard.py      # HoD module
│   ├── rd_dashboard.py       # R&D Coordinator module
│   ├── nba_module.py         # NBA Accreditation module
│   └── admin_dashboard.py    # Admin Control Center
├── components/
│   ├── ui.py                 # Reusable UI components
│   └── styles.py             # Global CSS injection
└── utils/
    ├── charts.py             # Plotly chart builders
    ├── helpers.py            # General utilities
    └── validators.py         # Input validation
```

---

## ⚡ Quick Start

### 1. Prerequisites

- Python 3.10+
- Supabase account (free tier is sufficient)
- Git

### 2. Clone & Install

```bash
# Clone the repo (or download the files)
cd "e:\Reseacrh portal"

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

```

### 3. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com) → **New Project**
2. Choose a region close to your users
3. Note your **Project URL** and **API Keys** from:
   - `Settings → API → Project URL`
   - `Settings → API → anon public` key
   - `Settings → API → service_role secret` key

### 4. Run the Database Schema

1. In Supabase Dashboard → **SQL Editor** → **New Query**
2. Paste the contents of `database/schema.sql`
3. Click **Run** — this creates all tables, RLS policies, triggers, and sample departments

### 5. Configure Authentication

In Supabase Dashboard:
1. **Authentication → Settings**
   - Enable **Email confirmations** (optional for testing: disable it)
   - Set **Site URL** to `http://localhost:8501` (for local dev)
   - Add `http://localhost:8501` to **Redirect URLs**
2. For production: update Site URL to your Streamlit Cloud URL

### 6. Set Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit .env with your actual values
```

`.env` file:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
APP_NAME=Research Information Collection Portal
INSTITUTION_NAME=Your University Name
```

### 7. Run the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 👤 User Roles & Access

| Role | Access Level |
|------|--------------|
| **Faculty** | Own entries only — submit, edit, delete, view personal analytics |
| **HoD** | Department-wide data, faculty performance, department exports |
| **R&D Coordinator** | Institution-wide analytics, all departments, KPIs |
| **Admin** | Full system — users, departments, reminders, all data |

### Creating the First Admin User

1. Register via the app's Registration tab
2. In Supabase Dashboard → **Table Editor** → `profiles`
3. Find your user row → change `role` from `faculty` to `admin`
4. Log out and log back in — you'll now have Admin access

Alternatively, use Supabase's SQL Editor:
```sql
UPDATE public.profiles
SET role = 'admin'
WHERE email = 'your-email@university.edu';
```

---

## 🗄️ Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `profiles` | Extended user data (linked to auth.users) |
| `research_entries` | All research submissions |
| `departments` | Department master list |
| `reminders` | Admin-sent notifications |

### Row Level Security (RLS)

All tables have RLS enabled:
- **Faculty**: Can only read/write their own entries
- **HoD**: Can read all entries in their department
- **R&D Coordinator / Admin**: Full read access
- **Admin**: Full CRUD on all tables via service role

---

## 📊 NBA Accreditation Module

The NBA module generates evidence-ready reports for:
- **Criterion 5** — Faculty Contributions (Publications, Patents, Funded Projects)

Filter by:
- Academic Year (e.g., 2024-25)
- Department
- Research Type

Export formats:
- **CSV** — for data processing
- **Excel** — formatted with auto-width columns

---

## ☁️ Streamlit Cloud Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/research-portal.git
git push -u origin main
```

> ⚠️ **NEVER** commit `.env` to GitHub. Add it to `.gitignore`.

### 2. Deploy on Streamlit Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Click **New App** → Connect your GitHub repo
3. Set:
   - **Main file path**: `app.py`
   - **Python version**: 3.11
4. Under **Advanced settings → Secrets**, add all your `.env` variables:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
APP_NAME = "Research Information Collection Portal"
INSTITUTION_NAME = "Your University Name"
```

5. Click **Deploy** — your app will be live in ~2 minutes!

### 3. Update Supabase Auth Redirect URLs

After deployment, add your Streamlit Cloud URL to Supabase:
- `Authentication → Settings → Redirect URLs`
- Add: `https://your-app.streamlit.app`

---

## 🔒 Security Checklist

- [x] Row Level Security enabled on all tables
- [x] Service Role key used only server-side (never exposed)
- [x] Role-based access enforced at both DB (RLS) and UI level
- [x] Input sanitization on all user inputs
- [x] Password validation (min 8 chars, uppercase, digit)
- [x] Session management via Supabase Auth tokens
- [ ] Enable email verification in production (Supabase Auth settings)
- [ ] Set up Supabase SMTP for custom email sender

---

## 🛠️ Customization Guide

### Change Institution Name
Update `INSTITUTION_NAME` in `.env`

### Add New Research Types
Edit `RESEARCH_TYPES` in `config.py`

### Add New Indexing Options
Edit `INDEXING_OPTIONS` in `config.py`

### Customize Colors / Theme
- Edit `COLORS` and `CHART_COLORS` in `config.py`
- Edit `.streamlit/config.toml` for Streamlit theme
- Edit `components/styles.py` for CSS customization

### Add a New Department
- Use the Admin Dashboard → Departments tab, OR
- Run SQL: `INSERT INTO departments (department_name, code) VALUES ('...', '...')`

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web framework |
| `supabase` | Supabase Python client |
| `python-dotenv` | Environment variable loading |
| `plotly` | Interactive charts |
| `pandas` | Data manipulation |
| `openpyxl` | Excel export |
| `streamlit-option-menu` | Enhanced sidebar navigation |

---

## 🐛 Troubleshooting

### "Supabase credentials are missing"
→ Ensure `.env` file exists with correct `SUPABASE_URL` and `SUPABASE_ANON_KEY`

### "Profile not found" after login
→ The auth trigger may not have fired. Manually insert into `profiles` table via Supabase Dashboard

### RLS blocking data reads
→ Ensure your user's `role` in the `profiles` table matches the expected role

### Charts not rendering
→ Run `pip install plotly --upgrade`

---

## 📄 License

MIT License — Free to use and modify for educational and institutional purposes.

---

## 👨‍💻 Built With

- **Streamlit** — Python-based web framework
- **Supabase** — Open-source Firebase alternative (PostgreSQL + Auth)
- **Plotly** — Interactive visualizations
- **Pandas** — Data processing

---

*Research Information Collection Portal — Empowering University Research Management*


*Git hub pull
*git pull origin main
*git pull origin master