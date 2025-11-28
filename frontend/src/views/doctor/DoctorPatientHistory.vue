<template>
  <div class="doctor-patient-history container py-4">
    <!-- HEADER -->
    <div class="card border-0 shadow-sm mb-3 header-card">
      <div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-2">
          <div class="page-icon-sm">
            <i class="bi bi-person-lines-fill"></i>
          </div>
          <div>
            <h4 class="mb-1">
              Patient History
              <span v-if="patient" class="text-muted small">
                – {{ patient.full_name }}
              </span>
            </h4>
            <p class="small text-muted mb-0">
              Chronological list of visits, diagnoses, medicines and follow-ups for this patient.
            </p>
          </div>
        </div>
        <button
          class="btn btn-outline-secondary btn-sm"
          type="button"
          @click="goBack"
        >
          <i class="bi bi-arrow-left me-1"></i>
          Back
        </button>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- PATIENT BASIC INFO -->
    <div v-if="patient" class="card border-0 shadow-sm mb-3">
      <div class="card-body small">
        <div class="row g-3">
          <div class="col-md-4">
            <div class="text-muted">Patient</div>
            <div class="fw-semibold">
              {{ patient.full_name || 'Patient' }}
            </div>
            <div class="text-muted">
              ID: #{{ patient.id || patient.patient_id }}
            </div>
          </div>
          <div class="col-md-4">
            <div class="text-muted">Contact</div>
            <div>{{ patient.email || 'N/A' }}</div>
            <div>{{ patient.phone || patient.mobile || 'N/A' }}</div>
          </div>
          <div class="col-md-4">
            <div class="text-muted">Other</div>
            <div>Age: {{ patient.age ?? 'N/A' }}</div>
            <div>Gender: {{ patient.gender || 'N/A' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- VISIT LIST -->
    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <div v-if="loading" class="text-center py-4 small text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>
          Loading visit history…
        </div>

        <div
          v-else-if="visits.length === 0"
          class="empty-state small text-muted text-center py-4"
        >
          <div class="empty-icon mb-2">
            <i class="bi bi-journal-medical"></i>
          </div>
          <div class="fw-semibold mb-1">No recorded visits for this patient.</div>
          <div>Once treatment details are saved, they will appear here.</div>
        </div>

        <div v-else class="timeline">
          <div
            v-for="v in visits"
            :key="v.id"
            class="timeline-item"
          >
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <div>
                  <div class="fw-semibold">
                    {{ prettyDate(v.appointment_date || v.visit_date) }}
                    <span v-if="v.time_slot" class="text-muted">
                      at {{ v.time_slot }}
                    </span>
                  </div>
                  <div class="small text-muted">
                    Visit type:
                    <strong>{{ mapVisitType(v.visit_type) }}</strong>
                  </div>
                </div>
                <span
                  class="badge rounded-pill"
                  :class="statusBadgeClass(v.status)"
                >
                  {{ (v.status || 'COMPLETED').toUpperCase() }}
                </span>
              </div>

              <div class="row small g-2">
                <div class="col-md-4">
                  <div class="label">Diagnosis</div>
                  <div class="value">
                    {{ v.diagnosis || '—' }}
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="label">Tests</div>
                  <div class="value">
                    {{ v.tests_done || v.tests || '—' }}
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="label">Follow-up</div>
                  <div class="value">
                    {{
                      v.follow_up_date ? prettyDate(v.follow_up_date) : 'No follow-up set'
                    }}
                  </div>
                </div>
              </div>

              <div class="row small g-2 mt-1">
                <div class="col-md-6">
                  <div class="label">Medicines & dosage</div>
                  <div class="value pre-line">
                    {{ v.medicines || '—' }}
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="label">Precautions / Notes</div>
                  <div class="value pre-line">
                    {{ v.precautions || v.notes || '—' }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <p class="small text-muted mt-2 mb-0">
            Hint: Ensure every completed visit has diagnosis, tests and follow-up information.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/axios'

const route = useRoute()
const router = useRouter()

const patientId = route.query.patientId

const loading = ref(false)
const errorMessage = ref('')
const patient = ref(null)
const visits = ref([])

const loadHistory = async () => {
  if (!patientId) {
    errorMessage.value = 'Patient ID missing in URL.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/doctor/patient-history', {
      params: { patient_id: patientId },
    })
    // Expecting: { patient: {...}, visits: [...] }
    patient.value = res.data?.patient || null
    visits.value = res.data?.visits || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load patient history.'
  } finally {
    loading.value = false
  }
}

const prettyDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString()
}

const mapVisitType = (v) => {
  if (!v) return 'Not specified'
  const up = v.toUpperCase()
  if (up === 'IN_PERSON') return 'In-person (clinic)'
  if (up === 'ONLINE') return 'Online / teleconsultation'
  return v
}

const statusBadgeClass = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'COMPLETED') return 'bg-success-subtle text-success-emphasis'
  if (s === 'CANCELLED') return 'bg-danger-subtle text-danger-emphasis'
  if (s === 'BOOKED') return 'bg-primary-subtle text-primary-emphasis'
  return 'bg-secondary-subtle text-secondary-emphasis'
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.header-card {
  border-radius: 16px;
}
.page-icon-sm {
  height: 40px;
  width: 40px;
  border-radius: 14px;
  background: #0f766e;
  color: #ecfeff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

/* Empty state */
.empty-state .empty-icon {
  font-size: 1.8rem;
  color: #9ca3af;
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 18px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: #e5e7eb;
}
.timeline-item {
  position: relative;
  margin-bottom: 14px;
}
.timeline-dot {
  position: absolute;
  left: -1px;
  top: 6px;
  height: 10px;
  width: 10px;
  border-radius: 999px;
  background: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25);
}
.timeline-content {
  margin-left: 18px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

/* Labels */
.label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}
.value {
  font-size: 0.82rem;
}
.pre-line {
  white-space: pre-line;
}

.small {
  font-size: 0.8rem;
}
</style>
