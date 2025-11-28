<template>
  <div class="doctor-dashboard container py-4">
    <!-- ============ TOP TOOLBAR ============ -->
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2 top-toolbar">
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <span class="pill-badge">
          <span class="pill-dot"></span>
          Online • Doctor Panel
        </span>
        <span class="small text-muted">
          Last refresh:
          <strong>{{ lastRefreshedLabel }}</strong>
        </span>
      </div>

      <div class="d-flex flex-wrap gap-2">
        <button
          class="btn btn-light btn-sm rounded-pill toolbar-btn"
          type="button"
          @click="goToAllAppointments"
        >
          <i class="bi bi-list-check me-1"></i>
          All appointments
        </button>
        <button
          class="btn btn-light btn-sm rounded-pill toolbar-btn"
          type="button"
          @click="goToAvailability"
        >
          <i class="bi bi-clock-history me-1"></i>
          Availability grid
        </button>
        <button
          class="btn btn-primary btn-sm rounded-pill toolbar-btn"
          type="button"
          @click="loadDashboard"
          :disabled="loading"
        >
          <span
            v-if="loading"
            class="spinner-border spinner-border-sm me-1"
          ></span>
          <i v-else class="bi bi-arrow-clockwise me-1"></i>
          Refresh
        </button>
      </div>
    </div>

    <!-- ============ HEADER / BANNER ============ -->
    <div class="banner card border-0 shadow-soft mb-4">
      <div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3">
        <!-- Left: Doctor intro -->
        <div class="d-flex align-items-center gap-3 flex-wrap">
          <div class="page-avatar">
            <i class="bi bi-person-badge"></i>
          </div>
          <div>
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <h2 class="page-title mb-0">
                Dr. {{ doctor?.full_name || 'Doctor' }}
              </h2>
              <span
                v-if="doctor?.specialization"
                class="chip chip-soft"
              >
                {{ doctor.specialization }}
              </span>
            </div>
            <p class="page-subtitle mb-1">
              {{ todayHuman }}
            </p>
            <p class="small text-muted mb-0">
              Today’s overview of your queue, completed visits and recent patients.
            </p>
          </div>
        </div>

        <!-- Right: next appointment / status -->
        <div class="header-right text-end small text-muted">
          <div class="badge-pill-text mb-2">
            <span class="dot dot-online"></span>
            Signed in as
            <strong>Doctor</strong>
          </div>

          <div
            v-if="nextAppointment"
            class="next-appt-pill d-inline-flex align-items-center gap-2"
          >
            <div class="next-appt-icon">
              <i class="bi bi-person-video3"></i>
            </div>
            <div class="next-appt-content text-start">
              <div class="next-appt-label">Next patient</div>
              <div class="fw-semibold">
                {{ nextAppointment.patient_name || 'Patient' }}
              </div>
              <div class="small text-muted">
                {{ nextAppointment.time_slot || '—' }}
                &nbsp;•&nbsp;
                {{ prettyDate(nextAppointment.appointment_date) }}
              </div>
            </div>
          </div>
          <div v-else class="small text-muted fst-italic mt-1">
            No upcoming appointments queued for today.
          </div>
        </div>
      </div>
    </div>

    <!-- ============ ERROR ============ -->
    <transition name="fade">
      <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
        {{ errorMessage }}
      </div>
    </transition>

    <!-- ============ TOP STATS CARDS ============ -->
    <div class="row g-3 mb-3">
      <div class="col-md-3 col-6">
        <div class="stat-card stat-primary">
          <div class="stat-header d-flex justify-content-between align-items-center">
            <div>
              <div class="stat-label">Today</div>
              <div class="stat-sub">Appointments</div>
            </div>
            <span class="stat-icon-wrap">
              <i class="bi bi-calendar2-week stat-icon"></i>
            </span>
          </div>
          <div class="stat-value">
            {{ summary?.stats?.today_total ?? '–' }}
          </div>
          <div class="stat-hint">
            B:
            <strong>{{ summary?.stats?.today_booked ?? 0 }}</strong>
            &nbsp;•&nbsp;
            C:
            <strong>{{ summary?.stats?.today_completed ?? 0 }}</strong>
          </div>
        </div>
      </div>

      <div class="col-md-3 col-6">
        <div class="stat-card stat-amber">
          <div class="stat-header d-flex justify-content-between align-items-center">
            <div>
              <div class="stat-label">Pending</div>
              <div class="stat-sub">Visits</div>
            </div>
            <span class="stat-icon-wrap">
              <i class="bi bi-hourglass-split stat-icon"></i>
            </span>
          </div>
          <div class="stat-value">
            {{ summary?.stats?.pending_visits ?? '–' }}
          </div>
          <div class="stat-hint">
            Still in <strong>BOOKED</strong>.
          </div>
        </div>
      </div>

      <div class="col-md-3 col-6">
        <div class="stat-card stat-green">
          <div class="stat-header d-flex justify-content-between align-items-center">
            <div>
              <div class="stat-label">This week</div>
              <div class="stat-sub">Completed</div>
            </div>
            <span class="stat-icon-wrap">
              <i class="bi bi-check2-circle stat-icon"></i>
            </span>
          </div>
          <div class="stat-value">
            {{ summary?.stats?.week_completed ?? '–' }}
          </div>
          <div class="stat-hint">
            Completed consults.
          </div>
        </div>
      </div>

      <div class="col-md-3 col-6">
        <div class="stat-card stat-sky d-flex flex-column justify-content-between">
          <div>
            <div class="stat-header d-flex justify-content-between align-items-center">
              <div>
                <div class="stat-label">Assigned</div>
                <div class="stat-sub">Patients</div>
              </div>
              <span class="stat-icon-wrap">
                <i class="bi bi-people stat-icon"></i>
              </span>
            </div>
            <div class="stat-value">
              {{ summary?.stats?.assigned_patients ?? '–' }}
            </div>
            <div class="stat-hint">
              Recently seen by you.
            </div>
          </div>
          <div class="text-end mt-1">
            <button
              class="btn btn-outline-primary btn-xs rounded-pill"
              type="button"
              @click="goToAllAppointments"
            >
              View all
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ MAIN TWO-COLUMN LAYOUT ============ -->
    <div class="row g-3">
      <!-- LEFT: TODAY QUEUE -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-soft h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <div>
                <h6 class="section-title mb-1">Today’s queue</h6>
                <p class="small text-muted mb-0">
                  Complete, cancel or update visit sheet in one place.
                </p>
              </div>
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <div class="d-flex align-items-center small text-muted">
                  <span class="me-1 fw-semibold">Status:</span>
                  <select
                    v-model="statusFilter"
                    class="form-select form-select-sm w-auto"
                  >
                    <option value="all">All</option>
                    <option value="BOOKED">Booked</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="CANCELLED">Cancelled</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Loading -->
            <div v-if="loading" class="text-center py-4 small text-muted">
              <div class="spinner-border spinner-border-sm mb-2"></div>
              Loading your schedule…
            </div>

            <!-- Empty -->
            <div
              v-else-if="filteredAppointments.length === 0"
              class="empty-state small text-muted text-center py-4"
            >
              <div class="empty-icon mb-2">
                <i class="bi bi-clipboard2-check"></i>
              </div>
              <div class="fw-semibold mb-1">No appointments for this filter.</div>
              <div>Try a different status or change date from Appointments page.</div>
            </div>

            <!-- Table -->
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle mb-0 appointments-table">
                <thead class="table-head small">
                  <tr>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th style="width: 260px;">Actions</th>
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
                        ID: #{{ appt.patient_id }}
                      </div>
                    </td>
                    <td class="text-muted">
                      {{ appt.reason || 'Not specified' }}
                    </td>
                    <td>
                      <span
                        class="badge rounded-pill status-pill"
                        :class="statusBadgeClass(appt.status)"
                      >
                        {{ statusUpper(appt) || 'UNKNOWN' }}
                      </span>
                    </td>
                    <td>
                      <div class="d-flex flex-wrap gap-1">
                        <!-- Complete: only when BOOKED -->
                        <button
                          v-if="canComplete(appt)"
                          class="btn btn-outline-success btn-xs"
                          type="button"
                          @click="askStatusChange(appt, 'COMPLETED')"
                          :disabled="statusLoadingId === appt.id"
                        >
                          <span
                            v-if="statusLoadingId === appt.id && targetStatus === 'COMPLETED'"
                            class="spinner-border spinner-border-sm me-1"
                          ></span>
                          Complete
                        </button>

                        <!-- Cancel: only when BOOKED -->
                        <button
                          v-if="canCancel(appt)"
                          class="btn btn-outline-danger btn-xs"
                          type="button"
                          @click="askStatusChange(appt, 'CANCELLED')"
                          :disabled="statusLoadingId === appt.id"
                        >
                          <span
                            v-if="statusLoadingId === appt.id && targetStatus === 'CANCELLED'"
                            class="spinner-border spinner-border-sm me-1"
                          ></span>
                          Cancel
                        </button>

                        <!-- Update visit: allowed if not CANCELLED -->
                        <button
                          v-if="canUpdateVisit(appt)"
                          class="btn btn-outline-primary btn-xs"
                          type="button"
                          @click="openTreatment(appt)"
                        >
                          {{ appt.has_treatment ? 'Edit visit sheet' : 'Add visit details' }}
                        </button>

                        <!-- History: always allowed -->
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
              Tip: update the visit sheet and mark as <strong>COMPLETED</strong> soon after each consult.
            </p>
          </div>
        </div>
      </div>

      <!-- RIGHT: ASSIGNED PATIENTS + AVAILABILITY CTA -->
      <div class="col-lg-4">
        <!-- Assigned patients -->
        <div class="card border-0 shadow-soft mb-3">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h6 class="section-title mb-0">Recent patients</h6>
              <small class="text-muted">
                {{ assignedPatients.length }} patient(s)
              </small>
            </div>

            <div v-if="assignedPatients.length === 0" class="small text-muted">
              Patients you see will appear here automatically.
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
                    History
                  </button>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- Availability CTA -->
        <div class="card border-0 shadow-soft">
          <div class="card-body">
            <h6 class="section-title mb-1">Availability</h6>
            <p class="small text-muted mb-2">
              7-day grid of your slots to help plan follow-ups.
            </p>
            <button
              class="btn btn-outline-success btn-sm rounded-pill"
              type="button"
              @click="goToAvailability"
            >
              <i class="bi bi-calendar-range me-1"></i>
              View availability
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ TREATMENT MODAL (Add / Edit Visit) ============ -->
    <div
      v-if="showTreatmentModal && activeAppointment"
      class="modal-backdrop-custom"
    >
      <div class="modal-card">
        <div class="modal-header d-flex justify-content-between align-items-center">
          <div>
            <h5 class="mb-0">
              {{ hasExistingTreatment ? 'Edit visit sheet' : 'Add visit details' }}
            </h5>
            <p class="small text-muted mb-0">
              Patient:
              <strong>{{ activeAppointment.patient_name }}</strong>
              &nbsp;•&nbsp;
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
              <label class="form-label small fw-semibold">Visit type</label>
              <select
                v-model="treatmentForm.visit_type"
                class="form-select form-select-sm"
              >
                <option value="">Select</option>
                <option value="IN_PERSON">In-person (clinic)</option>
                <option value="ONLINE">Online / teleconsultation</option>
              </select>
            </div>

            <div class="col-md-4">
              <label class="form-label small fw-semibold">Tests (optional)</label>
              <textarea
                v-model="treatmentForm.tests"
                rows="2"
                class="form-control form-control-sm"
                placeholder="One per line, Eg:
CBC
LFT
Chest X-ray"
              ></textarea>
              <div class="form-text small">
                One test per line; shown as comma-separated in history.
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
              <label class="form-label small fw-semibold">Medicines (pattern-based)</label>
              <textarea
                v-model="treatmentForm.medicines"
                rows="3"
                class="form-control form-control-sm"
                placeholder="One per line, Eg:
DOLO 650 | 1-1-1 | 5 days
PANTOP 40 | 1-0-1 | 7 days"
              ></textarea>
              <div class="form-text small">
                <strong>Format:</strong> Name | pattern | days.
                Example patterns:
                <code>1-0-1</code> (morning & night),
                <code>1-1-1</code> (three times / day).
                Patient history converts this into 0/1 grid.
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
                Optional review date.
              </div>
            </div>
          </div>

          <div class="mt-3">
            <label class="form-label small fw-semibold">Precautions</label>
            <textarea
              v-model="treatmentForm.precautions"
              rows="2"
              class="form-control form-control-sm"
              placeholder="Eg: Avoid spicy food, hydrate well, 30-min walk daily."
            ></textarea>
          </div>

          <div class="mt-2">
            <label class="form-label small fw-semibold">Additional notes for patient</label>
            <textarea
              v-model="treatmentForm.notes"
              rows="2"
              class="form-control form-control-sm"
              placeholder="Any extra advice or clinical notes to show in history."
            ></textarea>
          </div>
        </div>

        <div class="modal-footer d-flex justify-content-between align-items-center">
          <div class="small text-muted">
            Saved data will appear in the patient’s
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

    <!-- ============ CUSTOM CONFIRM MODAL ============ -->
    <div v-if="confirmVisible" class="modal-backdrop-custom">
      <div class="modal-card confirm-card">
        <div class="modal-header d-flex justify-content-between align-items-center">
          <div class="d-flex align-items-center gap-2">
            <div class="confirm-icon-circle" :class="confirmVariantClass">
              <i
                v-if="confirmVariant === 'danger'"
                class="bi bi-exclamation-triangle"
              ></i>
              <i
                v-else
                class="bi bi-question-circle"
              ></i>
            </div>
            <h6 class="mb-0">{{ confirmTitle }}</h6>
          </div>
          <button
            type="button"
            class="btn-close"
            @click="hideConfirm"
          ></button>
        </div>

        <div class="modal-body small">
          <p class="mb-0">{{ confirmMessage }}</p>
        </div>

        <div class="modal-footer d-flex justify-content-end gap-2">
          <button
            type="button"
            class="btn btn-outline-secondary btn-sm"
            @click="hideConfirm"
            :disabled="confirmProcessing"
          >
            {{ confirmCancelLabel }}
          </button>
          <button
            type="button"
            class="btn btn-sm"
            :class="confirmPrimaryClass"
            @click="runConfirm"
            :disabled="confirmProcessing"
          >
            <span
              v-if="confirmProcessing"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            {{ confirmPrimaryLabel }}
          </button>
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
const lastRefreshed = ref(null)

const summary = ref(null)
const doctor = computed(() => summary.value?.doctor || null)
const appointmentsToday = computed(() => summary.value?.upcoming_appointments || [])
const assignedPatients = computed(() => summary.value?.assigned_patients || [])

const nextAppointment = computed(() => {
  const list = appointmentsToday.value || []
  return list.length ? list[0] : null
})

const statusFilter = ref('all')
const statusLoadingId = ref(null)
const targetStatus = ref(null)

// Treatment modal state
const showTreatmentModal = ref(false)
const activeAppointment = ref(null)
const hasExistingTreatment = ref(false)
const savingTreatment = ref(false)
const treatmentForm = ref({
  visit_type: '',
  tests: '',
  diagnosis: '',
  medicines: '',
  precautions: '',
  notes: '',
  follow_up_date: ''
})

const todayHuman = new Intl.DateTimeFormat('en-IN', {
  weekday: 'long',
  month: 'short',
  day: 'numeric',
  year: 'numeric'
}).format(new Date())

const lastRefreshedLabel = computed(() => {
  if (!lastRefreshed.value) return 'just now'
  const diffMs = Date.now() - lastRefreshed.value.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin <= 0) return 'just now'
  if (diffMin === 1) return '1 min ago'
  if (diffMin < 60) return `${diffMin} mins ago`
  const diffH = Math.floor(diffMin / 60)
  return `${diffH} hr${diffH > 1 ? 's' : ''} ago`
})

const loadDashboard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/doctor/dashboard-summary')
    summary.value = res.data || {}
    lastRefreshed.value = new Date()
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
  const target = statusFilter.value.toUpperCase()
  return list.filter(a => (a.status || '').toUpperCase() === target)
})

const statusBadgeClass = status => {
  const s = (status || '').toUpperCase()
  if (s === 'COMPLETED') return 'bg-success-soft text-success-emphasis'
  if (s === 'CANCELLED') return 'bg-danger-soft text-danger-emphasis'
  if (s === 'BOOKED') return 'bg-primary-soft text-primary-emphasis'
  return 'bg-secondary-soft text-secondary-emphasis'
}

const statusUpper = appt => (appt.status || '').toUpperCase()

const canComplete = appt => statusUpper(appt) === 'BOOKED'
const canCancel = appt => statusUpper(appt) === 'BOOKED'
const canUpdateVisit = appt => statusUpper(appt) !== 'CANCELLED'

const prettyDate = dateStr => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString()
}

/* ========== Confirm modal state ========== */
const confirmVisible = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmPrimaryLabel = ref('Confirm')
const confirmCancelLabel = ref('Cancel')
const confirmVariant = ref('primary')
const confirmProcessing = ref(false)
const pendingAction = ref(null)

const confirmVariantClass = computed(() =>
  confirmVariant.value === 'danger' ? 'confirm-icon-danger' : 'confirm-icon-primary'
)
const confirmPrimaryClass = computed(() =>
  confirmVariant.value === 'danger' ? 'btn-danger' : 'btn-primary'
)

const showConfirm = (options) => {
  confirmTitle.value = options.title || 'Are you sure?'
  confirmMessage.value = options.message || ''
  confirmPrimaryLabel.value = options.primaryLabel || 'Confirm'
  confirmCancelLabel.value = options.cancelLabel || 'No'
  confirmVariant.value = options.variant || 'primary'
  pendingAction.value = options.onConfirm || null
  confirmVisible.value = true
  confirmProcessing.value = false
}

const hideConfirm = () => {
  if (confirmProcessing.value) return
  confirmVisible.value = false
  pendingAction.value = null
}

/**
 * FIXED: always clears spinner and closes popup even if API fails.
 */
const runConfirm = async () => {
  if (!pendingAction.value) {
    hideConfirm()
    return
  }
  confirmProcessing.value = true
  try {
    await pendingAction.value()
  } catch (e) {
    // errorMessage is set inside pendingAction; just keep popup clean
    console.error('Status change failed', e)
  } finally {
    confirmProcessing.value = false
    hideConfirm()
  }
}

/* ========== Status updates ========== */
const askStatusChange = (appt, newStatus) => {
  const upper = (newStatus || '').toUpperCase()
  if (!appt?.id) return

  let title = ''
  let message = ''
  let primaryLabel = ''
  let variant = 'primary'

  if (upper === 'COMPLETED') {
    title = 'Mark visit as completed?'
    message =
      `This will mark the appointment for ${appt.patient_name || 'the patient'} at ` +
      `${appt.time_slot || ''} as COMPLETED. You can still edit visit details later.`
    primaryLabel = 'Mark completed'
    variant = 'primary'
  } else if (upper === 'CANCELLED') {
    title = 'Cancel this appointment?'
    message =
      `This will cancel the appointment for ${appt.patient_name || 'the patient'} ` +
      `and free up this time slot. This will appear in history.`
    primaryLabel = 'Cancel appointment'
    variant = 'danger'
  } else {
    title = 'Change status?'
    message = `Change status of this appointment to ${upper}?`
    primaryLabel = 'Change status'
    variant = 'primary'
  }

  showConfirm({
    title,
    message,
    primaryLabel,
    cancelLabel: 'No, keep as is',
    variant,
    onConfirm: () => performStatusChange(appt, upper)
  })
}

/**
 * FIXED: rethrows on error so confirm modal can stop loading
 */
const performStatusChange = async (appt, upperStatus) => {
  statusLoadingId.value = appt.id
  targetStatus.value = upperStatus
  errorMessage.value = ''

  try {
    await api.post(`/doctor/appointments/${appt.id}/status`, {
      status: upperStatus
    })
    await loadDashboard()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message ||
      `Failed to update status to ${upperStatus}.`
    throw err           // let runConfirm handle cleanup
  } finally {
    statusLoadingId.value = null
    targetStatus.value = null
  }
}

/* ========== Treatment modal (auto-fill) ========== */
const openTreatment = async (appt) => {
  if (!appt?.id) return

  activeAppointment.value = appt
  showTreatmentModal.value = true
  hasExistingTreatment.value = false
  savingTreatment.value = false
  errorMessage.value = ''

  treatmentForm.value = {
    visit_type: '',
    tests: '',
    diagnosis: '',
    medicines: '',
    precautions: '',
    notes: '',
    follow_up_date: ''
  }

  try {
    const res = await api.get(`/doctor/appointments/${appt.id}/treatment`)
    if (res.data?.exists && res.data.treatment) {
      const t = res.data.treatment
      hasExistingTreatment.value = true

      treatmentForm.value = {
        visit_type: t.visit_type || '',
        tests: t.tests_text || '',
        diagnosis: t.diagnosis || '',
        medicines: t.medicines_text || '',
        precautions: t.precautions || '',
        notes: t.notes || '',
        follow_up_date: t.follow_up_date || ''
      }
    }
  } catch (err) {
    console.error('Failed to load treatment for auto-fill', err)
    // allow doctor to still type fresh
  }
}

const closeTreatment = () => {
  showTreatmentModal.value = false
  activeAppointment.value = null
  hasExistingTreatment.value = false
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
      follow_up_date: treatmentForm.value.follow_up_date || null
    }

    await api.post(
      `/doctor/appointments/${activeAppointment.value.id}/treatment`,
      payload
    )

    await loadDashboard()
    closeTreatment()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to save treatment.'
  } finally {
    savingTreatment.value = false
  }
}

/* ========== Navigation helpers ========== */
const goToPatientHistory = patientId => {
  if (!patientId) return
  router.push({ path: '/doctor/patient-history', query: { patientId } })
}

const goToAllAppointments = () => {
  router.push({ path: '/doctor/appointments' })
}

const goToAvailability = () => {
  router.push({ path: '/doctor/availability' })
}

onMounted(loadDashboard)
</script>

<style scoped>
.doctor-dashboard {
  animation: fadeIn 0.24s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Top toolbar */
.top-toolbar {
  border-radius: 999px;
  padding: 6px 14px;
  background: rgba(248, 250, 252, 0.96);
  border: 1px solid #e5e7eb;
}
.pill-badge {
  font-size: 0.78rem;
  border-radius: 999px;
  padding: 3px 10px;
  background: #eef2ff;
  color: #4338ca;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.pill-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22c55e;
}

/* Banner */
.banner {
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff, #ffffff);
  overflow: hidden;
}
.shadow-soft {
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}
.page-avatar {
  height: 48px;
  width: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  color: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}
.page-title {
  font-weight: 800;
  font-size: 1.1rem;
}
.page-subtitle {
  font-size: 0.85rem;
  color: #4b5563;
}
.chip {
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 999px;
}
.chip-soft {
  background: rgba(59, 130, 246, 0.08);
  color: #1d4ed8;
}

/* Signed-in pill */
.badge-pill-text {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(224, 231, 255, 0.9);
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

/* Next appointment pill */
.next-appt-pill {
  margin-top: 4px;
  padding: 6px 10px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
}
.next-appt-icon {
  height: 28px;
  width: 28px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.95rem;
}
.next-appt-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
}
.next-appt-content {
  max-width: 220px;
}

/* Toolbar buttons */
.toolbar-btn {
  border-radius: 999px;
}

/* Section titles */
.section-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

/* Stat cards */
.stat-card {
  border-radius: 14px;
  padding: 8px 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}
.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}
.stat-header {
  margin-bottom: 4px;
}
.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}
.stat-sub {
  font-size: 0.74rem;
  color: #9ca3af;
}
.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 2px 0;
}
.stat-hint {
  font-size: 0.76rem;
  color: #6b7280;
}
.stat-icon-wrap {
  height: 26px;
  width: 26px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
}
.stat-icon {
  font-size: 0.9rem;
  opacity: 0.85;
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

/* Empty state */
.empty-state .empty-icon {
  font-size: 1.8rem;
  color: #9ca3af;
}

/* Table */
.table-head {
  background: #f9fafb;
}
.appointments-table tbody tr {
  transition: background-color 0.12s ease;
}
.appointments-table tbody tr:hover {
  background-color: #f9fafb;
}
.status-pill {
  padding-inline: 10px;
}

/* Soft badge variants */
.bg-success-soft {
  background: rgba(22, 163, 74, 0.12) !important;
}
.bg-danger-soft {
  background: rgba(220, 38, 38, 0.12) !important;
}
.bg-primary-soft {
  background: rgba(37, 99, 235, 0.12) !important;
}
.bg-secondary-soft {
  background: rgba(148, 163, 184, 0.16) !important;
}

/* Modal backdrop (shared) */
.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

/* Main modal card */
.modal-card {
  width: min(900px, 100% - 32px);
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.35);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.modal-header,
.modal-footer {
  padding: 10px 16px;
}
.modal-header {
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}
.modal-footer {
  border-top: 1px solid #e5e7eb;
}
.modal-body {
  padding: 10px 16px 12px;
  overflow-y: auto;
}

/* Confirm modal smaller card */
.confirm-card {
  width: min(420px, 100% - 32px);
}

/* Confirm icon */
.confirm-icon-circle {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}
.confirm-icon-primary {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}
.confirm-icon-danger {
  background: rgba(220, 38, 38, 0.1);
  color: #b91c1c;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Typography */
.small {
  font-size: 0.8rem;
}
</style>
