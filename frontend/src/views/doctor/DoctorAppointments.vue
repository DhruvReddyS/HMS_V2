<template>
  <div class="doctor-appointments container py-4">
    <!-- ========= HEADER ========= -->
    <div class="card border-0 shadow-soft mb-3 header-card">
      <div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-2">
          <div class="page-icon-sm">
            <i class="bi bi-calendar2-week"></i>
          </div>
          <div>
            <h4 class="mb-1">Appointments</h4>
            <p class="small text-muted mb-0">
              View, filter and manage all your appointments by date and status.
            </p>
          </div>
        </div>

        <div class="text-end small text-muted">
          <div class="mb-1">
            <span class="pill-badge">
              <span class="pill-dot"></span>
              Doctor view • All appointments
            </span>
          </div>
          <div>
            Last refreshed:
            <strong>{{ lastRefreshedLabel }}</strong>
          </div>
        </div>
      </div>
    </div>

    <!-- ========= ERROR ========= -->
    <transition name="fade">
      <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
        {{ errorMessage }}
      </div>
    </transition>

    <!-- ========= FILTERS ========= -->
    <div class="card border-0 shadow-soft mb-3">
      <div class="card-body small">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
          <div class="section-title mb-0">
            Filters
          </div>
          <div class="small text-muted">
            Showing
            <strong>{{ appointments.length }}</strong>
            appointment(s)
            <span v-if="statusFilter !== 'all'">
              • Status:
              <strong>{{ statusFilter }}</strong>
            </span>
          </div>
        </div>

        <div class="row g-2 align-items-end">
          <div class="col-md-4 col-sm-7">
            <label class="form-label mb-1">Date</label>
            <div class="d-flex gap-2">
              <input
                type="date"
                v-model="dateFilter"
                class="form-control form-control-sm"
                @change="onFilterChange"
              />
              <button
                class="btn btn-light btn-sm"
                type="button"
                @click="setToday"
                :disabled="loading || dateFilter === today"
              >
                Today
              </button>
            </div>
            <div class="small text-muted mt-1">
              <span v-if="dateFilter === today">
                Showing today's appointments.
              </span>
              <span v-else>
                Showing appointments for {{ prettyDate(dateFilter) }}.
              </span>
            </div>
          </div>

          <div class="col-md-3 col-sm-5">
            <label class="form-label mb-1">Status</label>
            <select
              v-model="statusFilter"
              class="form-select form-select-sm"
              @change="onFilterChange"
            >
              <option value="all">All</option>
              <option value="BOOKED">Booked</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div class="col-md-3 col-sm-8">
            <label class="form-label mb-1">Search (patient / reason)</label>
            <input
              type="text"
              v-model="searchTerm"
              class="form-control form-control-sm"
              placeholder="Type patient name, ID or reason"
              @keyup.enter="loadAppointments"
            />
          </div>

          <div class="col-md-2 col-sm-4 d-flex gap-2 justify-content-sm-end">
            <button
              class="btn btn-light btn-sm w-50 d-none d-md-block"
              type="button"
              @click="resetFilters"
              :disabled="loading"
            >
              Clear
            </button>
            <button
              class="btn btn-primary btn-sm w-100"
              type="button"
              @click="loadAppointments"
              :disabled="loading"
            >
              <span
                v-if="loading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              Apply
            </button>
          </div>
        </div>

        <!-- mini status chips -->
        <div v-if="appointments.length" class="d-flex flex-wrap gap-2 mt-3 small">
          <span class="chip chip-soft-primary">
            Total: {{ appointments.length }}
          </span>
          <span class="chip chip-soft-booked">
            Booked:
            {{ countByStatus('BOOKED') }}
          </span>
          <span class="chip chip-soft-completed">
            Completed:
            {{ countByStatus('COMPLETED') }}
          </span>
          <span class="chip chip-soft-cancelled">
            Cancelled:
            {{ countByStatus('CANCELLED') }}
          </span>
        </div>
      </div>
    </div>

    <!-- ========= TABLE ========= -->
    <div class="card border-0 shadow-soft">
      <div class="card-body">
        <div v-if="loading" class="text-center py-4 small text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>
          Loading appointments…
        </div>

        <div
          v-else-if="appointments.length === 0"
          class="empty-state small text-muted text-center py-4"
        >
          <div class="empty-icon mb-2">
            <i class="bi bi-clipboard2-x"></i>
          </div>
          <div class="fw-semibold mb-1">No appointments found.</div>
          <div>Try changing filters or selecting another date.</div>
        </div>

        <div v-else class="table-responsive">
          <table class="table table-sm align-middle mb-0 appointments-table">
            <thead class="table-head small">
              <tr>
                <th>Date & Time</th>
                <th>Patient</th>
                <th>Reason</th>
                <th>Status</th>
                <th style="width: 260px;">Actions</th>
              </tr>
            </thead>
            <tbody class="small">
              <tr v-for="appt in appointments" :key="appt.id">
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
                    {{ (appt.status || '').toUpperCase() || 'UNKNOWN' }}
                  </span>
                </td>
                <td>
                  <div class="d-flex flex-wrap gap-1">
                    <!-- Only allow Complete/Cancel when BOOKED -->
                    <button
                      class="btn btn-outline-success btn-xs"
                      type="button"
                      @click="updateStatus(appt, 'COMPLETED')"
                      :disabled="
                        statusLoadingId === appt.id ||
                        (appt.status || '').toUpperCase() !== 'BOOKED'
                      "
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
                      :disabled="
                        statusLoadingId === appt.id ||
                        (appt.status || '').toUpperCase() !== 'BOOKED'
                      "
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
                      {{ appt.has_treatment ? 'Edit visit' : 'Update visit' }}
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
          Note: Updating status here will also reflect on the doctor dashboard and patient view.
        </p>
      </div>
    </div>

    <!-- ========= TREATMENT MODAL ========= -->
    <div
      v-if="showTreatmentModal && activeAppointment"
      class="modal-backdrop-custom"
    >
      <div class="modal-card">
        <div class="modal-header d-flex justify-content-between align-items-center">
          <div>
            <h5 class="mb-0">Update visit – {{ activeAppointment.patient_name }}</h5>
            <p class="small text-muted mb-0">
              {{ prettyDate(activeAppointment.appointment_date) }} at
              {{ activeAppointment.time_slot }}
            </p>
          </div>
          <button
            type="button"
            class="btn-close"
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
              <label class="form-label small fw-semibold">Tests done / advised</label>
              <input
                type="text"
                v-model="treatmentForm.tests"
                class="form-control form-control-sm"
                placeholder="Eg: CBC, LFT, X-Ray chest"
              />
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
            </div>

            <div class="col-md-4">
              <label class="form-label small fw-semibold">Follow-up date</label>
              <input
                type="date"
                v-model="treatmentForm.follow_up_date"
                class="form-control form-control-sm"
              />
            </div>
          </div>

          <div class="mt-3">
            <label class="form-label small fw-semibold">Precautions</label>
            <textarea
              v-model="treatmentForm.precautions"
              rows="2"
              class="form-control form-control-sm"
              placeholder="Eg: Avoid oily/spicy food, hydrate well"
            ></textarea>
          </div>

          <div class="mt-2">
            <label class="form-label small fw-semibold">Additional notes</label>
            <textarea
              v-model="treatmentForm.notes"
              rows="2"
              class="form-control form-control-sm"
              placeholder="Any extra advice / summary"
            ></textarea>
          </div>
        </div>

        <div class="modal-footer d-flex justify-content-between align-items-center">
          <div class="small text-muted">
            These details will be stored in the patient’s visit history.
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/axios'

const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const appointments = ref([])

const today = new Date().toISOString().slice(0, 10)
const dateFilter = ref(today)
const statusFilter = ref('all')
const searchTerm = ref('')

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

const lastRefreshed = ref(null)
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

const loadAppointments = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/doctor/appointments', {
      params: {
        date: dateFilter.value,
        status: statusFilter.value === 'all' ? undefined : statusFilter.value,
        search: searchTerm.value || undefined
      }
    })
    appointments.value = res.data?.appointments || res.data || []
    lastRefreshed.value = new Date()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load appointments.'
  } finally {
    loading.value = false
  }
}

// called when date/status change
const onFilterChange = () => {
  if (!loading.value) {
    loadAppointments()
  }
}

const setToday = () => {
  dateFilter.value = today
  loadAppointments()
}

const resetFilters = () => {
  dateFilter.value = today
  statusFilter.value = 'all'
  searchTerm.value = ''
  loadAppointments()
}

const prettyDate = dateStr => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString()
}

const statusBadgeClass = status => {
  const s = (status || '').toUpperCase()
  if (s === 'COMPLETED') return 'bg-success-soft text-success-emphasis'
  if (s === 'CANCELLED') return 'bg-danger-soft text-danger-emphasis'
  if (s === 'BOOKED') return 'bg-primary-soft text-primary-emphasis'
  return 'bg-secondary-soft text-secondary-emphasis'
}

const countByStatus = status => {
  const s = status.toUpperCase()
  return appointments.value.filter(
    a => (a.status || '').toUpperCase() === s
  ).length
}

const updateStatus = async (appt, newStatus) => {
  if (!appt?.id) return
  if ((appt.status || '').toUpperCase() !== 'BOOKED') return

  if (newStatus === 'CANCELLED' && !confirm('Cancel this appointment?')) return

  statusLoadingId.value = appt.id
  targetStatus.value = newStatus
  errorMessage.value = ''

  try {
    await api.post(`/doctor/appointments/${appt.id}/status`, { status: newStatus })
    await loadAppointments()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message ||
      `Failed to update status to ${newStatus}.`
  } finally {
    statusLoadingId.value = null
    targetStatus.value = null
  }
}

const openTreatment = appt => {
  activeAppointment.value = appt
  treatmentForm.value = {
    visit_type: '',
    tests: '',
    diagnosis: '',
    medicines: '',
    precautions: '',
    notes: '',
    follow_up_date: ''
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
      follow_up_date: treatmentForm.value.follow_up_date || null
    }

    await api.post(
      `/doctor/appointments/${activeAppointment.value.id}/treatment`,
      payload
    )

    if ((activeAppointment.value.status || '').toUpperCase() === 'BOOKED') {
      await api.post(
        `/doctor/appointments/${activeAppointment.value.id}/status`,
        { status: 'COMPLETED' }
      )
    }

    await loadAppointments()
    closeTreatment()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to save treatment.'
  } finally {
    savingTreatment.value = false
  }
}

const goToPatientHistory = patientId => {
  if (!patientId) return
  router.push({ path: '/doctor/patient-history', query: { patientId } })
}

// 🔹 Automatically show today's appointments on first load
onMounted(loadAppointments)
</script>

<style scoped>
.doctor-appointments {
  animation: fadeIn 0.25s ease-out;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-card {
  border-radius: 18px;
  background: radial-gradient(circle at top left, #e0f2fe, #f5f3ff 40%, #ffffff 85%);
}
.shadow-soft {
  box-shadow: 0 12px 35px rgba(15, 23, 42, 0.06);
}
.page-icon-sm {
  height: 42px;
  width: 42px;
  border-radius: 16px;
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  color: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.45);
}

/* Pill badge */
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

/* Section title */
.section-title {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
}

/* Chips */
.chip {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid transparent;
}
.chip-soft-primary {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
  color: #1d4ed8;
}
.chip-soft-booked {
  background: rgba(59, 130, 246, 0.06);
  border-color: rgba(59, 130, 246, 0.18);
  color: #1d4ed8;
}
.chip-soft-completed {
  background: rgba(22, 163, 74, 0.08);
  border-color: rgba(22, 163, 74, 0.25);
  color: #15803d;
}
.chip-soft-cancelled {
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.25);
  color: #b91c1c;
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

/* Soft status badge colours */
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
.modal-header {
  background: linear-gradient(135deg, #eff6ff, #ffffff);
}
.modal-footer {
  border-top: 1px solid #e5e7eb;
  border-bottom: none;
}
.modal-body {
  padding: 10px 16px 12px;
  overflow-y: auto;
}

/* Buttons */
.btn-xs {
  padding: 2px 8px;
  font-size: 0.75rem;
  border-radius: 999px;
}

/* Fade transition */
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
