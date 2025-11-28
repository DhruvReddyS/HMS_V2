<template>
  <div class="patient-book container py-4">
    <!-- HEADER -->
    <div class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4">
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-calendar-plus"></i>
        </div>
        <div>
          <h2 class="page-title">Book Appointment</h2>
          <p class="page-subtitle mb-0">
            Follow the steps to choose a doctor, date and time for your visit.
          </p>
        </div>
      </div>
    </div>

    <!-- PREFILL BANNER -->
    <div
      v-if="isPrefilled"
      class="alert alert-primary py-2 small mb-3 d-flex flex-wrap justify-content-between align-items-center"
    >
      <div>
        Booking for
        <strong>Dr. {{ prefilledDoctorName || 'Selected doctor' }}</strong>
        <span v-if="prefillDept" class="text-muted"> ({{ prefillDept }})</span>
        on
        <strong>{{ selectedDate }}</strong>
        at
        <strong>{{ prefillTime }}</strong>.
      </div>
      <div class="mt-1 mt-md-0 small text-muted">
        Doctor, date and time are pre-selected. You just need to confirm and add reason.
      </div>
    </div>

    <!-- ERROR / SUCCESS TOASTS -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="alert alert-success py-2 small mb-3">
      {{ successMessage }}
    </div>

    <!-- MAIN CARD -->
    <div class="card shadow-sm border-0 booking-card">
      <div class="card-body">
        <!-- STEP INDICATOR -->
        <div class="step-indicator small text-muted mb-3">
          <span class="step-pill step-pill-active">1. Select doctor</span>
          <span
            class="step-pill"
            :class="{ 'step-pill-active': selectedDoctorId }"
          >
            2. Choose date
          </span>
          <span
            class="step-pill"
            :class="{ 'step-pill-active': selectedSlot || prefillTime }"
          >
            3. Pick time
          </span>
          <span
            class="step-pill"
            :class="{ 'step-pill-active': canSubmit }"
          >
            4. Confirm details
          </span>
        </div>

        <div class="row g-3">
          <!-- STEP 1: SPECIALIZATION -->
          <div class="col-md-4">
            <label class="form-label small fw-semibold">
              Specialization
              <span class="text-muted fw-normal">(optional)</span>
            </label>
            <select
              v-model="selectedSpecialization"
              class="form-select form-select-sm"
              :disabled="isPrefilled"
            >
              <option value="">All Specializations</option>
              <option
                v-for="spec in specializations"
                :key="spec"
                :value="spec"
              >
                {{ spec }}
              </option>
            </select>
            <p class="text-muted small mt-1 mb-0">
              Filter doctors by department / specialization.
            </p>
          </div>

          <!-- STEP 1: DOCTOR -->
          <div class="col-md-4">
            <label class="form-label small fw-semibold">
              Doctor
              <span class="text-danger">*</span>
            </label>
            <select
              v-model.number="selectedDoctorId"
              class="form-select form-select-sm"
              :disabled="loadingDoctors || doctors.length === 0 || isPrefilled"
            >
              <option value="">
                {{ loadingDoctors ? 'Loading doctors...' : 'Select a doctor' }}
              </option>
              <option
                v-for="doc in filteredDoctors"
                :key="doc.id"
                :value="doc.id"
              >
                Dr. {{ doc.full_name }} – {{ doc.specialization || 'General' }}
              </option>
            </select>
            <p
              class="text-muted small mt-1 mb-0"
              v-if="!loadingDoctors && doctors.length"
            >
              Choose the doctor you want to consult.
            </p>
            <p
              class="text-muted small mt-1 mb-0"
              v-if="!loadingDoctors && !doctors.length"
            >
              No doctors available. Please contact the hospital.
            </p>
          </div>

          <!-- STEP 2: DATE -->
          <div class="col-md-4">
            <label class="form-label small fw-semibold">
              Preferred Date
              <span class="text-danger">*</span>
            </label>
            <input
              type="date"
              v-model="selectedDate"
              :min="today"
              class="form-control form-control-sm"
              :disabled="isPrefilled"
            />
            <p class="text-muted small mt-1 mb-0">
              You can only choose today or a future date.
            </p>
          </div>
        </div>

        <!-- SELECTED DOCTOR PREVIEW -->
        <div
          v-if="selectedDoctor"
          class="doctor-preview mt-3 d-flex align-items-start gap-3"
        >
          <div class="doctor-avatar">
            <i class="bi bi-person-badge"></i>
          </div>
          <div class="flex-grow-1">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <div>
                <div class="fw-semibold small">
                  Dr. {{ selectedDoctor.full_name }}
                </div>
                <div class="small text-muted">
                  {{ selectedDoctor.specialization || 'General Medicine' }}
                  <span v-if="selectedDoctor.experience_years">
                    • {{ selectedDoctor.experience_years }} yrs experience
                  </span>
                </div>
              </div>
              <span class="badge bg-light text-muted border small">
                Doctor ID: {{ selectedDoctor.id }}
              </span>
            </div>
            <div class="small text-muted">
              <span v-if="selectedDoctor.qualification">
                {{ selectedDoctor.qualification }}
              </span>
              <span v-if="selectedDoctor.hospital_name">
                • {{ selectedDoctor.hospital_name }}
              </span>
            </div>
          </div>
        </div>

        <!-- STEP 3: TIME SLOTS -->
        <div class="mt-4">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0 small fw-bold">Available Time Slots</h6>

            <!-- Refresh button only in normal flow -->
            <button
              v-if="!isPrefilled"
              class="btn btn-outline-secondary btn-sm"
              @click="loadSlots"
              :disabled="!selectedDoctorId || !selectedDate || loadingSlots"
              type="button"
            >
              <span
                v-if="loadingSlots"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              Refresh Slots
            </button>
          </div>

          <p class="small text-muted mb-2" v-if="!isPrefilled">
            Green slots are available. Red slots are already booked or the doctor is
            not available in that time.
          </p>

          <!-- PREFILLED MODE -->
          <div
            v-if="isPrefilled"
            class="alert alert-secondary py-2 small mb-2"
          >
            Selected slot from previous page:
            <strong>{{ prefillTime }}</strong> on
            <strong>{{ selectedDate }}</strong>.
            This slot will be booked if it is still available. If someone else
            has taken it or the doctor is not available anymore, you’ll see a conflict message.
          </div>

          <!-- NORMAL MODE: grid -->
          <div v-else>
            <div
              v-if="!selectedDoctorId || !selectedDate"
              class="alert alert-warning py-2 small mb-2"
            >
              Please select a doctor and date first to view available slots.
            </div>

            <div v-else>
              <div
                v-if="loadingSlots"
                class="alert alert-info py-2 small mb-2 d-flex align-items-center gap-2"
              >
                <span class="spinner-border spinner-border-sm"></span>
                <span>Loading available slots...</span>
              </div>

              <div
                v-if="!loadingSlots && slots.length === 0"
                class="alert alert-info py-2 small mb-2"
              >
                No slots available for the selected date. The doctor may be on leave
                or fully booked. Please try another date.
              </div>

              <div v-if="slots.length" class="slots-grid">
                <button
                  v-for="slot in slots"
                  :key="slot.time"
                  type="button"
                  class="slot-pill"
                  :class="slotClasses(slot)"
                  :disabled="slot.status === 'booked'"
                  @click="selectedSlot = slot.time"
                >
                  {{ slot.time }}
                </button>
              </div>

              <div v-if="slots.length" class="slot-legend small text-muted mt-2">
                <span class="legend-dot legend-free"></span> Available
                <span class="legend-dot legend-booked ms-3"></span> Booked / Not available
                <span class="legend-dot legend-selected ms-3"></span> Selected
              </div>
            </div>
          </div>
        </div>

        <!-- REASON -->
        <div class="mt-4">
          <label class="form-label small fw-semibold">
            Reason / Symptoms
            <span class="text-muted fw-normal">(optional but recommended)</span>
          </label>
          <textarea
            v-model="reason"
            rows="3"
            class="form-control form-control-sm"
            placeholder="Eg: Fever and headache since 3 days"
          ></textarea>
          <div class="d-flex justify-content-between mt-1">
            <p class="small text-muted mb-0">
              Give a brief summary so the doctor can prepare before your visit.
            </p>
            <span class="small text-muted">
              {{ reasonLength }}/300
            </span>
          </div>
        </div>

        <!-- SUMMARY -->
        <div class="mt-4 summary-card border rounded-3 p-3 bg-light">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="small fw-bold mb-0">Appointment Summary</h6>
            <span
              class="badge rounded-pill small"
              :class="canSubmit ? 'bg-success-subtle text-success' : 'bg-warning-subtle text-warning'"
            >
              {{ canSubmit ? 'Ready to book' : 'Incomplete details' }}
            </span>
          </div>

          <div class="small">
            <div class="summary-row">
              <span class="summary-label">Doctor</span>
              <span class="summary-value">
                <template v-if="selectedDoctor">
                  Dr. {{ selectedDoctor.full_name }}
                  <span class="text-muted">
                    ({{ selectedDoctor.specialization || 'General' }})
                  </span>
                </template>
                <template v-else>
                  Not selected
                </template>
              </span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Date</span>
              <span class="summary-value">
                {{ selectedDate || 'Not selected' }}
              </span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Time</span>
              <span class="summary-value">
                {{ selectedSlot || prefillTime || 'Not selected' }}
              </span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Reason</span>
              <span class="summary-value">
                {{ reason ? reason : 'Not provided' }}
              </span>
            </div>
          </div>
        </div>

        <!-- ACTIONS -->
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button
            class="btn btn-outline-secondary btn-sm"
            type="button"
            @click="resetForm()"
            :disabled="submitting"
          >
            Clear
          </button>
          <button
            class="btn btn-primary btn-sm"
            type="button"
            @click="bookAppointment"
            :disabled="submitting || !canSubmit"
          >
            <span
              v-if="submitting"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            Book Appointment
          </button>
        </div>
      </div>
    </div>

    <p class="small text-muted mt-3 mb-0">
      Note: Appointment confirmation will be visible under
      <strong>"My Appointments"</strong>. You will also be able to see all details
      like doctor name, date, time and reason there.
    </p>

    <!-- SUCCESS MODAL -->
    <div v-if="showSuccessModal" class="success-backdrop">
      <div class="success-modal card shadow-lg">
        <div class="card-body">
          <div class="d-flex align-items-center mb-2">
            <div class="success-icon me-2">
              <i class="bi bi-check2-circle"></i>
            </div>
            <div>
              <h5 class="mb-0">Appointment booked!</h5>
              <p class="small text-muted mb-0">
                Your appointment has been booked successfully.
              </p>
            </div>
          </div>

          <div v-if="lastBooked" class="small mb-3">
            <div class="summary-row">
              <span class="summary-label">Doctor</span>
              <span class="summary-value">
                Dr. {{ lastBooked.doctorName }}
                <span v-if="lastBooked.doctorSpec" class="text-muted">
                  ({{ lastBooked.doctorSpec }})
                </span>
              </span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Date</span>
              <span class="summary-value">{{ lastBooked.date }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Time</span>
              <span class="summary-value">{{ lastBooked.time }}</span>
            </div>
          </div>

          <div class="d-flex justify-content-end gap-2">
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm"
              @click="handleSuccessRedirect"
            >
              Close
            </button>
            <button
              type="button"
              class="btn btn-success btn-sm"
              @click="handleSuccessRedirect"
            >
              Go to My Appointments
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/axios'

const route = useRoute()
const router = useRouter()

const doctors = ref([])
const selectedSpecialization = ref('')
const selectedDoctorId = ref('')
const selectedDate = ref('')
const slots = ref([]) // [{ time, status }]
const selectedSlot = ref('')
const reason = ref('')

const loadingDoctors = ref(false)
const loadingSlots = ref(false)
const submitting = ref(false)

const errorMessage = ref('')
const successMessage = ref('')

/* PREFILL STATE FROM URL */
const prefillDoctorId = ref(null)
const prefillDept = ref('')
const prefillDate = ref('')
const prefillTime = ref('')

const isPrefilled = computed(
  () => !!(prefillDoctorId.value && prefillDate.value && prefillTime.value)
)

/* SUCCESS MODAL STATE */
const showSuccessModal = ref(false)
const lastBooked = ref(null)

const specializations = computed(() => {
  const set = new Set()
  doctors.value.forEach((d) => {
    if (d.specialization) set.add(d.specialization)
  })
  return Array.from(set)
})

const filteredDoctors = computed(() => {
  if (!selectedSpecialization.value) return doctors.value
  return doctors.value.filter(
    (d) => d.specialization === selectedSpecialization.value
  )
})

const selectedDoctor = computed(
  () => doctors.value.find((d) => d.id === selectedDoctorId.value) || null
)

const today = computed(() => {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
})

const canSubmit = computed(() => {
  const hasBase =
    selectedDoctorId.value &&
    selectedDate.value &&
    (selectedSlot.value || prefillTime.value)
  return !!(hasBase && !submitting.value)
})

const reasonLength = computed(() =>
  Math.min((reason.value || '').length, 300)
)

const prefilledDoctorName = computed(() => {
  if (!prefillDoctorId.value) return ''
  const doc = doctors.value.find((d) => d.id === prefillDoctorId.value)
  return doc?.full_name || ''
})

/* Clear + auto-load slots on doctor/date change (only when not prefilled) */
watch(
  [selectedDoctorId, selectedDate],
  async ([docId, dateVal]) => {
    if (isPrefilled.value) return
    slots.value = []
    selectedSlot.value = ''

    if (docId && dateVal) {
      await loadSlots()
    }
  }
)

const loadDoctors = async () => {
  loadingDoctors.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/patient/doctors')
    doctors.value = res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load doctors.'
  } finally {
    loadingDoctors.value = false
  }
}

const loadSlots = async () => {
  if (!selectedDoctorId.value || !selectedDate.value) return
  loadingSlots.value = true
  errorMessage.value = ''
  slots.value = []
  if (!isPrefilled.value) selectedSlot.value = ''

  try {
    const res = await api.get('/patient/available-slots', {
      params: {
        doctor_id: selectedDoctorId.value,
        date: selectedDate.value,
      },
    })
    // [{ time: "10:00", status: "free" | "booked" }]
    slots.value = res.data?.slots || res.data || []

    // In prefill flow, re-check that the chosen time is still free
    if (prefillTime.value) {
      const found = slots.value.find(
        (s) => s.time === prefillTime.value && s.status === 'free'
      )
      if (found) {
        selectedSlot.value = prefillTime.value
      } else {
        // optional: clear selected slot if it's no longer free
        selectedSlot.value = ''
      }
    }
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load available slots.'
  } finally {
    loadingSlots.value = false
  }
}

const bookAppointment = async () => {
  if (!canSubmit.value) {
    errorMessage.value = 'Please select doctor, date and time slot.'
    return
  }

  if (selectedDate.value < today.value) {
    errorMessage.value = 'Appointment date cannot be in the past.'
    return
  }

  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const payload = {
      doctor_id: selectedDoctorId.value,
      appointment_date: selectedDate.value,
      time_slot: selectedSlot.value || prefillTime.value,
      reason: reason.value?.trim() || null,
    }

    await api.post('/patient/appointments', payload)

    // Snapshot summary for popup
    lastBooked.value = {
      doctorName: selectedDoctor.value?.full_name || '',
      doctorSpec: selectedDoctor.value?.specialization || '',
      date: selectedDate.value,
      time: selectedSlot.value || prefillTime.value,
    }

    successMessage.value = 'Appointment booked successfully.'
    showSuccessModal.value = true
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to book appointment.'
  } finally {
    submitting.value = false
  }
}

const resetForm = (clearDoctors = false) => {
  if (isPrefilled.value) {
    selectedSpecialization.value = prefillDept.value || ''
    selectedDoctorId.value = prefillDoctorId.value || ''
    selectedDate.value = prefillDate.value || ''
  } else {
    selectedSpecialization.value = ''
    selectedDoctorId.value = ''
    selectedDate.value = ''
  }

  slots.value = []
  selectedSlot.value = ''
  reason.value = ''
  errorMessage.value = ''
  successMessage.value = ''

  if (clearDoctors) doctors.value = []
}

const slotClasses = (slot) => ({
  'slot-pill-free': slot.status === 'free',
  'slot-pill-booked': slot.status === 'booked',
  'slot-pill-selected':
    slot.status === 'free' && slot.time === selectedSlot.value,
})

const applyPrefillFromRoute = async () => {
  const q = route.query
  const doctorIdQ = q.doctorId ? Number(q.doctorId) : null
  const deptQ = (q.dept || '').toString()
  const dateQ = (q.date || '').toString()
  const timeQ = (q.time || '').toString()

  prefillDoctorId.value = doctorIdQ
  prefillDept.value = deptQ
  prefillDate.value = dateQ
  prefillTime.value = timeQ

  if (doctorIdQ) selectedDoctorId.value = doctorIdQ
  if (deptQ) selectedSpecialization.value = deptQ
  if (dateQ) selectedDate.value = dateQ

  if (doctorIdQ && dateQ) {
    await loadSlots()
  }
}

/* redirect handler for popup */
const handleSuccessRedirect = () => {
  showSuccessModal.value = false
  resetForm(false)
  router.push('/patient/appointments')
}

onMounted(async () => {
  await loadDoctors()
  await applyPrefillFromRoute()
})
</script>

<style scoped>
.patient-book {
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
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

.booking-card {
  border-radius: 18px;
}

/* Step indicator */
.step-indicator {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.step-pill {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px dashed #d1d5db;
}
.step-pill-active {
  border-style: solid;
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}

/* Doctor preview */
.doctor-preview {
  border-radius: 14px;
  border: 1px dashed #e5e7eb;
  padding: 10px 12px;
  background: #f9fafb;
}
.doctor-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: #e0f2fe;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  color: #0ea5e9;
}

/* Slots */
.slots-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.slot-pill {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  font-size: 0.8rem;
  cursor: pointer;
  transition: 0.15s ease;
}

.slot-pill-free {
  background: #ecfdf3;
  border-color: #bbf7d0;
  color: #166534;
}
.slot-pill-booked {
  background: #fee2e2;
  border-color: #fecaca;
  color: #b91c1c;
  cursor: not-allowed;
  opacity: 0.75;
}
.slot-pill-selected {
  background: #16a34a;
  border-color: #15803d;
  color: #ffffff;
  box-shadow: 0 0 0 1px rgba(22, 163, 74, 0.3);
}
.slot-pill:hover.slot-pill-free:not(.slot-pill-selected) {
  background: #dcfce7;
}

.slot-legend .legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-right: 4px;
}
.legend-free {
  background: #22c55e;
}
.legend-booked {
  background: #ef4444;
}
.legend-selected {
  background: #16a34a;
}

/* Summary */
.summary-card .summary-row,
.success-modal .summary-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px dashed #e5e7eb;
}
.summary-card .summary-row:last-child,
.success-modal .summary-row:last-child {
  border-bottom: none;
}
.summary-label {
  color: #6b7280;
}
.summary-value {
  font-weight: 500;
  color: #111827;
}

/* SUCCESS MODAL */
.success-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.success-modal {
  border-radius: 16px;
  max-width: 420px;
  width: 100%;
}
.success-icon {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #dcfce7;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #16a34a;
}

/* Generic small text */
.small {
  font-size: 0.8rem;
}
</style>
