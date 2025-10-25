# backend/app/main.py
from __future__ import annotations

import os, sys, json, logging, traceback, random
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, __version__ as PYD_VERSION

logger = logging.getLogger("uvicorn.error")

def _log_exc(msg="Unhandled exception"):
    logger.error(msg + "\n" + traceback.format_exc())

def model_to_dict(m):
    # Works for both Pydantic v1 and v2
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()

# ---------------------------
# App & CORS (single instance)
# ---------------------------
app = FastAPI(title="SaveYears AI Coach")

prod_origin = (os.getenv("WEB_ORIGIN") or "").strip().rstrip("/")
dev_origins = [o.strip().rstrip("/") for o in os.getenv("DEV_ORIGINS", "").split(",") if o.strip()]
allow_origins = [o for o in [prod_origin, *dev_origins] if o] or ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],   # includes OPTIONS for preflight
    allow_headers=["*"],
    max_age=86400,
)

# --------------------------------
# In-memory stores (MVP simplicity)
# --------------------------------
DB_INTAKES: Dict[str, Dict[str, Any]] = {}
DB_PLANS: Dict[str, Dict[str, Any]] = {}

# ----------------
# Exercise library
# ----------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXERCISES_PATH = DATA_DIR / "exercises.json"

def load_exercises() -> Dict[str, Dict[str, Any]]:
    try:
        if not EXERCISES_PATH.exists():
            return {}
        with EXERCISES_PATH.open("r", encoding="utf-8") as f:
            items = json.load(f)
        return {item["id"]: item for item in items}
    except Exception:
        _log_exc("Failed to load exercises.json")
        return {}

def filter_by_equipment(equipment: List[str]) -> List[Dict[str, Any]]:
    lib = load_exercises()
    eq = set(equipment or [])
    if "bodyweight_only" in eq:
        eq.discard("bodyweight_only")
        eq.add("bodyweight")
    if not eq:
        eq.add("bodyweight")
    return [ex for ex in lib.values() if eq.intersection(ex.get("equipment", []))]

def choose_by_tags(pool: List[Dict[str, Any]], include_tags: List[str], n: int, rng: random.Random) -> List[Dict[str, Any]]:
    if not pool: return []
    candidates = [ex for ex in pool if set(include_tags).intersection(ex.get("tags", []))]
    base = candidates or pool
    n = min(max(1, n), len(base))
    return rng.sample(base, k=n)

# ------------------------
# Models (request/response)
# ------------------------
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

# --------------------
# Plan gen (rule-based)
# --------------------
GOAL_PARAMS = {
    "strength":      {"reps": (3,5),   "sets": (3,5), "rest_s": (120,180)},
    "muscle_gain":   {"reps": (8,12),  "sets": (3,4), "rest_s": (60,90)},
    "fat_loss":      {"reps": (12,20), "sets": (2,4), "rest_s": (30,60)},
    "general_fitness":{"reps": (8,12), "sets": (3,4), "rest_s": (60,90)},
}
GOAL_TAGS = {
    "strength":        [["squat","knee_dominant"], ["hinge"], ["push"], ["pull"]],
    "muscle_gain":     [["push"], ["pull"], ["squat","knee_dominant"], ["hinge"]],
    "fat_loss":        [["conditioning"], ["push"], ["pull"]],
    "general_fitness": [["push"], ["pull"], ["squat","knee_dominant"], ["hinge"]],
}

def _rand_range(rng: random.Random, lo_hi): return rng.randint(lo_hi[0], lo_hi[1])

def _volume_scale(days_per_week: int, session_len_min: int) -> float:
    d = max(1, min(6, int(days_per_week or 3)))
    s = max(20, min(120, int(session_len_min or 45)))
    return (d / 3.0) * (s / 45.0)

def _make_warmup(rng: random.Random, pool: List[Dict[str, Any]]) -> List[str]:
    choices = ["5 min easy cardio", "Dynamic leg swings", "Arm circles", "Hip openers", "Dead hang 30s", "Cat-cow x10"]
    if pool:
        choices += [ex["name"] for ex in rng.sample(pool, k=min(2, len(pool)))]
    return rng.sample(choices, k=min(4, len(choices)))

def _make_main_sets(rng: random.Random, goal: str, pool: List[Dict[str, Any]], vol_scale: float) -> List[Dict[str, Any]]:
    params = GOAL_PARAMS.get(goal, GOAL_PARAMS["general_fitness"])
    sets_count = max(2, min(6, round(_rand_range(rng, params["sets"]) * min(1.8, vol_scale))))
    reps = _rand_range(rng, params["reps"])
    rest = _rand_range(rng, params["rest_s"])

    n_lifts = max(2, min(4, round(2 * vol_scale)))
    tag_groups = GOAL_TAGS.get(goal, GOAL_TAGS["general_fitness"])

    picks: List[Dict[str, Any]] = []
    for tg in tag_groups:
        picks += choose_by_tags(pool, tg, 1, rng)
        if len(picks) >= n_lifts: break
    remaining = [ex for ex in pool if ex not in picks]
    if remaining and len(picks) < n_lifts:
        picks += rng.sample(remaining, k=min(n_lifts - len(picks), len(remaining)))

    out = []
    for ex in picks[:n_lifts]:
        out.append({
            "exercise_id": ex["id"],
            "exercise": ex["name"],
            "sets": sets_count,
            "reps": reps if isinstance(reps, int) else f"{params['reps'][0]}–{params['reps'][1]}",
            "tempo": None,
            "rest": f"{rest}s",
            "meta": {
                "description": ex.get("description"),
                "video": ex.get("video"),
                "poster": ex.get("poster"),
                "equipment": ex.get("equipment"),
                "primary_muscles": ex.get("primary_muscles"),
                "secondary_muscles": ex.get("secondary_muscles"),
                "cues": ex.get("cues"),
                "tags": ex.get("tags"),
                "level": ex.get("level"),
            }
        })
    return out

def _make_accessories(rng: random.Random, pool: List[Dict[str, Any]], goal: str, vol_scale: float) -> List[str]:
    n = max(2, min(6, round(3 * vol_scale)))
    picks = rng.sample(pool, k=min(n, len(pool))) if pool else []
    names = [p["name"] for p in picks]
    if goal == "fat_loss":
        names = (names + ["Farmer carries", "Core circuit 10 min"])[:n]
    elif goal == "strength":
        names = (names + ["Back extensions", "Face pulls"])[:n]
    return names

def build_plan_from_intake(intake: Dict[str, Any], seed: int | None = None, weeks: int = 4) -> Dict[str, Any]:
    rng = random.Random(seed or random.randint(1, 10_000_000))
    goal = (intake.get("goals") or "general_fitness").strip().lower()
    days = int(intake.get("days_per_week") or 3)
    session_len = int(intake.get("session_length_minutes") or 45)
    equipment = intake.get("equipment") or ["bodyweight_only"]

    pool = filter_by_equipment(equipment)
    vol_scale = _volume_scale(days, session_len)

    plan_weeks = []
    for w in range(weeks):
        week_rng = random.Random(rng.randint(1, 1_000_000))
        plan_weeks.append({
            "title": f"Week {w+1}",
            "warmup": _make_warmup(week_rng, pool),
            "main_sets": _make_main_sets(week_rng, goal, pool, vol_scale),
            "accessories": _make_accessories(week_rng, pool, goal, vol_scale),
            "notes": f"Goal: {goal.replace('_',' ')} | Days/wk: {days}, Session: {session_len} min | RPE: 1–3 RIR.",
        })

    return {
        "plan_id": str(uuid4()),
        "status": "draft",
        "weeks": plan_weeks,
        "generated_from": {
            "days_per_week": days,
            "session_length_minutes": session_len,
            "equipment": equipment,
            "goals": goal,
        }
    }

# -----------
# Diagnostics
# -----------
@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.get("/_diag")
def diag():
    count = 0
    exists = EXERCISES_PATH.exists()
    try:
        if exists:
            with EXERCISES_PATH.open("r", encoding="utf-8") as f:
                count = len(json.load(f))
    except Exception:
        _log_exc("Failed to read exercises.json")
    return {
        "python": sys.version,
        "pydantic": PYD_VERSION,
        "exercises_path": str(EXERCISES_PATH),
        "exercises_exists": exists,
        "exercises_count": count,
        "allow_origins": allow_origins,
    }

# -------
# Routes
# -------
@app.post("/api/intake", response_model=IntakeCreated)
def create_intake(req: IntakeRequest):
    try:
        intake_id = str(uuid4())
        DB_INTAKES[intake_id] = model_to_dict(req)
        return {"intake_id": intake_id}
    except Exception:
        _log_exc("INTAKE failed")
        raise HTTPException(status_code=500, detail="Server error during intake")

@app.post("/api/generate-plan")
def generate_plan(req: GeneratePlanRequest):
    try:
        if req.intake_override:
            intake = model_to_dict(req.intake_override)
        elif req.intake_id and req.intake_id in DB_INTAKES:
            intake = DB_INTAKES[req.intake_id]
        else:
            raise HTTPException(status_code=400, detail="No intake provided")

        plan = build_plan_from_intake(intake)
        plan_id = plan["plan_id"]
        DB_PLANS[plan_id] = plan
        return {"plan_id": plan_id}
    except HTTPException:
        raise
    except Exception:
        _log_exc("GENERATE_PLAN failed")
        raise HTTPException(status_code=500, detail="Server error during plan generation")

@app.get("/api/plans/{plan_id}")
def get_plan(plan_id: str):
    plan = DB_PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Not found")
    return plan

# Optional: make bare OPTIONS return 204 for manual tests
@app.options("/{rest_of_path:path}")
def any_options(rest_of_path: str):
    return Response(status_code=204)
