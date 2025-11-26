<template>
  <div class="admin-dashboard container py-4">

<!-- ================= HEADER ================= -->
<div class="header-area mb-4">
  <h2 class="page-title">Admin Dashboard</h2>
  <p class="page-subtitle">Monitor key statistics and hospital activity overview.</p>
</div>

<!-- ================= TOP STAT CARDS ================= -->
<div class="row g-4 mb-4">

  <!-- Doctors -->
  <div class="col-md-4">
    <div class="stat-card">
      <div class="stat-icon bg-blue">
        <i class="bi bi-person-badge"></i>
      </div>
      <div class="stat-content">
        <p class="stat-label">Doctors</p>
        <h3 class="stat-number">{{ loadingStats ? '...' : (stats.doctors ?? 0) }}</h3>
      </div>
    </div>
  </div>

  <!-- Patients -->
  <div class="col-md-4">
    <div class="stat-card">
      <div class="stat-icon bg-green">
        <i class="bi bi-people-fill"></i>
      </div>
      <div class="stat-content">
        <p class="stat-label">Patients</p>
        <h3 class="stat-number">{{ loadingStats ? '...' : (stats.patients ?? 0) }}</h3>
      </div>
    </div>
  </div>

  <!-- Appointments -->
  <div class="col-md-4">
    <div class="stat-card">
      <div class="stat-icon bg-yellow">
        <i class="bi bi-calendar-check"></i>
      </div>
      <div class="stat-content">
        <p class="stat-label">Appointments</p>
        <h3 class="stat-number">{{ loadingStats ? '...' : (stats.appointments ?? 0) }}</h3>
      </div>
    </div>
  </div>

</div>

<!-- ================= APPOINTMENT STATUS CARDS ================= -->
<h5 class="section-title mb-3">Appointments Overview</h5>

<div class="row g-4 mb-4">

  <!-- Booked -->
  <div class="col-md-4">
    <div class="mini-card">
      <div class="mini-card-left">
        <p class="mini-card-label">Booked</p>
        <h4 class="mini-card-value">{{ appointmentSummary.booked }}</h4>
      </div>
      <div class="mini-card-icon bg-blue">
        <i class="bi bi-clock-history"></i>
      </div>
    </div>
  </div>

  <!-- Completed -->
  <div class="col-md-4">
    <div class="mini-card">
      <div class="mini-card-left">
        <p class="mini-card-label">Completed</p>
        <h4 class="mini-card-value">{{ appointmentSummary.completed }}</h4>
      </div>
      <div class="mini-card-icon bg-green">
        <i class="bi bi-check2-circle"></i>
      </div>
    </div>
  </div>

  <!-- Cancelled -->
  <div class="col-md-4">
    <div class="mini-card">
      <div class="mini-card-left">
        <p class="mini-card-label">Cancelled</p>
        <h4 class="mini-card-value">{{ appointmentSummary.cancelled }}</h4>
      </div>
      <div class="mini-card-icon bg-red">
        <i class="bi bi-x-octagon"></i>
      </div>
    </div>
  </div>

</div>

    <!-- ================= STATUS FILTER BUTTONS ================= -->
    <div class="filter-buttons mb-3">
      <button
        class="filter-btn"
        :class="{ active: statusFilter === '' }"
        @click="setStatusFilter('')"
      >All</button>

      <button
        class="filter-btn"
        :class="{ active: statusFilter === 'BOOKED' }"
        @click="setStatusFilter('BOOKED')"
      >Booked</button>

      <button
        class="filter-btn"
        :class="{ active: statusFilter === 'COMPLETED' }"
        @click="setStatusFilter('COMPLETED')"
      >Completed</button>

      <button
        class="filter-btn"
        :class="{ active: statusFilter === 'CANCELLED' }"
        @click="setStatusFilter('CANCELLED')"
      >Cancelled</button>
    </div>

    <!-- ================= APPOINTMENT TABLE ================= -->
    <div class="table-card shadow-sm">

      <div v-if="loadingAppointments" class="loading-section">
        <div class="spinner-border spinner-border-sm"></div>
        <p class="text-muted small mt-2">Loading appointments...</p>
      </div>

      <template v-else-if="filteredAppointments.length === 0">
        <p class="text-center py-4 text-muted small">
          No appointments found
          <span v-if="statusFilter">with status {{ statusFilter }}</span>.
        </p>
      </template>

      <div v-else class="table-responsive">
        <table class="table table-hover align-middle">
          <thead>
  <tr>
    <th><i class="bi bi-hash me-1"></i>Appt. ID</th>
    <th><i class="bi bi-person me-1"></i>Patient</th>
    <th><i class="bi bi-person-badge me-1"></i>Doctor</th>
    <th><i class="bi bi-calendar-date me-1"></i>Date</th>
    <th><i class="bi bi-clock me-1"></i>Time</th>
    <th><i class="bi bi-bookmark-check me-1"></i>Status</th>
    <th class="text-end"><i class="bi bi-eye me-1"></i>Action</th>
  </tr>
</thead>

          <tbody>
            <tr v-for="appt in limitedAppointments" :key="appt.id">
              <td>#{{ appt.id }}</td>
              <td>{{ appt.patient_id }}</td>
              <td>{{ appt.doctor_id }}</td>
              <td>{{ appt.date }}</td>
              <td>{{ appt.time }}</td>
              <td>
                <span :class="['badge status-badge', statusBadgeClass(appt.status)]">
                  {{ appt.status }}
                </span>
              </td>
              <td class="text-end">
                <router-link
                  :to="`/admin/appointments/${appt.id}`"
                  class="btn btn-light btn-sm view-btn"
                >View</router-link>
              </td>
            </tr>
          </tbody>

        </table>

        <div class="footer-row small text-muted d-flex justify-content-between px-2 pb-2">
          <span>
            Showing {{ limitedAppointments.length }} of {{ filteredAppointments.length }}
            <span v-if="statusFilter">
              ({{ statusFilter.toLowerCase() }} only)
            </span>
          </span>
          <router-link to="/admin/appointments" class="view-all-link">View All »</router-link>
        </div>

      </div>
    </div>

    <div v-if="errorMessage" class="alert alert-danger small mt-3">
      {{ errorMessage }}
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/axios'
import { authStore } from '../../store/authStore'

const router = useRouter()

// --------- reactive state ---------
const stats = ref({
  doctors: 0,
  patients: 0,
  appointments: 0,
})

const appointments = ref([])

const loadingStats = ref(false)
const loadingAppointments = ref(false)

const errorMessage = ref('')
const statusFilter = ref('') // '', 'BOOKED', 'COMPLETED', 'CANCELLED'

// ✅ rely on router guards, but DON'T redirect here (to avoid weird loops)
// if (authStore.role !== 'admin') {
//   router.push('/login')
// }

// --------- API calls ---------
const fetchStats = async () => {
  loadingStats.value = true
  try {
    const res = await api.get('/admin/stats')
    // defensive: only assign if object
    stats.value = res.data || stats.value
  } catch (err) {
    console.error(err)
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load admin stats.'
  } finally {
    loadingStats.value = false
  }
}

const fetchAppointments = async () => {
  loadingAppointments.value = true
  try {
    const res = await api.get('/admin/appointments')
    appointments.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error(err)
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load appointments.'
  } finally {
    loadingAppointments.value = false
  }
}

// --------- computed helpers ---------
const filteredAppointments = computed(() => {
  if (!statusFilter.value) return appointments.value
  const s = statusFilter.value.toUpperCase()
  return appointments.value.filter(
    (a) => (a.status || '').toUpperCase() === s
  )
})

const limitedAppointments = computed(() =>
  filteredAppointments.value.slice(0, 10)
)

const appointmentSummary = computed(() => {
  const summary = {
    booked: 0,
    completed: 0,
    cancelled: 0,
  }

  for (const a of appointments.value) {
    const s = (a.status || '').toUpperCase()
    if (s === 'BOOKED') summary.booked++
    else if (s === 'COMPLETED') summary.completed++
    else if (s === 'CANCELLED') summary.cancelled++
  }

  return summary
})

const setStatusFilter = (status) => {
  statusFilter.value = status
}

const statusBadgeClass = (status) => {
  const s = (status || '').toUpperCase()
  if (s === 'BOOKED') return 'bg-primary text-white'
  if (s === 'COMPLETED') return 'bg-success text-white'
  if (s === 'CANCELLED') return 'bg-danger text-white'
  return 'bg-secondary text-white'
}

// --------- lifecycle ---------
onMounted(() => {
  fetchStats()
  fetchAppointments()
})
</script>

<style scoped>
/* ================= GLOBAL ================ */

* {
  transition: 0.2s ease;
}

.admin-dashboard {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ================= HEADER ================ */

.page-title {
  font-weight: 800;
  font-size: 2rem;
  letter-spacing: -0.5px;
}

.page-subtitle {
  color: #6d6d6d;
  font-size: 0.9rem;
  margin-top: -3px;
}

/* ================= SHARED CARD STYLES ================ */

.stat-card,
.mini-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;

  border: 1px solid #f0f0f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.stat-card:hover,
.mini-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.10);
}

/* ================= ICON BLOCK ================ */

.stat-icon,
.mini-card-icon {
  width: 65px;
  height: 65px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;

  font-size: 1.9rem;
  font-weight: 700;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
}

/* Soft pastel backgrounds */
.bg-blue   { background: #e2ebff; color: #0d6efd; }
.bg-green  { background: #def7eb; color: #198754; }
.bg-yellow { background: #fff3cd; color: #d6a200; }
.bg-red    { background: #ffe1e1; color: #dc3545; }
.bg-gray   { background: #f0f0f0; color: #6c757d; }

/* ================= CARD TEXT ================ */

.stat-label,
.mini-card-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #9ca3af;
  margin: 0;
}

.stat-number,
.mini-card-value {
  margin-top: 6px;
  color: #111827;
  font-weight: 800;
}

.stat-number { font-size: 2rem; }
.mini-card-value { font-size: 1.7rem; }

/* Label + value stack */
.mini-card-left {
  display: flex;
  flex-direction: column;
}

/* Remove old borders */
.border-blue,
.border-green,
.border-red {
  border-color: transparent !important;
}

/* ================= FILTER BUTTONS ================ */

.filter-buttons {
  display: flex;
  gap: 12px;
}

.filter-btn {
  padding: 7px 18px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  color: #374151;
}

.filter-btn.active {
  background: #0d6efd;
  color: white;
  border-color: #0d6efd;
  box-shadow: 0 6px 16px rgba(13, 110, 253, 0.25);
}

.filter-btn:hover {
  background: #eef1f5;
}

/* ================= TABLE ================ */

.table-card {
  background: #ffffff;
  padding: 20px;
  border-radius: 18px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.table-hover tbody tr:hover {
  background: #f4f6ff !important;
  cursor: pointer;
  transform: scale(1.01);
}

.status-badge {
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Clean badge colors */
.bg-primary { background-color: #0d6efd !important; }
.bg-success { background-color: #198754 !important; }
.bg-danger  { background-color: #dc3545 !important; }

.view-btn {
  font-size: 0.85rem;
  padding: 6px 14px;
  border-radius: 10px;
  background: #f4f6fa;
  border: 1px solid #d9dce1;
  color: #2a2f35;
  font-weight: 500;
  transition: 0.2s ease;
}

.view-btn:hover {
  background: #e9edf3;
  border-color: #bfc4ca;
  color: #0d6efd;
  box-shadow: 0 3px 10px rgba(13, 110, 253, 0.15);
  transform: translateY(-2px);
}

.view-all-link {
  color: #0d6efd;
  font-weight: 600;
  text-decoration: none;
}

.view-all-link:hover {
  text-decoration: underline;
}

/* ================= LOADING ================ */

.loading-section {
  text-align: center;
  padding: 40px;
}
</style>

