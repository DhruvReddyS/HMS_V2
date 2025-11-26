<template>
  <div class="container py-4 patient-doctors">
    <!-- HEADER -->
    <div
      class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon shadow-sm">
          <i class="bi bi-people-fill"></i>
        </div>
        <div>
          <h2 class="page-title">Doctors</h2>
          <p class="page-subtitle mb-1">
            Browse doctors, check their availability and continue to book appointments.
          </p>
          <div v-if="activeDeptLabel" class="small text-muted">
            <i class="bi bi-funnel me-1"></i>
            Filtered by:
            <span class="badge bg-primary-subtle text-primary-emphasis ms-1">
              {{ activeDeptLabel }}
            </span>
          </div>
        </div>
      </div>

      <div class="search-box">
        <div class="input-group input-group-sm">
          <span class="input-group-text bg-light border-end-0">
            <i class="bi bi-search"></i>
          </span>
          <input
            v-model="search"
            type="text"
            class="form-control border-start-0"
            placeholder="Search by name or specialization..."
          />
        </div>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="text-center py-5 text-muted small">
      <div class="spinner-border spinner-border-sm mb-2"></div>
      <div>Loading doctors...</div>
    </div>

    <!-- DOCTORS GRID -->
    <div v-else>
      <div
        v-if="filteredDoctors.length === 0"
        class="small text-muted text-center py-3"
      >
        No doctors match this search or filter.
      </div>

      <div class="row g-4">
        <div
          v-for="d in filteredDoctors"
          :key="d.id"
          class="col-md-6 col-lg-4"
        >
          <div class="doc-card h-100 shadow-sm">
            <div class="d-flex gap-3 mb-2">
              <!-- Avatar -->
              <div class="avatar-circle">
                <span>{{ initials(d.full_name) }}</span>
              </div>

              <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-start">
                  <h6 class="mb-0 doc-name">
                    {{ d.full_name || 'Doctor' }}
                  </h6>
                  <span class="badge spec-pill">
                    {{ d.specialization || 'General' }}
                  </span>
                </div>
                <p class="small text-muted mb-0">
                  Experience: {{ d.experience_years || 0 }} yrs
                </p>
              </div>
            </div>

            <p class="small text-muted mb-3 doc-about">
              {{ d.about || 'Doctor information will be visible here when available.' }}
            </p>

            <div class="d-flex justify-content-between align-items-center mt-auto">
              <button
                class="btn btn-outline-primary btn-sm rounded-pill flex-grow-1 me-2"
                type="button"
                @click="openAvailability(d)"
              >
                <i class="bi bi-calendar-week me-1"></i>
                Check availability
              </button>
              <button
                class="btn btn-outline-secondary btn-sm rounded-pill"
                type="button"
                @click="directBook(d)"
              >
                <i class="bi bi-arrow-right-circle"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AVAILABILITY MODAL -->
    <div v-if="showAvailability" class="modal-backdrop-custom">
      <div class="modal-dialog-custom">
        <div class="modal-content-custom">
          <div class="modal-header-custom">
            <div>
              <div class="small text-muted mb-1">
                Availability for
              </div>
              <h6 class="mb-0">
                Dr. {{ selectedDoctor?.full_name || 'Doctor' }}
                <span v-if="selectedDoctor?.specialization" class="text-muted small">
                  • {{ selectedDoctor.specialization }}
                </span>
              </h6>
            </div>
            <button
              type="button"
              class="btn-close-custom"
              @click="closeAvailability"
            >
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <div class="modal-body-custom">
            <!-- Date selector -->
            <div class="mb-3">
              <label class="form-label small fw-semibold">Select Date</label>
              <input
                type="date"
                v-model="selectedDate"
                :min="today"
                class="form-control form-control-sm"
              />
              <div class="form-text small">
                You can only choose today or a future date.
              </div>
            </div>

            <!-- Slots section -->
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h6 class="small fw-bold mb-0">
                Time Slots
              </h6>
              <button
                class="btn btn-outline-secondary btn-xs"
                type="button"
                @click="loadSlots"
                :disabled="!selectedDate || loadingSlots"
              >
                <span
                  v-if="loadingSlots"
                  class="spinner-border spinner-border-sm me-1"
                ></span>
                Refresh
              </button>
            </div>

            <p class="small text-muted mb-2">
              Green slots are available, red ones are already booked.
            </p>

            <div v-if="slotError" class="alert alert-warning py-1 small mb-2">
              {{ slotError }}
            </div>

            <div v-if="!selectedDate" class="alert alert-info py-1 small mb-2">
              Please select a date to view slots.
            </div>

            <div v-else class="slots-section">
              <div
                v-if="!loadingSlots && slots.length === 0"
                class="alert alert-info py-1 small mb-2"
              >
                No slots configured or available for this date.
              </div>

              <div class="slots-grid">
                <button
                  v-for="s in slots"
                  :key="s.time"
                  type="button"
                  class="slot-pill"
                  :class="slotClasses(s)"
                  :disabled="s.status === 'booked'"
                  @click="selectSlot(s)"
                >
                  {{ s.time }}
                </button>
              </div>

              <div class="slot-legend small text-muted mt-2">
                <span class="legend-dot legend-free"></span> Available
                <span class="legend-dot legend-booked ms-3"></span> Booked
              </div>
            </div>
          </div>

          <div class="modal-footer-custom">
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm rounded-pill"
              @click="closeAvailability"
            >
              Close
            </button>
            <button
              type="button"
              class="btn btn-primary btn-sm rounded-pill"
              :disabled="!canProceedToBook"
              @click="proceedToBook"
            >
              Continue to booking
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api/axios'

const route = useRoute()
const router = useRouter()

const doctors = ref([])
const loading = ref(false)
const errorMessage = ref('')
const search = ref('')

/* Availability modal state */
const showAvailability = ref(false)
const selectedDoctor = ref(null)
const selectedDate = ref('')
const slots = ref([]) // [{time, status: 'free'|'booked'}]
const loadingSlots = ref(false)
const slotError = ref('')
const selectedSlotTime = ref('')

/* Load doctors from backend */
const loadDoctors = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/patient/doctors')
    doctors.value = res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load doctors.'
  } finally {
    loading.value = false
  }
}

/* Active dept filter from query */
const deptFilterRaw = computed(() => (route.query.dept || '').toString())
const activeDeptLabel = computed(() => deptFilterRaw.value || '')

/* Search + dept filtered list */
const filteredDoctors = computed(() => {
  const q = search.value.trim().toLowerCase()
  const deptFilter = deptFilterRaw.value.trim().toLowerCase()

  return doctors.value.filter((d) => {
    const combined = `${d.full_name || ''} ${d.specialization || ''}`.toLowerCase()
    const matchesSearch = !q || combined.includes(q)
    const matchesDept =
      !deptFilter || (d.specialization || '').toLowerCase() === deptFilter
    return matchesSearch && matchesDept
  })
})

/* Helpers */
const initials = (name) => {
  if (!name) return '?'
  const parts = name.trim().split(' ')
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

const today = computed(() => {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
})

/* Availability popup handlers */
const openAvailability = (doctor) => {
  selectedDoctor.value = doctor
  selectedDate.value = ''
  slots.value = []
  slotError.value = ''
  selectedSlotTime.value = ''
  showAvailability.value = true
}

const closeAvailability = () => {
  showAvailability.value = false
}

/* Fetch slots from backend */
const loadSlots = async () => {
  if (!selectedDoctor.value || !selectedDate.value) {
    slotError.value = 'Please select a date first.'
    return
  }
  loadingSlots.value = true
  slotError.value = ''
  slots.value = []
  selectedSlotTime.value = ''

  try {
    const res = await api.get('/patient/available-slots', {
      params: {
        doctor_id: selectedDoctor.value.id,
        date: selectedDate.value,
      },
    })
    // API returns { slots: [{time, status}] }
    slots.value = res.data?.slots || res.data || []
  } catch (err) {
    slotError.value =
      err?.response?.data?.message || 'Failed to load available slots.'
  } finally {
    loadingSlots.value = false
  }
}

const slotClasses = (s) => {
  return {
    'slot-pill-free': s.status === 'free',
    'slot-pill-booked': s.status === 'booked',
    'slot-pill-selected': s.status === 'free' && s.time === selectedSlotTime.value,
  }
}

const selectSlot = (s) => {
  if (s.status === 'booked') return
  selectedSlotTime.value = s.time
}

/* Booking navigation */
const canProceedToBook = computed(
  () => !!(selectedDoctor.value && selectedDate.value && selectedSlotTime.value)
)

/**
 * Goes to booking page with doctor preselected,
 * plus date, time and dept in query string.
 * /patient/book?doctorId=..&date=..&time=..&dept=..
 */
const proceedToBook = () => {
  if (!canProceedToBook.value) return
  const dept = selectedDoctor.value?.specialization || ''
  router.push({
    path: '/patient/book',
    query: {
      doctorId: selectedDoctor.value.id,
      date: selectedDate.value,
      time: selectedSlotTime.value,
      dept,
    },
  })
}

/**
 * Quick direct book (without picking slot here) –
 * just navigate to book page with doctor & dept.
 * User can choose date + time there.
 */
const directBook = (doctor) => {
  const dept = doctor.specialization || ''
  router.push({
    path: '/patient/book',
    query: {
      doctorId: doctor.id,
      dept,
    },
  })
}

/* Lifecycle */
onMounted(() => {
  loadDoctors()
})
</script>

<style scoped>
.patient-doctors {
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
  border-radius: 16px;
  background: linear-gradient(135deg, #e0f2fe, #eff6ff);
  color: #1d4ed8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}
.page-title {
  font-weight: 800;
}
.page-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
}
.search-box {
  min-width: 240px;
}

/* DOCTOR CARDS */
.doc-card {
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  padding: 14px 16px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: 0.2s ease;
}
.doc-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at top right,
    rgba(59, 130, 246, 0.08),
    transparent 55%
  );
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none; 
}

.doc-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
  border-color: #c7d2fe;
}
.doc-card:hover::before {
  opacity: 1;
}

.avatar-circle {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  background: linear-gradient(135deg, #e0f2fe, #fae8ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  color: #1f2933;
  flex-shrink: 0;
}
.doc-name {
  font-weight: 600;
}
.spec-pill {
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.7rem;
}
.doc-about {
  min-height: 40px;
}

/* AVAILABILITY MODAL */
.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.modal-dialog-custom {
  max-width: 480px;
  width: 100%;
  padding: 0 12px;
}
.modal-content-custom {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}
.modal-header-custom {
  padding: 10px 14px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-body-custom {
  padding: 12px 14px 8px;
}
.modal-footer-custom {
  padding: 10px 14px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.btn-close-custom {
  border: none;
  background: transparent;
  padding: 2px;
  cursor: pointer;
  color: #6b7280;
  font-size: 0.9rem;
}

/* SLOTS */
.slots-section {
  min-height: 80px;
}
.slots-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}
.slot-pill {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  border: 1px solid #d1d5db;
  background: #f9fafb;
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

/* Tiny button */
.btn-xs {
  padding: 2px 8px;
  font-size: 0.75rem;
  border-radius: 999px;
}
</style>
