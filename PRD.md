# SaveYears AI Coach — MVP PRD (Defaults)

## 1) Overview
- **One-line**: AI intake → instant 4‑week plan → trainer approval → client delivery (web + iOS + Android via Capacitor).
- **Goal**: Automate intake and plan generation to 10× capacity while keeping SaveYears voice and quality.
- **Personas**:
  - Busy Professional (3x/week, ≤45m sessions, minimal equipment, knee discomfort)
  - New Parent (20–30m/day at home, bands + light DBs)

## 2) Success Criteria (MVP)
- 10 paying clients complete intake and receive approved plan within 24h
- p50 generation latency ≤ 6s (API side)
- Trainer approval rate ≥ 90% on first pass

## 3) Scope
### In
- AI intake (responsive web)
- Program generator (4 weeks; Full-body 3x; Upper/Lower 4x)
- Trainer review/approve/edit (web)
- Plan viewer + PDF export (1 page/week)
- Stripe checkout (one-time + monthly), webhook
- Email delivery (Brevo)
- Push notifications: plan_ready, weekly_checkin
- Deep links to plan/check-in screens

### Out (Phase 2+)
- Wearable integrations
- Native-only features (camera videos, offline editor)
- Nutrition plans

## 4) Flows
- **Acquisition** → Checkout (Stripe) → Intake → Generate (AI) → Trainer Approve → PDF + Email + Push
- Weekly → **Check-in** → Next plan adaptation (post-MVP)

## 5) Non-functional
- Availability 99.5% (best-effort MVP)
- Cost ceiling ≤ $250/month infra/AI
- Privacy: minimal health data; consent required

## 6) Risks & Mitigations
- App Store IAP risk → justify Stripe (coaching services); fallback later if needed
- AI hallucination → rule-based validator before approve
- PDF churn → approve tokens early (logo, colors, margins)

## 7) Milestones
- Slice 1: Intake→Hello Plan stub
- Slice 2: AI live + persistence
- Slice 3: Approve + PDF
- Slice 4: Stripe + Email + Push
- Web beta → TestFlight/Play internal → Public stores
