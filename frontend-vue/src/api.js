const API = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function jsonFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export async function createIntake(payload) {
  return jsonFetch(`${API}/api/intake`, { method: "POST", body: JSON.stringify(payload) });
}

export async function generatePlanByIntakeId(intake_id) {
  return jsonFetch(`${API}/api/generate-plan`, { method: "POST", body: JSON.stringify({ intake_id }) });
}

export async function getPlan(plan_id) {
  return jsonFetch(`${API}/api/plans/${plan_id}`);
}
