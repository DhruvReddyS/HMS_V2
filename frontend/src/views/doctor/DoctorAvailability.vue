<template>
  <div class="doctor-availability container py-4">
    <!-- HEADER -->
    <div class="card border-0 shadow-sm mb-3 header-card">
      <div
        class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3"
      >
        <div class="d-flex align-items-center gap-2">
          <div class="page-icon-sm">
            <i class="bi bi-grid-3x3-gap"></i>
          </div>
          <div>
            <h4 class="mb-1">Availability Grid</h4>
            <p class="small text-muted mb-0">
              Next 7 days – tap a slot to mark it as Available or Not available. Booked
              slots are locked.
            </p>
          </div>
        </div>
        <div class="d-flex gap-2">
          <button
            class="btn btn-outline-secondary btn-sm"
            type="button"
            @click="shiftWeek(-7)"
          >
            <i class="bi bi-chevron-left"></i>
          </button>
          <button
            class="btn btn-outline-secondary btn-sm"
            type="button"
            @click="goToToday"
          >
            Today
          </button>
          <button
            class="btn btn-outline-secondary btn-sm"
            type="button"
            @click="shiftWeek(7)"
          >
            <i class="bi bi-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- LEGEND -->
    <div class="card border-0 shadow-sm mb-3">
      <div class="card-body small d-flex flex-wrap align-items-center gap-3">
        <div class="fw-semibold me-2">Legend:</div>
        <div class="legend-item">
          <span class="legend-dot bg-free"></span> Free / Available
        </div>
        <div class="legend-item">
          <span class="legend-dot bg-booked"></span> Booked / Completed (locked)
        </div>
        <div class="legend-item">
          <span class="legend-dot bg-blocked"></span> Blocked / Not available
        </div>
      </div>
    </div>

    <!-- GRID -->
    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <div v-if="loading" class="text-center py-4 small text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>
          Loading availability grid…
        </div>

        <div
          v-else-if="days.length === 0"
          class="small text-muted text-center py-4"
        >
          No availability data found for this period.
        </div>

        <div v-else class="availability-grid">
          <!-- header row -->
          <div class="grid-row grid-row-header">
            <div class="grid-cell time-cell"></div>
            <div
              v-for="day in days"
              :key="day.date"
              class="grid-cell day-header"
            >
              <div class="fw-semibold">
                {{ weekdayShort(day.date) }}
              </div>
              <div class="small text-muted">
                {{ prettyDate(day.date) }}
              </div>
              <!-- 🔹 NEW: full day off button -->
              <button
                type="button"
                class="btn btn-link btn-xs p-0 mt-1 small text-danger"
                @click="markDayOff(day)"
                :disabled="saving"
              >
                <i class="bi bi-moon-stars me-1"></i> Day off
              </button>
            </div>
          </div>

          <!-- slot rows -->
          <div
            v-for="slot in allSlots"
            :key="slot"
            class="grid-row"
          >
            <div class="grid-cell time-cell">
              <span class="time-label">{{ slot }}</span>
            </div>

            <div
              v-for="day in days"
              :key="day.date + '-' + slot"
              class="grid-cell slot-cell"
              :class="slotClass(day, slot)"
              @click="onSlotClick(day, slot)"
            >
              <span class="slot-dot"></span>
              <span class="slot-text small">
                {{ slotStatusText(day, slot) }}
              </span>
            </div>
          </div>
        </div>

        <p class="small text-muted mt-2 mb-0">
          Note: Booked slots cannot be changed from here. To free a booked slot,
          cancel or reschedule the appointment first.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/axios'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')

// always start from TODAY: "YYYY-MM-DD"
const todayIso = () => new Date().toISOString().slice(0, 10)
const startDate = ref(todayIso())

// backend data: [{ date, slots: [...] }]
const rawDays = ref([])

// normalized computed
const days = computed(() => rawDays.value || [])

// compute master slot list based on all days
const allSlots = computed(() => {
  const set = new Set()
  for (const d of days.value) {
    for (const s of d.slots || []) {
      if (s.time_slot) set.add(s.time_slot)
    }
  }
  return Array.from(set).sort()
})

const loadAvailability = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/doctor/availability', {
      params: { start_date: startDate.value },
    })
    // new backend shape: { days: [...] }
    rawDays.value = res.data?.days || res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load availability.'
  } finally {
    loading.value = false
  }
}

const shiftWeek = (deltaDays) => {
  const d = new Date(startDate.value)
  d.setDate(d.getDate() + deltaDays)
  startDate.value = d.toISOString().slice(0, 10)
  loadAvailability()
}

const goToToday = () => {
  startDate.value = todayIso()
  loadAvailability()
}

const prettyDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' })
}

const weekdayShort = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { weekday: 'short' })
}

// ---- slot helpers ----
const findSlot = (day, time) => {
  return (day.slots || []).find((s) => s.time_slot === time) || null
}

// Is a slot booked (BOOKED / COMPLETED)?
const isSlotBooked = (s) => {
  if (!s) return false
  const booking = (s.booking_status || '').toString().toUpperCase()
  if (booking === 'BOOKED' || booking === 'COMPLETED') return true

  // legacy fallback
  const st = (s.status || '').toString().toUpperCase()
  return st === 'BOOKED'
}

// Is a slot available from doctor's schedule POV?
const isSlotAvailable = (s) => {
  if (!s) return true // no override = available
  if (typeof s.is_available === 'boolean') return s.is_available

  // legacy fallback: FREE == available
  const st = (s.status || 'FREE').toString().toUpperCase()
  if (st === 'BLOCKED' || st === 'UNAVAILABLE') return false
  return true
}

/**
 * Class rules:
 * - BOOKED → slot-booked (locked)
 * - NOT booked & is_available=true → slot-free
 * - NOT booked & is_available=false → slot-blocked
 */
const slotClass = (day, time) => {
  const s = findSlot(day, time)

  if (isSlotBooked(s)) return 'slot-booked'
  if (!isSlotAvailable(s)) return 'slot-blocked'
  return 'slot-free'
}

const slotStatusText = (day, time) => {
  const s = findSlot(day, time)
  if (!s) return 'Available'

  if (isSlotBooked(s)) {
    const booking = (s.booking_status || '').toString().toUpperCase()
    if (booking === 'COMPLETED') return 'Completed'
    return 'Booked'
  }

  return isSlotAvailable(s) ? 'Available' : 'Not available'
}

// ---- single-slot toggle ----
const onSlotClick = async (day, time) => {
  if (saving.value || loading.value) return

  const s = findSlot(day, time)

  // prevent editing booked/completed slots
  if (isSlotBooked(s)) {
    alert('This slot is already booked / completed. Cancel the appointment to free it.')
    return
  }

  const currentAvailable = isSlotAvailable(s)
  const nextAvailable = !currentAvailable

  saving.value = true
  errorMessage.value = ''
  try {
    await api.post('/doctor/availability/toggle', {
      date: day.date,
      time_slot: time,
      is_available: nextAvailable,
    })
    await loadAvailability()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to update availability.'
  } finally {
    saving.value = false
  }
}

// ---- full day off (bulk) ----
const markDayOff = async (day) => {
  if (saving.value || loading.value) return

  // Build payload: set all known slots for this day to not available
  const slotsPayload = allSlots.value.map((ts) => ({
    time_slot: ts,
    is_available: false,
  }))

  if (!slotsPayload.length) return

  saving.value = true
  errorMessage.value = ''
  try {
    await api.post('/doctor/availability/bulk', {
      date: day.date,
      slots: slotsPayload,
    })
    await loadAvailability()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to update day availability.'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  goToToday()
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
  background: #7c3aed;
  color: #f5f3ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

/* Legend */
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.legend-dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
}
.bg-free {
  background: #ecfdf3;
  border-color: #bbf7d0;
}
.bg-booked {
  background: #eff6ff;
  border-color: #bfdbfe;
}
.bg-blocked {
  background: #fef2f2;
  border-color: #fecaca;
}

/* Grid */
.availability-grid {
  overflow-x: auto;
}
.grid-row {
  display: grid;
  grid-template-columns: 110px repeat(auto-fit, minmax(120px, 1fr));
  border-bottom: 1px solid #e5e7eb;
}
.grid-row-header {
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}
.grid-cell {
  padding: 8px 10px;
  border-right: 1px solid #e5e7eb;
}
.grid-cell:last-child {
  border-right: none;
}
.time-cell {
  background: #f9fafb;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4b5563;
}
.day-header {
  font-size: 0.82rem;
}
.slot-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  cursor: pointer;
}
.slot-cell.slot-free {
  background: #ffffff;
}
.slot-cell.slot-booked {
  background: #eff6ff;
  cursor: not-allowed;
}
.slot-cell.slot-blocked {
  background: #fef2f2;
}
.slot-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}
.slot-free .slot-dot {
  background: #22c55e;
}
.slot-booked .slot-dot {
  background: #3b82f6;
}
.slot-blocked .slot-dot {
  background: #ef4444;
}
.time-label {
  font-size: 0.78rem;
}
.small {
  font-size: 0.8rem;
}
.btn-xs {
  font-size: 0.7rem;
  line-height: 1;
}
</style>
