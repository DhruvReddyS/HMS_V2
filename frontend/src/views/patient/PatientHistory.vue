<template>
  <div class="container py-4 patient-history">
    <!-- HEADER -->
    <div class="page-header d-flex justify-content-between flex-wrap align-items-center mb-3">
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-clock-history"></i>
        </div>
        <div>
          <h2 class="page-title">Visit History</h2>
          <p class="page-subtitle mb-0">
            A detailed record of your visits – diagnosis, tests, medicines and precautions.
          </p>
        </div>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- FILTERS -->
    <div class="d-flex flex-wrap gap-2 mb-3">
      <button
        class="btn btn-filter btn-sm"
        :class="{ 'btn-filter-active': activeFilter === 'all' }"
        @click="activeFilter = 'all'"
      >
        All ({{ history.length }})
      </button>
      <button
        class="btn btn-filter btn-sm"
        :class="{ 'btn-filter-active': activeFilter === 'completed' }"
        @click="activeFilter = 'completed'"
      >
        Completed ({{ completedCount }})
      </button>
      <button
        class="btn btn-filter btn-sm"
        :class="{ 'btn-filter-active': activeFilter === 'cancelled' }"
        @click="activeFilter = 'cancelled'"
      >
        Cancelled ({{ cancelledCount }})
      </button>
    </div>

    <!-- CARD WRAPPER -->
    <div class="card border-0 shadow-sm rounded-3">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="section-title mb-0">Appointment-wise history</h6>
          <small class="text-muted">
            {{ filteredHistory.length }} record(s)
          </small>
        </div>

        <!-- LOADING -->
        <div v-if="loading" class="text-center py-4 small text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>
          Loading history...
        </div>

        <!-- EMPTY -->
        <div
          v-else-if="filteredHistory.length === 0"
          class="small text-muted text-center py-3"
        >
          No history available yet.
        </div>

        <!-- LIST -->
        <div v-else class="history-list">
          <div
            v-for="item in filteredHistory"
            :key="item.id"
            class="history-card shadow-sm"
          >
            <!-- TOP ROW: DATE / DOCTOR / STATUS -->
            <div class="d-flex justify-content-between flex-wrap gap-2">
              <div>
                <div class="small text-muted mb-1">
                  {{ formatDate(item.appointment_date) }} •
                  {{ item.time_slot || 'Time not set' }}
                </div>
                <div class="fw-semibold">
                  Dr. {{ item.doctor_name || 'Doctor' }}
                  <span
                    v-if="item.doctor_specialization"
                    class="text-muted small"
                  >
                    ({{ item.doctor_specialization }})
                  </span>
                </div>
                <div class="small text-muted">
                  Reason:
                  <span class="text-body">
                    {{ item.reason || 'Not specified' }}
                  </span>
                </div>
              </div>

              <div class="text-end">
                <span
                  class="badge rounded-pill mb-1"
                  :class="statusBadgeClass(item.status)"
                >
                  {{ (item.status || '').toUpperCase() }}
                </span>
                <div class="small text-muted">
                  Booked on {{ formatDateTime(item.created_at) }}
                </div>
              </div>
            </div>

            <hr class="my-2" />

            <!-- GRID: SUMMARY + TREATMENT SNIPPET -->
            <div class="row g-3 align-items-start">
              <!-- LEFT SUMMARY -->
              <div class="col-md-5">
                <div class="small text-muted mb-1 fw-semibold">
                  Visit summary
                </div>
                <ul class="summary-list small mb-0">
                  <li>
                    <span class="label">Status:</span>
                    <span class="value">
                      {{ prettyStatus(item.status) }}
                    </span>
                  </li>

                  <li v-if="item.treatment">
                    <span class="label">Diagnosis:</span>
                    <span class="value">
                      {{ item.treatment.diagnosis || 'Not recorded' }}
                    </span>
                  </li>

                  <li v-if="parsedNotes(item).visitType">
                    <span class="label">Visit type:</span>
                    <span class="value">
                      {{ prettyVisitType(parsedNotes(item).visitType) }}
                    </span>
                  </li>

                  <li v-if="parsedNotes(item).testsText">
                    <span class="label">Tests:</span>
                    <span class="value">
                      {{ parsedNotes(item).testsText }}
                    </span>
                  </li>

                  <li v-if="item.treatment?.created_at">
                    <span class="label">Updated:</span>
                    <span class="value">
                      {{ formatDateTime(item.treatment.created_at) }}
                    </span>
                  </li>
                </ul>
              </div>

              <!-- RIGHT: QUICK TREATMENT PEEK -->
              <div class="col-md-7">
                <div class="small text-muted mb-1 fw-semibold">
                  Prescription overview
                </div>

                <div v-if="item.treatment">
                  <p class="small mb-1 text-muted">
                    {{ shortPrescription(item.treatment) }}
                  </p>
                  <button
                    type="button"
                    class="btn btn-outline-primary btn-xs rounded-pill"
                    @click="toggleExpanded(item.id)"
                  >
                    <i
                      class="bi"
                      :class="isExpanded(item.id) ? 'bi-chevron-up' : 'bi-chevron-down'"
                    ></i>
                    {{ isExpanded(item.id) ? 'Hide full details' : 'View full details' }}
                  </button>
                </div>

                <div v-else class="small text-muted">
                  Doctor has not added treatment details yet.
                </div>
              </div>
            </div>

            <!-- EXPANDED TREATMENT DETAILS -->
            <transition name="fade">
              <div
                v-if="item.treatment && isExpanded(item.id)"
                class="treatment-details mt-3"
              >
                <div class="row g-3 small">
                  <!-- Column 1: Diagnosis & Tests -->
                  <div class="col-md-4">
                    <h6 class="detail-title">Diagnosis & Tests</h6>

                    <p class="mb-1">
                      <strong>Diagnosis:</strong><br />
                      <span class="text-muted">
                        {{ item.treatment.diagnosis || 'Not recorded' }}
                      </span>
                    </p>

                    <div class="mt-2">
                      <strong>Tests done / advised:</strong>
                      <div v-if="parsedNotes(item).testsArray.length" class="mt-1">
                        <span
                          v-for="(t, idx) in parsedNotes(item).testsArray"
                          :key="idx"
                          class="badge rounded-pill test-chip me-1 mb-1"
                        >
                          {{ t }}
                        </span>
                      </div>
                      <p
                        v-else
                        class="text-muted mb-0"
                      >
                        Not specified
                      </p>
                    </div>
                  </div>

                  <!-- Column 2: Medicines & dosage -->
                  <div class="col-md-4">
                    <h6 class="detail-title">Medicines & dosage pattern</h6>

                    <div
                      v-if="parsedMedicines(item.treatment).length"
                      class="table-responsive mb-1"
                    >
                      <table class="table table-sm align-middle mb-1 meds-table">
                        <thead class="small text-muted">
                          <tr>
                            <th>Medicine</th>
                            <th class="text-center">Morn</th>
                            <th class="text-center">Noon</th>
                            <th class="text-center">Night</th>
                            <th class="text-center">Bed</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="(m, idx) in parsedMedicines(item.treatment)"
                            :key="idx"
                          >
                            <td class="fw-semibold">
                              {{ m.name }}
                              <div class="small text-muted">
                                Pattern: <code>{{ m.pattern }}</code>
                              </div>
                            </td>

                            <td class="text-center">
                              <span
                                v-if="m.morning"
                                class="dose-dot morning"
                                :title="doseTitle('Morning', m.morning)"
                              >
                                {{ m.morning }}
                              </span>
                              <span v-else class="muted-dot">–</span>
                            </td>
                            <td class="text-center">
                              <span
                                v-if="m.afternoon"
                                class="dose-dot noon"
                                :title="doseTitle('Afternoon', m.afternoon)"
                              >
                                {{ m.afternoon }}
                              </span>
                              <span v-else class="muted-dot">–</span>
                            </td>
                            <td class="text-center">
                              <span
                                v-if="m.night"
                                class="dose-dot night"
                                :title="doseTitle('Night', m.night)"
                              >
                                {{ m.night }}
                              </span>
                              <span v-else class="muted-dot">–</span>
                            </td>
                            <td class="text-center">
                              <span
                                v-if="m.bedtime"
                                class="dose-dot bed"
                                :title="doseTitle('Bedtime', m.bedtime)"
                              >
                                {{ m.bedtime }}
                              </span>
                              <span v-else class="muted-dot">–</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                      <p class="small text-muted mb-0">
                        Example: <code>1-0-1</code> = 1 tablet in the morning and night.
                      </p>
                    </div>

                    <p
                      v-else
                      class="text-muted mb-0"
                    >
                      {{ item.treatment.prescription || 'No prescription recorded.' }}
                    </p>
                  </div>

                  <!-- Column 3: Precautions & notes -->
                  <div class="col-md-4">
                    <h6 class="detail-title">Precautions & follow-up</h6>

                    <div class="mb-2">
                      <span class="badge rounded-pill bg-light text-muted border me-1">
                        Visit:
                        {{ parsedNotes(item).visitType
                          ? prettyVisitType(parsedNotes(item).visitType)
                          : 'Not specified'
                        }}
                      </span>
                    </div>

                    <div class="mb-2">
                      <strong>Precautions:</strong><br />
                      <ul v-if="precautionsArray(item).length" class="precautions-list mb-1">
                        <li
                          v-for="(p, idx) in precautionsArray(item)"
                          :key="idx"
                        >
                          {{ p }}
                        </li>
                      </ul>
                      <p v-else class="text-muted mb-1">
                        Not specified
                      </p>
                    </div>

                    <p class="mb-0">
                      <strong>Doctor notes:</strong><br />
                      <span class="text-muted">
                        {{ item.treatment.notes || 'No additional notes recorded.' }}
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <p class="small text-muted mt-3 mb-0">
          This history is appointment-wise. Each visit captures diagnosis, tests,
          medicines, dosage pattern and doctor’s instructions once the doctor
          updates the treatment details in the system.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/axios'

const history = ref([]) // data from /patient/history
const loading = ref(false)
const errorMessage = ref('')

const activeFilter = ref('all') // all | completed | cancelled
const expandedIds = ref(new Set())

/* ------------ API ------------ */
const loadHistory = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/patient/history')
    history.value = res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to fetch history.'
  } finally {
    loading.value = false
  }
}

/* ------------ Counters & filters ------------ */
const completedCount = computed(
  () =>
    history.value.filter(
      (h) => (h.status || '').toUpperCase() === 'COMPLETED'
    ).length
)

const cancelledCount = computed(
  () =>
    history.value.filter(
      (h) => (h.status || '').toUpperCase() === 'CANCELLED'
    ).length
)

const filteredHistory = computed(() => {
  const list = history.value || []
  const filter = activeFilter.value
  if (filter === 'completed') {
    return list.filter(
      (h) => (h.status || '').toUpperCase() === 'COMPLETED'
    )
  }
  if (filter === 'cancelled') {
    return list.filter(
      (h) => (h.status || '').toUpperCase() === 'CANCELLED'
    )
  }
  return list
})

/* ------------ Formatting helpers ------------ */
const prettyStatus = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'COMPLETED') return 'Completed'
  if (s === 'CANCELLED') return 'Cancelled'
  if (s === 'BOOKED') return 'Booked'
  return status || 'Unknown'
}

const statusBadgeClass = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'COMPLETED') return 'bg-success-subtle text-success-emphasis'
  if (s === 'CANCELLED') return 'bg-danger-subtle text-danger-emphasis'
  if (s === 'BOOKED') return 'bg-primary-subtle text-primary-emphasis'
  return 'bg-secondary-subtle text-secondary-emphasis'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString()
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString()
}

/* ------------ Parse notes (Tests, visit type, precautions) ------------ */
/**
 * Notes format from seed / doctor:
 * "Tests done: X, Y | Visit type: IN_PERSON | Precautions: some text"
 */
const parsedNotes = (item) => {
  const t = item.treatment
  const notes = (t && t.notes) || ''
  const out = {
    testsText: '',
    testsArray: [],
    visitType: '',
    precautionsRaw: '',
  }

  if (!notes || typeof notes !== 'string') {
    return out
  }

  const parts = notes.split('|').map((p) => p.trim())

  for (const part of parts) {
    const lower = part.toLowerCase()

    if (lower.startsWith('tests done:') || lower.startsWith('tests:')) {
      const val = part.split(':').slice(1).join(':').trim()
      out.testsText = val
      out.testsArray = val
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
    } else if (lower.startsWith('visit type:')) {
      const val = part.split(':').slice(1).join(':').trim()
      out.visitType = val
    } else if (lower.startsWith('precautions:')) {
      const val = part.split(':').slice(1).join(':').trim()
      out.precautionsRaw = val
    }
  }

  return out
}

const prettyVisitType = (vt) => {
  if (!vt) return 'Not specified'
  const s = vt.toLowerCase()
  if (s.includes('online') || s.includes('virtual')) return 'Online'
  if (s.includes('in_person') || s.includes('in-person') || s.includes('clinic'))
    return 'In person'
  return vt
}

/* Turn precautions string into bullet list */
const precautionsArray = (item) => {
  const raw = parsedNotes(item).precautionsRaw
  if (!raw) return []
  // split by '.' or ';' into short points
  return raw
    .split(/[.;]/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
}

/* ------------ Parse prescription (medicines & pattern) ------------ */
/**
 * Example prescription from seed:
 * "DOLO650-1-1-1 | AZITH500-1-0-0"
 *
 * We map to:
 *   name: "DOLO650"
 *   pattern: "1-1-1"
 *   morning/afternoon/night/bedtime: counts as numbers (0/1/2)
 */
const parsedMedicines = (treatment) => {
  const prescription = (treatment && treatment.prescription) || ''
  if (!prescription || typeof prescription !== 'string') return []

  const chunks = prescription.split('|').map((c) => c.trim()).filter(Boolean)
  const meds = []
  const patternRegex = /(\d(?:-\d){1,3})$/

  for (const chunk of chunks) {
    const match = chunk.match(patternRegex)
    let name = chunk
    let pattern = ''

    if (match) {
      pattern = match[1]
      name = chunk.slice(0, chunk.lastIndexOf(pattern)).replace(/[-–]+$/, '').trim()
    }

    if (!name && !pattern) continue

    const { morning, afternoon, night, bedtime } = decodePatternCounts(pattern)

    meds.push({
      name: name || 'Medicine',
      pattern: pattern || '—',
      morning,
      afternoon,
      night,
      bedtime,
    })
  }

  return meds
}

/* Decode "1-0-1-0" → counts per time slot */
const decodePatternCounts = (pattern) => {
  const parts = (pattern || '').split('-').map((p) => p.trim())
  const safe = [0, 0, 0, 0]

  parts.forEach((val, idx) => {
    if (idx > 3) return
    const num = parseInt(val, 10)
    if (!isNaN(num) && num > 0) {
      safe[idx] = num
    }
  })

  return {
    morning: safe[0],
    afternoon: safe[1],
    night: safe[2],
    bedtime: safe[3],
  }
}

/* Tooltip / title text for dose dot */
const doseTitle = (label, count) => {
  if (!count) return `${label}: none`
  if (count === 1) return `${label}: 1 tablet`
  return `${label}: ${count} tablets`
}

/* Short line for card snippet */
const shortPrescription = (treatment) => {
  const meds = parsedMedicines(treatment)
  if (meds.length) {
    const names = meds.slice(0, 2).map((m) => m.name).filter(Boolean)
    let line = names.join(', ')
    if (meds.length > 2) line += ' + more'
    return line || treatment.prescription || 'Medicines recorded.'
  }
  return treatment.prescription || 'Medicines recorded.'
}

/* expand / collapse helpers */
const isExpanded = (id) => expandedIds.value.has(id)
const toggleExpanded = (id) => {
  const set = new Set(expandedIds.value)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  expandedIds.value = set
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.patient-history {
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.page-header {
  border-bottom: 1px solid #edf0f5;
  padding-bottom: 12px;
}
.page-icon {
  height: 44px;
  width: 44px;
  border-radius: 14px;
  background: #fff7ed;
  color: #c2410c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}
.page-title {
  font-weight: 800;
}
.page-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
}
.section-title {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

/* Filter pills */
.btn-filter {
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  font-size: 0.8rem;
  padding-inline: 12px;
}
.btn-filter-active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}

/* History cards */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.history-card {
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  padding: 12px 14px;
  background: #ffffff;
}

/* Small summary list */
.summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.summary-list li {
  display: flex;
  gap: 4px;
  margin-bottom: 2px;
}
.summary-list .label {
  min-width: 80px;
  color: #6b7280;
}
.summary-list .value {
  flex: 1;
}

/* Treatment details */
.detail-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
  margin-bottom: 4px;
}

/* Tests chips */
.test-chip {
  background: #eef2ff;
  color: #4f46e5;
  border: 1px solid #c7d2fe;
  font-size: 0.7rem;
}

/* Medicines table */
.meds-table th,
.meds-table td {
  padding: 4px 6px;
  font-size: 0.78rem;
}

/* Dose dots */
.dose-dot {
  display: inline-flex;
  min-width: 20px;
  height: 20px;
  border-radius: 999px;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  color: #ffffff;
}
.dose-dot.morning {
  background: #22c55e;
}
.dose-dot.noon {
  background: #eab308;
}
.dose-dot.night {
  background: #3b82f6;
}
.dose-dot.bed {
  background: #6366f1;
}
.muted-dot {
  color: #9ca3af;
  font-size: 0.7rem;
}

/* Precautions bullet list */
.precautions-list {
  padding-left: 18px;
}

/* Buttons */
.btn-xs {
  padding: 2px 8px;
  font-size: 0.75rem;
}

/* Fade transition for details */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
