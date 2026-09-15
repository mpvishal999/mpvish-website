# MPVISH v3.0 — Website + Admin Panel (Do Alag Apps)

## ⚡ QUICK START

### Website chalane ke liye:
```bash
cd mpvish_website
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
python seed_data.py
python create_admin.py
python app.py
# → http://127.0.0.1:5000
```

### Admin Panel chalane ke liye:
```bash
cd mpvish_admin
python -m venv venv
venv\Scripts\activate
# source venv/bin/activate
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5001
```

## 🔗 ADMIN AUR WEBSITE KO CONNECT KASE KRE?

Dono apps **same database** use karte hain. Sirf ek kaam karna hai:

### Local (SQLite):
Dono apps ka `DATABASE_URL` same rakhna hai:
```
# .env file me DONO apps ke liye:
DATABASE_URL=sqlite:///mpvish.db
```

**Important:** SQLite ke saath, dono apps ko ek hi folder se chalao taaki `mpvish.db` file same location pe rahe. Ya phir absolute path use karo:
```
DATABASE_URL=sqlite:///C:/mpvish/mpvish.db
```

### Production (PostgreSQL):
Render.com pe dono apps ka `DATABASE_URL` same PostgreSQL database ka rakho:
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## 📋 DONO APPS KA CONNECTION KASE WORK KRTA HE?

```
┌─────────────────┐         ┌──────────────────┐
│  mpvish_website  │         │  mpvish_admin     │
│  (Port 5000)     │         │  (Port 5001)      │
│                  │         │                   │
│  - Homepage      │         │  - Dashboard      │
│  - Notes/Papers  │         │  - Notes CRUD     │
│  - Results       │         │  - Papers CRUD    │
│  - Govt Jobs     │         │  - Yojna CRUD     │
│  - MP Yojna      │         │  - User Management│
│  - Premium       │─────────│  - Premium Approve │
│  - Login/Register│ SHARED  │  - Soft Delete     │
│  - Search        │   DB    │  - Trash/Restore   │
│  - Downloads     │         │  - Analytics       │
│                  │         │  - Settings Control │
└─────────────────┘         └──────────────────┘
        │                           │
        └─────────┬─────────────────┘
                  ▼
         ┌────────────────┐
         │   DATABASE     │
         │ (SQLite/PG)   │
         │                │
         │ - Users        │
         │ - Notes         │
         │ - Papers        │
         │ - Yojnas        │
         │ - Settings      │
         │ - Downloads     │
         │ - Audit Logs    │
         └────────────────┘
```

**Admin se koi bhi setting change karoge (site name, tagline, social links, etc.) → website pe automatically dikhega!**

## ✨ NAYE FEATURES (v3.0)

### 1. MP Yojna & Info Section
- Website: `/mp-yojna` page — sab yojna, helpline, links dekho
- Admin: Yojna CRUD — add/edit/delete yojnas with category, department, eligibility, benefits, helpline

### 2. Soft Delete + Trash
- Delete karne pe item permanently delete NAHI hota — trash me jata hai
- Trash se restore kar sakte ho (wapas aa jayega)
- Permanent delete sirf superadmin kar sakta hai
- "Empty Trash" button se sab permanent delete ek click me

### 3. Login Required for Notes/Papers
- Notes aur Papers VIEW aur DOWNLOAD dono ke liye login zaroori hai
- Bina login ke note/paper kholne pe login page pe redirect

### 4. User Login Tracking
- Admin panel me dekho: kaun login kiya, kab kiya, kitni baar kiya
- Filter: Logged In / Never Logged In / Premium / Admins
- User detail page: downloads, purchases, login history

### 5. Animations & Highlights
- Card animations (fade-up, scale-in, slide-right)
- MP Yojna button alag colour me (green highlight)
- Premium button golden colour me
- Featured items special badge ke saath
- Smooth hover effects
- Flash messages auto-dismiss

## 🚀 DEPLOYMENT (Render.com)

### Website Deploy:
1. New Web Service → mpvish_website
2. Build: `pip install -r requirements.txt`
3. Start: `gunicorn app:app`
4. Env Vars: `SECRET_KEY`, `DATABASE_URL`, `SITE_URL`

### Admin Panel Deploy:
1. New Web Service → mpvish_admin
2. Build: `pip install -r requirements.txt`
3. Start: `gunicorn app:app`
4. Env Vars: `SECRET_KEY`, `DATABASE_URL` (SAME as website!)

### Database:
1. Create PostgreSQL database on Render
2. Copy connection string
3. Paste in BOTH website and admin env vars

## 📁 FILE STRUCTURE

### mpvish_website/
```
app.py              — Flask app entry point
config.py           — Configuration
extensions.py       — DB, Login, CSRF
models.py           — Database models (shared)
forms.py            — WTForms
utils.py            — Helper functions
routes/
  main.py           — Public routes (home, notes, papers, etc.)
  auth.py           — Login, Register, Profile, Google OAuth
templates/          — Jinja2 templates
static/css/style.css — Website styling + animations
static/js/main.js   — Theme, nav, animations
seed_data.py        — Demo data
create_admin.py     — Admin user creation
requirements.txt
.env.example
```

### mpvish_admin/
```
app.py              — Admin Flask app entry point
config.py           — Configuration (same DB!)
extensions.py       — DB, Login, CSRF
models.py           — Same models (shared)
forms.py            — Admin forms
utils.py            — Helper functions
routes/
  admin.py          — All admin routes (CRUD, trash, settings)
templates/admin/    — Admin templates
static/css/admin.css — Admin styling
static/js/admin.js   — Admin JS
create_admin.py     — Admin user creation
seed_data.py        — Demo data
requirements.txt
.env.example
```

## 🔐 ADMIN LOGIN

Default admin credentials (seed_data se):
- Email: `admin@mpvish.in`
- Password: `Admin@12345`

**Change karna na bhulen!** `create_admin.py` run karke naya admin banao.

## ❓ FAQ

**Q: Dono apps alag ports pe chalenge?**
A: Haan! Website port 5000 pe, Admin port 5001 pe. Production me dono alag URLs pe (jaise mpvish.onrender.com aur admin-mpvish.onrender.com).

**Q: Admin se website ka title change karunga to website pe dikhega?**
A: Haan! Admin → Settings me site name/tagline change karo, website pe turant dikhega. Dono same DB use karte hain.

**Q: Admin panel bina website ke chalega?**
A: Haan! Admin panel standalone hai. Website band bhi ho to admin panel chalega.

**Q: Trash se wapas kaise laaye?**
A: Admin → Trash → item ke aage "Restore" button dabao.

## 🖼️ HERO IMAGES (Homepage Carousel)

Admin panel se homepage ke liye images add karo:

1. **Admin Panel** → Sidebar → **Hero Images** → **+ Upload Image**
2. Image upload karo (JPG/PNG/WebP), title/subtitle/link optional
3. Website homepage pe carousel me slide-slide dikhegi
4. Hide/Show toggle, Delete, Display Order sab manage kar sakte ho

### ⚠️ IMPORTANT — Shared Uploads Folder:

Admin jo images upload karta hai, website ko dikhane ke liye **dono apps ka UPLOAD_FOLDER same hona chahiye**:

**Local (Windows example):**
```
# Dono apps ke .env me:
UPLOAD_FOLDER=C:/mpvish/shared_uploads
```

**Production (Render):**
Dono web services me same env var set karo, ya S3/Cloudinary use karo.

### Font:
- **Recoleta** — headings me use hota hai (hero title, section titles, logo)
- Font files: `static/fonts/` me hain

## 🔄 v3.2 Changes:
- Navbar: sirf "Login" button, MP Yojna/Premium normal links
- Homepage: image carousel (admin se manage)
- Recoleta font headings me
- Login + Register ek page pe tabs
- Overall clean professional UI
