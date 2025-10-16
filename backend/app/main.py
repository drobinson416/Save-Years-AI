from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

app = FastAPI(title="SaveYears AI Coach (MVP Defaults)")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# --- In-memory "DB" for quick start ---
DB_CLIENTS: Dict[str, Dict[str, Any]] = {}
DB_INTAKES: Dict[str, Dict[str, Any]] = {}
DB_PLANS: Dict[str, Dict[str, Any]] = {}

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

# --- Helpers ---
def dummy_plan(client_name: str, days_per_week: int, session_len: int) -> Dict[str, Any]:
    weeks = []
    for w in range(1, 5):
        days = []
        for d in range(1, min(days_per_week, 6) + 1):
            days.append({
                "day_number": d,
                "warmup": ["5 min easy cardio", "World’s Greatest Stretch x 5/side"],
                "main_sets": [
                    {"exercise": "Goblet Squat", "sets": 4, "reps": "8–10", "rpe": "7"},
                    {"exercise": "DB Bench Press", "sets": 4, "reps": "8–10", "rpe": "7"},
                    {"exercise": "1-Arm DB Row", "sets": 3, "reps": "10/side", "rpe": "7"},
                ],
                "accessories": ["Side Plank 3x30s/side", "Face Pull 3x12"],
                "notes": f"Stay within {session_len} min. Control tempo, breathe."
            })
        weeks.append({"week_number": w, "days": days})
    return {"weeks": weeks}

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
    # pick intake data
    if req.intake_override:
        intake = req.intake_override
        client_name = intake.name
        days = intake.days_per_week
        sess = intake.session_length_minutes
    elif req.intake_id and req.intake_id in DB_INTAKES:
        raw = DB_INTAKES[req.intake_id]["answers"]
        intake = IntakeRequest(**raw)
        client_name = intake.name
        days = intake.days_per_week
        sess = intake.session_length_minutes
    else:
        raise HTTPException(status_code=400, detail="No valid intake provided")

    # build dummy plan (replace with AI later)
    plan_id = str(uuid4())
    plan = {
        "plan_id": plan_id,
        "client_name": client_name,
        "status": "draft",
        **dummy_plan(client_name, days, sess)
    }
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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],    # or ["POST","GET","OPTIONS"]
    allow_headers=["*"],    # or ["Content-Type","Authorization"]
)

@app.get("/health")
def health():
    return {"ok": True}

