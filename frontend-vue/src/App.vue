<template>
  <main style="max-width:1000px;margin:24px auto;font-family:Inter,system-ui">
    <h1>SaveYears Coach</h1>
    <p style="color:#666">Intake → Generate → View Plan</p>

    <!-- Intake form (unchanged) -->
    <form class="card" @submit.prevent="onSubmit">
      <label>Name<br /><input v-model="form.name" required /></label><br /><br />
      <label>Email<br /><input v-model="form.email" type="email" required /></label><br /><br />
      <label>Days per week<br /><input v-model.number="form.days_per_week" type="number" min="1" max="6" required /></label><br /><br />
      <label>Session length (minutes)<br /><input v-model.number="form.session_length_minutes" type="number" min="15" max="120" required /></label><br /><br />
      <label>Equipment (hold Ctrl/Cmd for multi-select)<br />
        <select multiple v-model="form.equipment">
          <option value="dumbbells">Dumbbells</option>
          <option value="kettlebells">Kettlebells</option>
          <option value="bands">Bands</option>
          <option value="bodyweight_only">Bodyweight Only</option>
        </select>
      </label><br /><br />
      <label>Goal<br />
        <select v-model="form.goals">
          <option value="general_fitness">General Fitness</option>
          <option value="fat_loss">Fat Loss</option>
          <option value="muscle_gain">Muscle Gain</option>
          <option value="strength">Strength</option>
        </select>
      </label><br /><br />

      <button :disabled="loading" class="btn">
        {{ loading ? "Working..." : "Submit Intake" }}
      </button>
    </form>

    <section v-if="error" class="card error">
      <strong>Error:</strong> {{ error }}
    </section>

    <!-- PLAN VIEW -->
    <section v-if="plan" class="card">
      <header class="plan-header">
        <div>
          <div class="eyebrow">Plan ID</div>
          <h2 class="tight">{{ plan.plan_id || plan.id || "—" }}</h2>
        </div>
        <div>
          <div class="eyebrow">Weeks</div>
          <h2 class="tight">{{ weeks.length }}</h2>
        </div>
      </header>

      <div v-for="(week, widx) in weeks" :key="widx" class="week">
        <h3 class="week-title">Week {{ widx + 1 }} <span v-if="week.title" class="muted">— {{ week.title }}</span></h3>

        <div class="week-sections">
          <div class="panel">
            <h4>Warm-up</h4>
            <ul v-if="toList(week.warmup).length">
              <li v-for="(item, i) in toList(week.warmup)" :key="i">{{ item }}</li>
            </ul>
            <div v-else class="muted">No warm-up items</div>
          </div>

          <div class="panel">
            <h4>Main Sets</h4>
            <div v-if="normalizeMain(week.main_sets).length" class="table">
              <div class="row head">
                <div>Exercise</div><div>Sets</div><div>Reps</div><div>Tempo</div><div>Rest</div>
              </div>
              <div class="row" v-for="(s, i) in normalizeMain(week.main_sets)" :key="i">
                <div>{{ s.exercise }}</div>
                <div>{{ s.sets ?? "—" }}</div>
                <div>{{ s.reps ?? "—" }}</div>
                <div>{{ s.tempo ?? "—" }}</div>
                <div>{{ s.rest ?? "—" }}</div>
              </div>
            </div>
            <div v-else class="muted">No main sets</div>
          </div>

          <div class="panel">
            <h4>Accessories</h4>
            <ul v-if="toList(week.accessories).length">
              <li v-for="(acc, i) in toList(week.accessories)" :key="i">{{ acc }}</li>
            </ul>
            <div v-else class="muted">No accessories</div>
          </div>
        </div>

        <div class="panel">
          <h4>Notes</h4>
          <textarea class="notes" :value="week.notes || ''" readonly></textarea>
        </div>
      </div>

      <details class="raw">
        <summary>Raw JSON</summary>
        <pre>{{ pretty(plan) }}</pre>
      </details>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { createIntake, generatePlanByIntakeId, getPlan } from './api.js'

const form = reactive({
  name: '',
  email: '',
  days_per_week: 3,
  session_length_minutes: 45,
  equipment: ['dumbbells'],
  goals: 'general_fitness'
})
const loading = ref(false)
const error = ref('')
const plan = ref(null)

const weeks = computed(() => {
  const w = plan.value?.weeks || plan.value?.program?.weeks || []
  return Array.isArray(w) ? w : []
})

function pretty(obj) { return JSON.stringify(obj, null, 2) }

/** Convert arrays of strings OR objects into display strings */
function toList(arr) {
  if (!arr) return []
  if (Array.isArray(arr) && typeof arr[0] === 'string') return arr
  if (Array.isArray(arr) && typeof arr[0] === 'object') {
    return arr.map(o => o.name || o.exercise || o.title || JSON.stringify(o))
  }
  return []
}

/** Normalize main_sets to a consistent shape for display */
function normalizeMain(arr) {
  if (!Array.isArray(arr)) return []
  return arr.map(o => {
    if (typeof o === 'string') return { exercise: o }
    return {
      exercise: o.exercise || o.name || o.title || '—',
      sets: o.sets ?? o.sets_count ?? o.set ?? undefined,
      reps: o.reps ?? o.rep_range ?? undefined,
      tempo: o.tempo ?? undefined,
      rest: o.rest ?? o.rest_seconds ?? undefined,
    }
  })
}

async function onSubmit() {
  error.value = ''
  plan.value = null
  loading.value = true
  try {
    const { intake_id } = await createIntake(form)
    const { plan_id } = await generatePlanByIntakeId(intake_id)
    plan.value = await getPlan(plan_id)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}
</script>

<style>
.card { border:1px solid #eee; border-radius:12px; padding:16px; margin:16px 0; background:#fff }
.error { border-color:#f88; background:#fff7f7 }
.btn { padding:10px 14px; border:0; border-radius:10px; background:#00BFA6; color:white; cursor:pointer }
.plan-header { display:flex; gap:24px; align-items:flex-end; margin-bottom:8px }
.eyebrow { font-size:12px; color:#777; text-transform:uppercase; letter-spacing:.06em }
.tight { margin:4px 0 0 0 }
.week { border-top:1px dashed #eee; padding-top:16px; margin-top:16px }
.week-title { margin:0 0 12px 0 }
.week-sections { display:grid; gap:12px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.panel { border:1px solid #f0f0f0; border-radius:10px; padding:12px; background:#fafafa }
.table { display:grid; gap:4px }
.row { display:grid; grid-template-columns: 2fr 0.7fr 0.7fr 0.8fr 0.8fr; gap:8px; padding:6px 8px; border-radius:6px }
.row.head { font-weight:600; background:#f1f5f9 }
.row:not(.head) { background:#fff }
.notes { width:100%; min-height:96px; resize:vertical; padding:8px; border-radius:8px; border:1px solid #ddd; background:#fff }
.muted { color:#777 }
.raw { margin-top:12px }
input, select { padding:8px; border-radius:8px; border:1px solid #ddd; width:100%; margin-top:6px; }
</style>
