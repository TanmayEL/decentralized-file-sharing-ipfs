# IPFS File Sharing

Upload files to IPFS. Share them with anyone. Files live on a decentralized network — no single server to go down, no single company to pull the plug.

**Live:** [ipfs-file-sharing.netlify.app](https://ipfs-file-sharing.netlify.app)

---

## What it does

- Upload files (up to 10MB) → get pinned to IPFS via Pinata
- Auto-compresses before upload — images via Sharp, everything else gzipped
- Public or private files, with per-user access sharing
- Files expire after 7 days unless you mark them persistent
- JWT auth, bcrypt passwords, rate limiting — the usual

---

## Stack

**Frontend** — React + Material-UI, deployed on Netlify

**Backend** — Node/Express, deployed on Vercel

**Storage** — Pinata (IPFS pinning) + MongoDB Atlas (metadata)

---

## Architecture

MVC — the backend is no longer a 650-line monolith:

```
backend/
├── models/        → User, File schemas
├── controllers/   → request handlers
├── services/      → IPFS, compression, cleanup logic
├── middleware/    → auth, upload, error handling
└── routes/        → auth + file routes

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

Clone, add a `.env` to `/backend`:

```
MONGODB_URI=your_mongo_uri
JWT_SECRET=something_long_and_random
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_secret
FRONTEND_URL=http://localhost:3000
```

Then:

```bash
# backend
cd backend && npm install && node index.js

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
