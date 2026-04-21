# IPFS File Sharing

Upload files to IPFS. Share them with anyone. Files live on a decentralized network — no single server to go down, no single company to pull the plug.

**Live:** [ipfs-file-sharing.netlify.app](https://ipfs-file-sharing.netlify.app)

---

## What it does

- Upload files (up to 10MB) → get pinned to IPFS via Pinata
- Auto-compresses before upload — images via Pillow, everything else gzipped
- Public or private files, with per-user access sharing
- Files expire after 7 days unless you mark them persistent
- JWT auth, bcrypt passwords, rate limiting — the usual

---

## Stack

**Frontend** — React + Material-UI, deployed on Netlify

**Backend** — Python/Django, deployed on Vercel

**Storage** — Pinata (IPFS pinning) + MongoDB Atlas (metadata)

---

## Architecture

MVC — split across Django apps with a shared core services layer:

```
django_backend/
├── auth_app/      → register, login, JWT refresh
├── files_app/     → upload, download, share, delete
├── admin_app/     → user and file moderation
└── core/          → auth, DB, IPFS, compression services

frontend/src/
├── components/
│   ├── auth/      → Login, Register
│   ├── files/     → Dashboard, FileUpload, PublicFiles
│   └── common/    → Navbar
├── context/       → AuthContext
└── services/      → API client
```

---

## Running locally

Clone, copy `django_backend/.env.example` to `django_backend/.env` and fill in:

```
MONGODB_URI=your_mongo_uri
DJANGO_SECRET_KEY=your_django_secret
JWT_SECRET=something_long_and_random
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_secret
FRONTEND_URL=http://localhost:3000
```

Then:

```bash
# backend
cd django_backend && pip install -r requirements.txt && python manage.py runserver

# frontend (new terminal)
cd frontend && npm install && npm start
```

---

## Limits

- 10MB max file size
- Files deleted after 7 days (toggle persistence to keep them)
- Pinata free tier bandwidth limits apply

---

**Built for the decentralized web.**
