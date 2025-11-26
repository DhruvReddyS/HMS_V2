<template>
  <div class="doctor-dashboard container py-4">
    <!-- ============ HEADER / BANNER ============ -->
    <div class="banner card border-0 shadow-sm mb-4">
      <div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-3">
          <div class="page-icon">
            <i class="bi bi-stethoscope"></i>
          </div>
          <div>
            <h2 class="page-title mb-1">
              Welcome, Dr. {{ doctor?.full_name || 'Doctor' }}
            </h2>
            <p class="page-subtitle mb-1">
              {{ doctor?.specialization || 'Consultant' }}
            </p>
            <p class="small text-muted mb-0">
              Today is
              <strong>{{ prettyDate(summary?.today || todayStr) }}</strong>.
              Manage your appointments, update visit history and review patients from one place.
            </p>
          </div>
        </div>

        <div class="text-end small text-muted">
          <div class="badge-pill-text">
            <span class="dot dot-online"></span>
            You are logged in as <strong>Doctor</strong>
          </div>
          <div>Last updated just now</div>
        </div>
      </div>
    </div>

    <!-- ============ ERROR ============ -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- ============ TOP STATS CARDS ============ -->
    <div class="row g-3 mb-3">
      <div class="col-md-3 col-sm-6">
        <div class="stat-card stat-primary">
          <div class="stat-label">Today’s Appointments</div>
          <div class="stat-value">
            {{ summary?.stats?.today_total ?? '–' }}
          </div>
          <div class="stat-hint">
            Booked:
            <strong>{{ summary?.stats?.today_booked ?? 0 }}</strong> &nbsp;•&nbsp;
            Completed:
            <strong>{{ summary?.stats?.today_completed ?? 0 }}</strong>
          </div>
        </div>
      </div>

      <div class="col-md-3 col-sm-6">
        <div class="stat-card stat-amber">
          <div class="stat-label">Pending Visits</div>
          <div class="stat-value">
            {{ summary?.stats?.pending_visits ?? '–' }}
          </div>
          <div class="stat-hint">
            Visits that are still in <strong>BOOKED</strong> status.
          </div>
        </div>
      </div>

      <div class="col-md-3 col-sm-6">
        <div class="stat-card stat-green">
          <div class="stat-label">Completed this week</div>
          <div class="stat-value">
            {{ summary?.stats?.week_completed ?? '–' }}
          </div>
          <div class="stat-hint">
            Good job! Keep your history updated regularly.
          </div>
        </div>
      </div>

      <div class="col-md-3 col-sm-6">
        <div class="stat-card stat-sky d-flex flex-column justify-content-between">
          <div>
            <div class="stat-label">Assigned Patients</div>
            <div class="stat-value">
              {{ summary?.stats?.assigned_patients ?? '–' }}
            </div>
            <div class="stat-hint">
              Patients who have consulted you recently.
            </div>
          </div>
          <div class="text-end">
            <button
              class="btn btn-outline-primary btn-xs rounded-pill mt-1"
              type="button"
              @click="goToAllAppointments"
            >
              View all appointments
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ MAIN TWO-COLUMN LAYOUT ============ -->
    <div class="row g-3">
      <!-- LEFT: UPCOMING APPOINTMENTS -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <div>
                <h6 class="section-title mb-0">Today’s Upcoming Appointments</h6>
                <p class="small text-muted mb-0">
                  Manage status and jump directly to update patient visit details.
                </p>
              </div>
              <div class="d-flex align-items-center gap-2">
                <select
                  v-model="statusFilter"
                  class="form-select form-select-sm w-auto"
                >
                  <option value="all">All</option>
                  <option value="BOOKED">Booked</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
                <button
                  class="btn btn-outline-secondary btn-sm"
                  type="button"
                  @click="loadDashboard"
                  :disabled="loading"
                >
                  <span
                    v-if="loading"
                    class="spinner-border spinner-border-sm me-1"
                  ></span>
                  Refresh
                </button>
              </div>
            </div>

            <div v-if="loading" class="text-center py-4 small text-muted">
              <div class="spinner-border spinner-border-sm me-2"></div>
              Loading dashboard...
            </div>

            <div
              v-else-if="filteredAppointments.length === 0"
              class="small text-muted text-center py-3"
            >
              No appointments for today with this filter.
            </div>

            <div v-else class="table-responsive">
              <table class="table table-sm align-middle mb-0">
                <thead class="table-light small">
                  <tr>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th style="width: 210px;">Actions</th>
                  </tr>
                </thead>
                <tbody class="small">
                  <tr v-for="appt in filteredAppointments" :key="appt.id">
                    <td>
                      <div class="fw-semibold">
                        {{ appt.time_slot || '–' }}
                      </div>
                      <div class="text-muted">
                        {{ prettyDate(appt.appointment_date) }}
                      </div>
                    </td>
                    <td>
                      <div class="fw-semibold">
                        {{ appt.patient_name || 'Patient' }}
                      </div>
                      <div class="text-muted">
                        #{{ appt.patient_id }}
                      </div>
                    </td>
                    <td class="text-muted">
                      {{ appt.reason || 'Not specified' }}
                    </td>
                    <td>
                      <span
                        class="badge rounded-pill"
                        :class="statusBadgeClass(appt.status)"
                      >
                        {{ (appt.status || '').toUpperCase() }}
                      </span>
                    </td>
                    <td>
                      <div class="d-flex flex-wrap gap-1">
                        <button
                          class="btn btn-outline-success btn-xs"
                          type="button"
                          @click="updateStatus(appt, 'COMPLETED')"
                          :disabled="statusLoadingId === appt.id"
                        >
                          <span
                            v-if="statusLoadingId === appt.id && targetStatus === 'COMPLETED'"
                            class="spinner-border spinner-border-sm me-1"
                          ></span>
                          Complete
                        </button>
                        <button
                          class="btn btn-outline-danger btn-xs"
                          type="button"
                          @click="updateStatus(appt, 'CANCELLED')"
                          :disabled="statusLoadingId === appt.id"
                        >
                          <span
                            v-if="statusLoadingId === appt.id && targetStatus === 'CANCELLED'"
                            class="spinner-border spinner-border-sm me-1"
                          ></span>
                          Cancel
                        </button>
                        <button
                          class="btn btn-outline-primary btn-xs"
                          type="button"
                          @click="openTreatment(appt)"
                        >
                          Update visit
                        </button>
                        <button
                          class="btn btn-outline-secondary btn-xs"
                          type="button"
                          @click="goToPatientHistory(appt.patient_id)"
                        >
                          History
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p class="small text-muted mt-2 mb-0">
              Tip: Always mark visits as <strong>COMPLETED</strong> once you finish
              consultation and save treatment details.
            </p>
          </div>
        </div>
      </div>

      <!-- RIGHT: ASSIGNED PATIENTS + AVAILABILITY CTA -->
      <div class="col-lg-4">
        <!-- Assigned patients -->
        <div class="card border-0 shadow-sm mb-3">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h6 class="section-title mb-0">Assigned / Recent Patients</h6>
              <small class="text-muted">
                {{ assignedPatients.length }} patient(s)
              </small>
            </div>

            <div v-if="assignedPatients.length === 0" class="small text-muted">
              Patients will appear here once you start seeing appointments.
            </div>

            <ul v-else class="list-unstyled mb-0 small patient-list">
              <li
                v-for="p in assignedPatients"
                :key="p.patient_id"
                class="patient-item"
              >
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <div class="fw-semibold">
                      {{ p.full_name || 'Patient' }}
                    </div>
                    <div class="text-muted">
                      Last visit:
                      <strong>
                        {{ p.last_visit ? prettyDate(p.last_visit) : 'N/A' }}
                      </strong>
                    </div>
                  </div>
                  <button
                    class="btn btn-outline-primary btn-xs"
                    type="button"
                    @click="goToPatientHistory(p.patient_id)"
                  >
                    View history
                  </button>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- Availability CTA -->
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <h6 class="section-title mb-1">Doctor’s Availability</h6>
            <p class="small text-muted mb-2">
              View how your slots look for the upcoming 7 days – which timings are
              already booked and which are still free.
            </p>
            <button
              class="btn btn-outline-success btn-sm rounded-pill"
              type="button"
              @click="goToAvailability"
            >
              View availability grid
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ TREATMENT MODAL (Update Visit) ============ -->
    <div
      v-if="showTreatmentModal && activeAppointment"
      class="modal-backdrop-custom"
    >
      <div class="modal-card">
        <div class="modal-header d-flex justify-content-between align-items-center">
          <div>
            <h5 class="mb-0">Update Visit Details</h5>
            <p class="small text-muted mb-0">
              Patient:
              <strong>{{ activeAppointment.patient_name }}</strong> &nbsp;•&nbsp;
              {{ prettyDate(activeAppointment.appointment_date) }}
              at
              {{ activeAppointment.time_slot }}
            </p>
          </div>
          <button
            type="button"
            class="btn-close"
            aria-label="Close"
            @click="closeTreatment"
          ></button>
        </div>

        <div class="modal-body small">
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label small fw-semibold">Visit Type</label>
              <select
                v-model="treatmentForm.visit_type"
                class="form-select form-select-sm"
              >
                <option value="">Select</option>
                <option value="IN_PERSON">In person (clinic)</option>
                <option value="ONLINE">Online / teleconsultation</option>
              </select>
            </div>

            <div class="col-md-4">
              <label class="form-label small fw-semibold">Tests done / advised</label>
              <input
                type="text"
                v-model="treatmentForm.tests"
                class="form-control form-control-sm"
                placeholder="Eg: CBC, LFT, X-Ray chest"
              />
              <div class="form-text small">
                Comma separated list of lab / imaging tests.
              </div>
            </div>

            <div class="col-md-4">
              <label class="form-label small fw-semibold">Diagnosis</label>
              <input
                type="text"
                v-model="treatmentForm.diagnosis"
                class="form-control form-control-sm"
                placeholder="Eg: Acute gastritis"
              />
            </div>
          </div>

          <div class="row g-3 mt-1">
            <div class="col-md-8">
              <label class="form-label small fw-semibold">Medicines & dosage pattern</label>
              <textarea
                v-model="treatmentForm.medicines"
                rows="2"
                class="form-control form-control-sm"
                placeholder="Eg: DOLO650-1-1-1 | PANTOP40-1-0-1"
              ></textarea>
              <div class="form-text small">
                Pattern format
                <code>1-0-1</code> = morning – none – night,
                <code>1-1-1</code> = thrice a day.
              </div>
            </div>

            <div class="col-md-4">
              <label class="form-label small fw-semibold">Follow-up date</label>
              <input
                type="date"
                v-model="treatmentForm.follow_up_date"
                class="form-control form-control-sm"
              />
              <div class="form-text small">
                Optional. Shows in patient history if set.
              </div>
            </div>
          </div>

          <div class="mt-3">
            <label class="form-label small fw-semibold">Precautions</label>
            <textarea
              v-model="treatmentForm.precautions"
              rows="2"
              class="form-control form-control-sm"
              placeholder="Eg: Avoid spicy food, drink plenty of water, walk 30 mins/day"
            ></textarea>
          </div>

          <div class="mt-2">
            <label class="form-label small fw-semibold">Additional notes for patient</label>
            <textarea
              v-model="treatmentForm.notes"
              rows="2"
              class="form-control form-control-sm"
              placeholder="Any extra advice or clinical notes that should appear in history."
            ></textarea>
          </div>
        </div>

        <div class="modal-footer d-flex justify-content-between align-items-center">
          <div class="small text-muted">
            These details will be visible in the patient’s
            <strong>Visit History</strong>.
          </div>
          <div class="d-flex gap-2">
            <button
              class="btn btn-outline-secondary btn-sm"
              type="button"
              @click="closeTreatment"
              :disabled="savingTreatment"
            >
              Close
            </button>
            <button
              class="btn btn-primary btn-sm"
              type="button"
              @click="saveTreatment"
              :disabled="savingTreatment"
            >
              <span
                v-if="savingTreatment"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              Save visit
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/axios'

const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')

const summary = ref(null) // full dashboard payload
const doctor = computed(() => summary.value?.doctor || null)
const appointmentsToday = computed(() => summary.value?.upcoming_appointments || [])
const assignedPatients = computed(() => summary.value?.assigned_patients || [])

const statusFilter = ref('all')
const statusLoadingId = ref(null)
const targetStatus = ref(null)

const showTreatmentModal = ref(false)
const activeAppointment = ref(null)
const savingTreatment = ref(false)
const treatmentForm = ref({
  visit_type: '',
  tests: '',
  diagnosis: '',
  medicines: '',
  precautions: '',
  notes: '',
  follow_up_date: '',
})

const todayStr = new Date().toISOString().slice(0, 10)

const loadDashboard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/doctor/dashboard-summary')
    summary.value = res.data || {}
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load doctor dashboard.'
  } finally {
    loading.value = false
  }
}

const filteredAppointments = computed(() => {
  const list = appointmentsToday.value || []
  if (statusFilter.value === 'all') return list
  return list.filter(
    (a) => (a.status || '').toUpperCase() === statusFilter.value.toUpperCase()
  )
})

const statusBadgeClass = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'COMPLETED') return 'bg-success-subtle text-success-emphasis'
  if (s === 'CANCELLED') return 'bg-danger-subtle text-danger-emphasis'
  if (s === 'BOOKED') return 'bg-primary-subtle text-primary-emphasis'
  return 'bg-secondary-subtle text-secondary-emphasis'
}

const prettyDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString()
}

const updateStatus = async (appt, newStatus) => {
  if (!appt?.id) return
  if (newStatus === 'CANCELLED' && !confirm('Cancel this appointment?')) return

  statusLoadingId.value = appt.id
  targetStatus.value = newStatus
  errorMessage.value = ''

  try {
    await api.post(`/doctor/appointments/${appt.id}/status`, {
      status: newStatus,
    })
    await loadDashboard()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message ||
      `Failed to update status to ${newStatus}.`
  } finally {
    statusLoadingId.value = null
    targetStatus.value = null
  }
}

const openTreatment = (appt) => {
  activeAppointment.value = appt
  // prefill minimal sensible defaults
  treatmentForm.value = {
    visit_type: '',
    tests: '',
    diagnosis: '',
    medicines: '',
    precautions: '',
    notes: '',
    follow_up_date: '',
  }
  showTreatmentModal.value = true
}

const closeTreatment = () => {
  showTreatmentModal.value = false
  activeAppointment.value = null
}

const saveTreatment = async () => {
  if (!activeAppointment.value?.id) return
  savingTreatment.value = true
  errorMessage.value = ''

  try {
    const payload = {
      visit_type: treatmentForm.value.visit_type || null,
      tests_done: treatmentForm.value.tests || null,
      diagnosis: treatmentForm.value.diagnosis || null,
      medicines: treatmentForm.value.medicines || null,
      precautions: treatmentForm.value.precautions || null,
      notes: treatmentForm.value.notes || null,
      follow_up_date: treatmentForm.value.follow_up_date || null,
    }

    await api.post(
      `/doctor/appointments/${activeAppointment.value.id}/treatment`,
      payload
    )

    // Optionally also mark as COMPLETED if still booked
    // (You can remove this if you want separate control)
    if ((activeAppointment.value.status || '').toUpperCase() === 'BOOKED') {
      await api.post(
        `/doctor/appointments/${activeAppointment.value.id}/status`,
        { status: 'COMPLETED' }
      )
    }

    await loadDashboard()
    closeTreatment()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to save treatment.'
  } finally {
    savingTreatment.value = false
  }
}

const goToPatientHistory = (patientId) => {
  if (!patientId) return
  router.push({ path: '/doctor/patient-history', query: { patientId } })
}

const goToAllAppointments = () => {
  router.push({ path: '/doctor/appointments' })
}

const goToAvailability = () => {
  router.push({ path: '/doctor/availability' })
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.doctor-dashboard {
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Banner */
.banner {
  border-radius: 18px;
  background: linear-gradient(135deg, #eff6ff, #f5f3ff);
}
.page-icon {
  height: 52px;
  width: 52px;
  border-radius: 20px;
  background: #1d4ed8;
  color: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.7rem;
}
.page-title {
  font-weight: 800;
}
.page-subtitle {
  font-size: 0.9rem;
  color: #4b5563;
}
.badge-pill-text {
  padding: 3px 10px;
  border-radius: 999px;
  background: #eef2ff;
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-right: 4px;
}
.dot-online {
  background: #22c55e;
}

/* Section titles */
.section-title {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

/* Stat cards */
.stat-card {
  border-radius: 16px;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
}
.stat-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}
.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 2px 0;
}
.stat-hint {
  font-size: 0.78rem;
  color: #6b7280;
}
.stat-primary {
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #eff6ff, #ffffff);
}
.stat-amber {
  border-color: #fed7aa;
  background: linear-gradient(135deg, #fffbeb, #ffffff);
}
.stat-green {
  border-color: #bbf7d0;
  background: linear-gradient(135deg, #ecfdf3, #ffffff);
}
.stat-sky {
  border-color: #bae6fd;
  background: linear-gradient(135deg, #e0f2fe, #ffffff);
}

/* Patient list */
.patient-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.patient-item {
  padding: 6px 0;
  border-bottom: 1px dashed #e5e7eb;
}
.patient-item:last-child {
  border-bottom: none;
}

/* Buttons */
.btn-xs {
  padding: 2px 8px;
  font-size: 0.75rem;
  border-radius: 999px;
}

/* Modal */
.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.modal-card {
  width: min(900px, 100% - 32px);
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.35);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.modal-header,
.modal-footer {
  padding: 10px 16px;
  border-bottom: 1px solid #e5e7eb;
}
.modal-footer {
  border-top: 1px solid #e5e7eb;
  border-bottom: none;
}
.modal-body {
  padding: 10px 16px 12px;
  overflow-y: auto;
}

/* Fade */
.small {
  font-size: 0.8rem;
}
</style>
