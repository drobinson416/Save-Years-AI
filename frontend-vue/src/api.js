const API = ""; // same-origin
async function jsonFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}
export const createIntake = (p) => jsonFetch(`/api/intake`, { method: "POST", body: JSON.stringify(p) });
export const generatePlanByIntakeId = (id) => jsonFetch(`/api/generate-plan`, { method: "POST", body: JSON.stringify({ intake_id: id }) });
export const getPlan = (id) => jsonFetch(`/api/plans/${id}`);

