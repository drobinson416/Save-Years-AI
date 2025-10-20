<template>
  <main style="max-width:900px;margin:24px auto;font-family:Inter,system-ui">
    <h1>SaveYears Coach</h1>
    <p style="color:#666">Intake → Generate → View Plan (talking to your live API)</p>

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

      <button :disabled="loading" style="padding:10px 14px;border:0;border-radius:10px;background:#00BFA6;color:white">
        {{ loading ? "Working..." : "Submit Intake" }}
      </button>
    </form>

    <section v-if="error" class="card" style="border-color:#f88">
      <strong>Error:</strong> {{ error }}
    </section>

    <section v-if="plan" class="card">
      <h3>Plan ({{ plan.status }})</h3>
      <pre style="white-space:pre;overflow:auto;background:#fafafa;padding:12px;border-radius:8px">
{{ pretty(plan) }}
      </pre>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
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

function pretty(obj) { return JSON.stringify(obj, null, 2) }

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
.card { border:1px solid #eee; border-radius:12px; padding:16px; margin:16px 0; }
input, select { padding:8px; border-radius:8px; border:1px solid #ddd; width:100%; margin-top:6px; }
</style>

