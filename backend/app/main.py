import os
import hashlib, json
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Create the app first (after imports)
app = FastAPI(title="SaveYears AI Coach (MVP Defaults)")

# --- CORS configuration ---
# Exact prod origin (NO trailing slash)
prod_origin = (os.getenv("WEB_ORIGIN") or "").strip().rstrip("/")

# Optional comma-separated dev/preview origins
devs = os.getenv("DEV_ORIGINS", "")
dev_origins = [o.strip().rstrip("/") for o in devs.split(",") if o.strip()]

allow_origins = [o for o in [prod_origin, *dev_origins] if o]
if not allow_origins:
    # sensible defaults for local dev if envs not set
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],          # includes OPTIONS
    allow_headers=["*"],
    max_age=86400,
)

# --- In-memory "DB" for quick start ---
DB_CLIENTS: Dict[str, Dict[str, Any]] = {}
DB_INTAKES: Dict[str, Dict[str, Any]] = {}
DB_PLANS: Dict[str, Dict[str, Any]] = {}
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXERCISES_PATH = DATA_DIR / "exercises.json"

# --- Schemas ---
class IntakeRequest(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    days_per_week: int
    session_length_minutes: int
    equipment: List[str]
    constraints: Optional[List[str]] = []
    goals: str
    experience: Optional[str] = "beginner"
    preferences: Optional[Dict[str, Any]] = {}

class IntakeCreated(BaseModel):
    intake_id: str

class GeneratePlanRequest(BaseModel):
    intake_id: Optional[str] = None
    intake_override: Optional[IntakeRequest] = None


class GeneratePlanRequest(BaseModel):
    intake_id: Optional[str] = None
    intake_override: Optional[IntakeRequest] = None

class PlanDay(BaseModel):
    day_number: int
    warmup: List[str] = []
    main_sets: List[Dict[str, Any]] = []
    accessories: List[str] = []
    notes: Optional[str] = ""

class PlanWeek(BaseModel):
    week_number: int
    days: List[PlanDay]

class Plan(BaseModel):
    plan_id: str
    client_name: str
    status: str = "draft"
    weeks: List[PlanWeek]

class StandardResponse(BaseModel):
    ok: bool = True
    message: str = "ok"


@lru_cache(maxsize=1)
def load_exercises() -> dict[str, dict]:
    """Load exercise library once; return dict keyed by id."""
    if not EXERCISES_PATH.exists():
        return {}
    with EXERCISES_PATH.open("r", encoding="utf-8") as f:
        items = json.load(f)
    by_id = {item["id"]: item for item in items}
    return by_id

def filter_by_equipment(equipment: list[str]) -> list[dict]:
    lib = load_exercises()
    eq = set(equipment or [])
    # map intake's 'bodyweight_only' to library's 'bodyweight'
    if "bodyweight_only" in eq:
        eq.discard("bodyweight_only")
        eq.add("bodyweight")
    if not eq:
        eq.add("bodyweight")
    return [ex for ex in lib.values() if eq.intersection(ex.get("equipment", []))]

def choose_by_tags(pool: list[dict], include_tags: list[str], n: int, rng: random.Random) -> list[dict]:
    if not pool: return []
    incl = [ex for ex in pool if set(include_tags).intersection(ex.get("tags", []))]
    base = incl if incl else pool
    n = min(max(1, n), len(base))
    return rng.sample(base, k=n)

# --- Routes ---
@app.post("/api/intake", response_model=IntakeCreated)
def create_intake(payload: IntakeRequest):
    # create client if missing
    client_id = None
    for cid, c in DB_CLIENTS.items():
        if c["email"].lower() == payload.email.lower():
            client_id = cid
            break
    if client_id is None:
        client_id = str(uuid4())
        DB_CLIENTS[client_id] = {"id": client_id, "name": payload.name, "email": payload.email, "created_at": datetime.utcnow().isoformat()}

    intake_id = str(uuid4())
    DB_INTAKES[intake_id] = {"id": intake_id, "client_id": client_id, "answers": payload.model_dump(), "created_at": datetime.utcnow().isoformat()}
    return {"intake_id": intake_id}

@app.post("/api/generate-plan")
def generate_plan(req: GeneratePlanRequest):
    # locate intake (by id or inline override)
    if req.intake_override:
        intake = req.intake_override.model_dump()
    elif req.intake_id and req.intake_id in DB_INTAKES:
        intake = DB_INTAKES[req.intake_id]
    else:
        raise HTTPException(status_code=400, detail="No intake provided")

    # generate a fresh plan using intake parameters (+ randomness)
    plan = build_plan_from_intake(intake)

    plan_id = plan["plan_id"]
    DB_PLANS[plan_id] = plan
    return {"plan_id": plan_id}

@app.get("/api/plans/{pid}", response_model=Plan)
def get_plan(pid: str):
    plan = DB_PLANS.get(pid)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@app.post("/api/plans/{pid}/approve", response_model=StandardResponse)
def approve_plan(pid: str):
    plan = DB_PLANS.get(pid)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan["status"] = "approved"
    return {"ok": True, "message": "approved"}

@app.get("/api/plans/{pid}/pdf")
def get_pdf(pid: str):
    # For MVP stub, return a placeholder URL. You can swap to real PDF generation later.
    if pid not in DB_PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"pdf_url": f"https://example.com/plan/{pid}.pdf"}

@app.post("/api/checkout/session", response_model=StandardResponse)
def create_checkout_session():
    return {"ok": True, "message": "stripe session created (stub)"}

@app.post("/api/webhooks/stripe", response_model=StandardResponse)
def stripe_webhook():
    return {"ok": True, "message": "webhook received (stub)"}

class PushRegisterRequest(BaseModel):
    platform: str = Field(pattern="^(ios|android|web)$")
    token: str

@app.post("/api/push/register", response_model=StandardResponse)
def push_register(req: PushRegisterRequest):
    return {"ok": True, "message": f"registered {req.platform}"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],    # or ["POST","GET","OPTIONS"]
    allow_headers=["*"],    # or ["Content-Type","Authorization"]
)

@app.get("/health")
def health():
    return {"ok": True}

