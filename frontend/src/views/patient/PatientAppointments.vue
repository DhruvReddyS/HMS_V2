<template>
  <div class="patient-appointments container py-4">
    <!-- HEADER -->
    <div
      class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-calendar-check"></i>
        </div>
        <div>
          <h2 class="page-title">My Appointments</h2>
          <p class="page-subtitle mb-0">
            Track all your upcoming and past visits with doctors in one place.
          </p>
        </div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="loadAppointments"
        >
          <i class="bi bi-arrow-clockwise me-1"></i> Refresh
        </button>
      </div>
    </div>

    <!-- ERROR / SUCCESS -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="alert alert-success py-2 small mb-3">
      {{ successMessage }}
    </div>

    <!-- TABS -->
    <ul class="nav nav-pills nav-sm mb-3">
      <li class="nav-item">
        <button
          class="nav-link"
          :class="{ active: activeTab === 'upcoming' }"
          @click="activeTab = 'upcoming'"
        >
          Upcoming
        </button>
      </li>
      <li class="nav-item">
        <button
          class="nav-link"
          :class="{ active: activeTab === 'past' }"
          @click="activeTab = 'past'"
        >
          Past
        </button>
      </li>
      <li class="nav-item">
        <button
          class="nav-link"
          :class="{ active: activeTab === 'all' }"
          @click="activeTab = 'all'"
        >
          All
        </button>
      </li>
    </ul>

    <!-- LOADING -->
    <div v-if="loading" class="text-center py-5 text-muted small">
      <div class="spinner-border spinner-border-sm mb-2"></div>
      <div>Loading appointments...</div>
    </div>

    <!-- APPOINTMENTS LIST -->
    <div v-else>
      <div
        v-if="filteredAppointments.length === 0"
        class="alert alert-info py-2 small"
      >
        No appointments found in this category.
      </div>

      <div class="appt-list">
        <div
          v-for="appt in filteredAppointments"
          :key="appt.id"
          class="appt-card shadow-sm"
          :class="{ 'appt-card-upcoming': isFutureOrToday(appt) }"
        >
          <div class="row g-0 align-items-stretch">
            <!-- LEFT: DATE BLOCK -->
            <div
              class="col-sm-3 col-md-2 date-block d-flex flex-column align-items-center justify-content-center"
            >
              <div class="date-day-name">
                {{ formatDayName(appt.appointment_date) }}
              </div>
              <div class="date-main">
                {{ formatDay(appt.appointment_date) }}
              </div>
              <div class="date-month-year">
                {{ formatMonthYear(appt.appointment_date) }}
              </div>
              <div v-if="isToday(appt)" class="date-pill-today">
                Today
              </div>
            </div>

            <!-- RIGHT: DETAILS -->
            <div class="col-sm-9 col-md-10">
              <div class="appt-body">
                <div
                  class="d-flex justify-content-between flex-wrap gap-2 mb-1"
                >
                  <div>
                    <div class="small text-muted mb-1">
                      {{ formatFullDate(appt.appointment_date) }}
                      &nbsp;•&nbsp;
                      {{ appt.time_slot || 'Time not set' }}
                    </div>
                    <h6 class="mb-1">
                      Dr. {{ appt.doctor_name || 'Unnamed Doctor' }}
                      <span
                        v-if="appt.doctor_specialization"
                        class="text-muted small"
                      >
                        – {{ appt.doctor_specialization }}
                      </span>
                    </h6>
                    <p class="small text-muted mb-1">
                      Reason:
                      <span class="text-body">
                        {{ appt.reason || 'Not specified' }}
                      </span>
                    </p>
                    <p class="small text-muted mb-0">
                      Appointment ID:
                      <span class="text-body fw-semibold">#{{ appt.id }}</span>
                      <span v-if="appt.doctor_id">
                        • Doctor ID:
                        <span class="text-body">#{{ appt.doctor_id }}</span>
                      </span>
                    </p>
                    <p class="small text-muted mb-0">
                      Created on:
                      <span class="text-body">
                        {{ formatDateTime(appt.created_at) }}
                      </span>
                    </p>
                  </div>

                  <div class="text-end">
                    <span
                      class="badge rounded-pill mb-1"
                      :class="statusBadgeClass(appt.status)"
                    >
                      {{ statusLabel(appt.status) }}
                    </span>

                    <div
                      class="d-flex flex-column gap-1 mt-1 align-items-end"
                    >
                      <button
                        class="btn btn-outline-secondary btn-xs w-100"
                        type="button"
                        @click="viewDetails(appt)"
                      >
                        Details
                      </button>
                      <button
                        v-if="canCancel(appt)"
                        class="btn btn-outline-danger btn-xs w-100"
                        type="button"
                        @click="askCancel(appt)"
                        :disabled="cancellingId === appt.id"
                      >
                        <span
                          v-if="cancellingId === appt.id"
                          class="spinner-border spinner-border-sm me-1"
                        ></span>
                        Cancel appointment
                      </button>
                      <small v-else class="text-muted small mt-1">
                        Cancellation not available
                      </small>
                    </div>
                  </div>
                </div>

                <!-- EXTRA INFO ROW -->
                <div class="appt-extra small text-muted mt-2">
                  <i class="bi bi-info-circle me-1"></i>
                  <span v-if="canCancel(appt)">
                    You can cancel this appointment before the visit date.
                  </span>
                  <span
                    v-else-if="(appt.status || '').toUpperCase() === 'CANCELLED'"
                  >
                    This appointment has been cancelled.
                  </span>
                  <span
                    v-else-if="(appt.status || '').toUpperCase() === 'COMPLETED'"
                  >
                    This appointment is completed. Check your visit history for
                    treatment details.
                  </span>
                  <span v-else>
                    Cancellation depends on date and status set by the
                    hospital.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- /appt-list -->
    </div>

    <!-- FOOTNOTE -->
    <p class="small text-muted mt-3 mb-0">
      Tip: If you are unable to attend, cancel your appointment in advance so
      the slot can be given to another patient.
    </p>

    <!-- DETAILS PANEL (simple modal-style) -->
    <div
      v-if="showDetails && selectedAppointment"
      class="details-backdrop"
      @click.self="closeDetails"
    >
      <div class="details-card">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div>
            <h6 class="mb-1">Appointment Details</h6>
            <p class="small text-muted mb-0">
              Dr. {{ selectedAppointment.doctor_name || 'Unnamed Doctor' }}
              <span
                v-if="selectedAppointment.doctor_specialization"
                class="text-muted small"
              >
                – {{ selectedAppointment.doctor_specialization }}
              </span>
            </p>
          </div>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            @click="closeDetails"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="details-grid small">
          <div>
            <div class="label">Appointment ID</div>
            <div class="value">#{{ selectedAppointment.id }}</div>
          </div>
          <div>
            <div class="label">Status</div>
            <div class="value">
              {{ statusLabel(selectedAppointment.status) }}
            </div>
          </div>
          <div>
            <div class="label">Date</div>
            <div class="value">
              {{ formatFullDate(selectedAppointment.appointment_date) }}
            </div>
          </div>
          <div>
            <div class="label">Time</div>
            <div class="value">
              {{ selectedAppointment.time_slot || 'Not set' }}
            </div>
          </div>
          <div>
            <div class="label">Reason</div>
            <div class="value">
              {{ selectedAppointment.reason || 'Not specified' }}
            </div>
          </div>
          <div>
            <div class="label">Created On</div>
            <div class="value">
              {{ formatDateTime(selectedAppointment.created_at) }}
            </div>
          </div>
        </div>

        <div class="small text-muted mt-2">
          For detailed diagnosis and prescription, please refer to the
          <strong>Visit History</strong> section once your appointment is
          completed.
        </div>
      </div>
    </div>

    <!-- CANCEL CONFIRMATION POPUP -->
    <div
      v-if="showCancelPopup && cancelTarget"
      class="details-backdrop"
      @click.self="closeCancelPopup"
    >
      <div class="details-card">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div>
            <h6 class="mb-1">Cancel Appointment</h6>
            <p class="small text-muted mb-0">
              You are about to cancel your appointment with
              <strong>{{ cancelTarget.doctor_name || 'Unnamed Doctor' }}</strong>.
            </p>
            <p class="small text-muted mb-0">
              {{ formatFullDate(cancelTarget.appointment_date) }}
              • {{ cancelTarget.time_slot || 'Time not set' }}
            </p>
          </div>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            @click="closeCancelPopup"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="small mb-3">
          Are you sure you want to cancel this appointment?
          <br />
          <span class="text-muted">
            This will free up the slot for other patients. You may need to book
            a new appointment if you want to visit again.
          </span>
        </div>

        <div class="d-flex justify-content-end gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            @click="closeCancelPopup"
          >
            Keep appointment
          </button>
          <button
            type="button"
            class="btn btn-sm btn-danger"
            @click="confirmCancel"
            :disabled="cancellingId === cancelTarget.id"
          >
            <span
              v-if="cancellingId === cancelTarget.id"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            Yes, cancel it
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/axios'

const appointments = ref([])
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const activeTab = ref('upcoming')
const cancellingId = ref(null)

// Details modal state
const showDetails = ref(false)
const selectedAppointment = ref(null)

// Cancel popup state
const showCancelPopup = ref(false)
const cancelTarget = ref(null)

/* ---- API ---- */
const loadAppointments = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await api.get('/patient/appointments')
    appointments.value = res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load appointments.'
  } finally {
    loading.value = false
  }
}

const cancelAppointment = async (appt) => {
  cancellingId.value = appt.id
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await api.post(`/patient/appointments/${appt.id}/cancel`)
    successMessage.value = 'Appointment cancelled successfully.'
    await loadAppointments()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to cancel appointment.'
  } finally {
    cancellingId.value = null
  }
}

/* ---- Cancel popup handlers ---- */
const askCancel = (appt) => {
  cancelTarget.value = appt
  showCancelPopup.value = true
}

const closeCancelPopup = () => {
  showCancelPopup.value = false
  cancelTarget.value = null
}

const confirmCancel = async () => {
  if (!cancelTarget.value) return
  await cancelAppointment(cancelTarget.value)
  closeCancelPopup()
}

/* ---- Helpers ---- */

const now = () => new Date()

const isFutureOrToday = (appt) => {
  if (!appt.appointment_date) return false
  const d = new Date(appt.appointment_date)
  d.setHours(0, 0, 0, 0)
  const t = now()
  t.setHours(0, 0, 0, 0)
  return d.getTime() >= t.getTime()
}

const isPast = (appt) => {
  if (!appt.appointment_date) return false
  const d = new Date(appt.appointment_date)
  d.setHours(0, 0, 0, 0)
  const t = now()
  t.setHours(0, 0, 0, 0)
  return d.getTime() < t.getTime()
}

const isToday = (appt) => {
  if (!appt.appointment_date) return false
  const d = new Date(appt.appointment_date)
  const t = now()
  return (
    d.getFullYear() === t.getFullYear() &&
    d.getMonth() === t.getMonth() &&
    d.getDate() === t.getDate()
  )
}

const upcomingAppointments = computed(() =>
  appointments.value.filter(
    (a) =>
      isFutureOrToday(a) && (a.status || '').toUpperCase() !== 'CANCELLED'
  )
)

const pastAppointments = computed(() =>
  appointments.value.filter((a) => isPast(a))
)

const filteredAppointments = computed(() => {
  if (activeTab.value === 'upcoming') return upcomingAppointments.value
  if (activeTab.value === 'past') return pastAppointments.value
  return appointments.value
})

const statusLabel = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'BOOKED') return 'Booked'
  if (s === 'COMPLETED') return 'Completed'
  if (s === 'CANCELLED') return 'Cancelled'
  if (s === 'PENDING') return 'Pending'
  if (s === 'CONFIRMED') return 'Confirmed'
  return status || 'Unknown'
}

const statusBadgeClass = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'BOOKED' || s === 'CONFIRMED')
    return 'bg-primary-subtle text-primary-emphasis'
  if (s === 'COMPLETED') return 'bg-success-subtle text-success-emphasis'
  if (s === 'CANCELLED') return 'bg-danger-subtle text-danger-emphasis'
  if (s === 'PENDING') return 'bg-warning-subtle text-warning-emphasis'
  return 'bg-secondary-subtle text-secondary-emphasis'
}

// Cancel allowed only for future/today & not completed/cancelled
const canCancel = (appt) => {
  const s = (appt.status || '').toUpperCase()
  if (!isFutureOrToday(appt)) return false
  if (s === 'CANCELLED' || s === 'COMPLETED') return false
  // Allow BOOKED / PENDING / CONFIRMED
  return true
}

const formatFullDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatDayName = (dateStr) => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '--'
  return d.toLocaleDateString(undefined, { weekday: 'short' })
}

const formatDay = (dateStr) => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '--'
  return d.getDate().toString().padStart(2, '0')
}

const formatMonthYear = (dateStr) => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '--'
  return d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString()
}

const viewDetails = (appt) => {
  selectedAppointment.value = appt
  showDetails.value = true
}

const closeDetails = () => {
  showDetails.value = false
  selectedAppointment.value = null
}

/* ---- Lifecycle ---- */
onMounted(() => {
  loadAppointments()
})
</script>

<style scoped>
.patient-appointments {
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

/* HEADER */
.page-header {
  border-bottom: 1px solid #edf0f5;
  padding-bottom: 14px;
}
.page-icon {
  height: 48px;
  width: 48px;
  background: linear-gradient(135deg, #e0f2fe, #d1fae5);
  color: #0ea5e9;
  font-size: 1.6rem;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.page-title {
  font-weight: 800;
  margin-bottom: 2px;
}
.page-subtitle {
  color: #6b7280;
  font-size: 0.9rem;
}

/* Tabs */
.nav-sm .nav-link {
  padding: 4px 10px;
  font-size: 0.8rem;
  border-radius: 999px;
}

/* Appointment cards */
.appt-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.appt-card {
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  overflow: hidden;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.appt-card:hover {
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
  transform: translateY(-2px);
}
.appt-card-upcoming {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.date-block {
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  text-align: center;
  padding: 10px 6px;
}
.date-day-name {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}
.date-main {
  font-size: 1.6rem;
  font-weight: 700;
  color: #111827;
}
.date-month-year {
  font-size: 0.8rem;
  color: #6b7280;
}
.date-pill-today {
  margin-top: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.7rem;
  background: #dbeafe;
  color: #1d4ed8;
  display: inline-block;
}

.appt-body {
  padding: 10px 12px;
}

/* Extra info row */
.appt-extra {
  border-top: 1px dashed #e5e7eb;
  padding-top: 6px;
}

/* Buttons */
.btn-xs {
  padding: 2px 8px;
  font-size: 0.75rem;
  border-radius: 999px;
}

/* Modal / popup shared styles */
.details-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.details-card {
  width: 100%;
  max-width: 480px;
  background: #ffffff;
  border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.35);
}

/* Details grid */
.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px 12px;
  margin-top: 6px;
}
.details-grid .label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
}
.details-grid .value {
  font-size: 0.85rem;
  color: #111827;
}

/* Small text */
.small {
  font-size: 0.8rem;
}
</style>
