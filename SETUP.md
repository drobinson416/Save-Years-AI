# SaveYears AI Coach — Setup (Defaults)

## Quick Start
### 1) Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # add keys later
uvicorn app.main:app --reload
```
Backend will run at http://127.0.0.1:8000

### 2) Minimal Web Demo (runs today)
```bash
cd frontend-minimal
# Open index.html in your browser (no build step needed)
# Or serve: python3 -m http.server 5173
```

> The minimal web demo posts to the backend and shows a dummy plan. No Node/Vite required.

### 3) Full Vue + Capacitor (later)
- Use `frontend-vue/` skeleton to install dependencies and run a full Vue app
- Initialize Capacitor when ready to wrap for iOS/Android

## Required Secrets (for production)
- OPENAI_API_KEY
- STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET + product/price IDs
- BREVO_API_KEY
- FIREBASE config for push (FCM + APNs)
- Apple Team ID, Bundle ID (`fit.saveyears.app`), Android Package (`fit.saveyears.app`)

## Endpoints (local)
- POST /api/intake
- POST /api/generate-plan
- GET  /api/plans/{id}
- POST /api/plans/{id}/approve
- GET  /api/plans/{id}/pdf
- POST /api/checkout/session
- POST /api/webhooks/stripe
- POST /api/push/register

## Daily Smoke Test (manual)
1) Submit intake (beginner/home)
2) Generate plan
3) View plan
4) Approve plan
5) Download PDF (stub url for now)
6) (Optional) Simulate push register
