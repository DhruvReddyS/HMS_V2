<template>
  <div class="patient-dashboard container py-4">
    <!-- ================= HEADER ================= -->
    <div class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4">
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-hospital"></i>
        </div>
        <div>
          <h2 class="page-title">Patient Dashboard</h2>
          <p class="page-subtitle mb-0">
            Welcome back, manage your health, appointments and information from one place.
          </p>
        </div>
      </div>

      <div class="header-right text-end small text-muted">
        <div v-if="profile">
          Logged in as
          <strong>{{ profile.full_name || 'Patient' }}</strong>
          <span
            v-if="!loadingProfile"
            class="badge rounded-pill ms-2"
            :class="needsProfileCompletion ? 'bg-warning-subtle text-warning' : 'bg-success-subtle text-success'"
          >
            {{ profileCompletion }}% profile complete
          </span>
        </div>
      </div>
    </div>

    <!-- ================= ERROR / INFO ================= -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- ================= PROFILE COMPLETION BANNER ================= -->
    <div
      v-if="needsProfileCompletion"
      class="banner-card d-flex flex-wrap align-items-start align-items-md-center justify-content-between gap-3 mb-4"
    >
      <div class="d-flex align-items-start gap-3">
        <div class="banner-icon">
          <i class="bi bi-exclamation-triangle-fill"></i>
        </div>
        <div>
          <h6 class="banner-title mb-1">Complete your health profile</h6>
          <p class="banner-text mb-1">
            Doctors use this information to understand you before the consultation.
          </p>
          <div class="missing-chips">
            <span
              v-for="item in missingFieldsList"
              :key="item"
              class="missing-chip"
            >
              <i class="bi bi-dot"></i>{{ item }}
            </span>
          </div>
          <p class="banner-note small mb-0">
            This takes less than 2 minutes and helps avoid repeated questions during every visit.
          </p>
        </div>
      </div>

      <div class="banner-actions d-flex flex-column align-items-stretch align-items-md-end gap-2">
        <span class="completion-pill">
          <i class="bi bi-person-check me-1"></i>
          {{ profileCompletion }}% completed
        </span>
        <router-link
          to="/patient/profile"
          class="btn btn-sm btn-primary rounded-pill banner-btn"
        >
          <i class="bi bi-pen me-1"></i> Update Profile
        </router-link>
      </div>
    </div>

    <!-- ================= MAIN GRID ================= -->
    <div class="row g-4">
      <!-- LEFT: QUICK NAV / ACTIONS -->
      <div class="col-lg-8">
        <!-- SECTION TITLE -->
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="section-title mb-0">Quick actions</h6>
          <small class="text-muted">Everything you usually need, one tap away.</small>
        </div>

        <div class="row g-3">
          <!-- Book Appointment -->
          <div class="col-sm-6 col-xl-4">
            <div class="quick-card quick-blue" @click="goTo('/patient/book')">
              <div class="quick-icon">
                <i class="bi bi-calendar-plus"></i>
              </div>
              <div class="quick-content">
                <h6>Book Appointment</h6>
                <p>Find a slot with a suitable doctor.</p>
              </div>
              <div class="quick-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
          </div>

          <!-- My Appointments -->
          <div class="col-sm-6 col-xl-4">
            <div class="quick-card quick-green" @click="goTo('/patient/appointments')">
              <div class="quick-icon">
                <i class="bi bi-calendar-check"></i>
              </div>
              <div class="quick-content">
                <h6>My Appointments</h6>
                <p>See upcoming and previous visits.</p>
              </div>
              <div class="quick-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
          </div>

          <!-- Profile -->
          <div class="col-sm-6 col-xl-4">
            <div class="quick-card quick-purple" @click="goTo('/patient/profile')">
              <div class="quick-icon">
                <i class="bi bi-person-vcard"></i>
              </div>
              <div class="quick-content">
                <h6>My Profile</h6>
                <p>Edit contact and health details.</p>
              </div>
              <div class="quick-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
          </div>

          <!-- Departments -->
          <div class="col-sm-6 col-xl-4">
            <div class="quick-card quick-orange" @click="goTo('/patient/departments')">
              <div class="quick-icon">
                <i class="bi bi-building"></i>
              </div>
              <div class="quick-content">
                <h6>Departments</h6>
                <p>Explore specialties like Cardiology & more.</p>
              </div>
              <div class="quick-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
          </div>

          <!-- Doctors -->
          <div class="col-sm-6 col-xl-4">
            <div class="quick-card quick-blue" @click="goTo('/patient/doctors')">
              <div class="quick-icon">
                <i class="bi bi-people-fill"></i>
              </div>
              <div class="quick-content">
                <h6>Doctors</h6>
                <p>View doctor list and profiles.</p>
              </div>
              <div class="quick-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
          </div>

          <!-- History -->
          <div class="col-sm-6 col-xl-4">
            <div class="quick-card quick-green" @click="goTo('/patient/history')">
              <div class="quick-icon">
                <i class="bi bi-clock-history"></i>
              </div>
              <div class="quick-content">
                <h6>Visit History</h6>
                <p>Past appointments & treatments.</p>
              </div>
              <div class="quick-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- SMALL HELPER INFO -->
        <div class="tips-card mt-3">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-info-circle text-primary pt-1"></i>
            <div>
              <div class="fw-semibold small">Tip</div>
              <p class="small mb-1">
                Always arrive 10–15 minutes before your appointment time. Carry your previous
                prescriptions or reports if available.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: PROFILE SUMMARY -->
      <div class="col-lg-4">
        <div class="card summary-card shadow-sm border-0">
          <div class="card-body" :class="{ 'opacity-50': loadingProfile }">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h6 class="mb-0">Profile summary</h6>
              <span
                class="badge rounded-pill"
                :class="needsProfileCompletion ? 'bg-warning-subtle text-warning' : 'bg-success-subtle text-success'"
              >
                {{ profileCompletion }}%
              </span>
            </div>
            <p class="small text-muted mb-3">
              Basic information that your doctors will see before the consultation.
            </p>

            <div class="summary-row">
              <span class="summary-label">Name</span>
              <span class="summary-value">
                {{ profile?.full_name || 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Username</span>
              <span class="summary-value">
                {{ profile?.username ? '@' + profile.username : 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Email</span>
              <span class="summary-value">
                {{ profile?.email || 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Phone</span>
              <span class="summary-value">
                {{ profile?.phone || 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Gender</span>
              <span class="summary-value">
                {{ profile?.gender || 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Date of Birth</span>
              <span class="summary-value">
                {{ profile?.dob || 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Age</span>
              <span class="summary-value">
                {{ computedAge || 'Not available' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Height</span>
              <span class="summary-value">
                {{ profile?.height_cm ? profile.height_cm + ' cm' : 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Weight</span>
              <span class="summary-value">
                {{ profile?.weight_kg ? profile.weight_kg + ' kg' : 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Blood Group</span>
              <span class="summary-value">
                {{ profile?.blood_group || 'Not set' }}
              </span>
            </div>

            <div class="summary-row">
              <span class="summary-label">Physically Challenged</span>
              <span class="summary-value">
                {{
                  profile?.is_disabled === true
                    ? 'Yes'
                    : profile?.is_disabled === false
                      ? 'No'
                      : 'Not specified'
                }}
              </span>
            </div>

            <button
              class="btn btn-outline-primary btn-sm rounded-pill w-100 mt-3"
              @click="goTo('/patient/profile')"
            >
              <i class="bi bi-pencil-square me-1"></i>
              Edit Profile
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- FOOTNOTE -->
    <p class="small text-muted mt-4 mb-0 text-center text-md-start">
      Keeping your profile updated helps doctors complete your consultation faster and more safely.
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/axios'

const router = useRouter()

const profile = ref(null)
const loadingProfile = ref(false)
const errorMessage = ref('')

const loadProfile = async () => {
  loadingProfile.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/patient/profile')
    profile.value = res.data || {}
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load profile.'
  } finally {
    loadingProfile.value = false
  }
}

/* ---------- Computed helpers ---------- */

const computedAge = computed(() => {
  if (!profile.value?.dob) return null
  const dob = new Date(profile.value.dob)
  if (isNaN(dob.getTime())) return null
  const today = new Date()
  let age = today.getFullYear() - dob.getFullYear()
  const m = today.getMonth() - dob.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
    age--
  }
  return age > 0 ? `${age} yrs` : null
})

const profileCompletion = computed(() => {
  const p = profile.value || {}
  const checks = [
    !!p.phone,
    !!p.gender,
    !!p.dob,
    !!p.height_cm,
    !!p.weight_kg,
    !!p.blood_group,
    p.is_disabled === true || p.is_disabled === false,
  ]
  const total = checks.length
  const filled = checks.filter(Boolean).length
  return Math.round((filled / total) * 100)
})

const needsProfileCompletion = computed(() => profileCompletion.value < 100)

const missingFieldsList = computed(() => {
  const p = profile.value || {}
  const missing = []

  if (!p.phone) missing.push('Phone number')
  if (!p.gender) missing.push('Gender')
  if (!p.dob) missing.push('Date of birth')
  if (!p.height_cm) missing.push('Height')
  if (!p.weight_kg) missing.push('Weight')
  if (!p.blood_group) missing.push('Blood group')
  if (!(p.is_disabled === true || p.is_disabled === false)) {
    missing.push('Physically challenged status')
  }

  return missing.slice(0, 6)
})

const goTo = (path) => {
  router.push(path)
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.patient-dashboard {
  animation: fadeIn 0.35s ease;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
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

/* SECTION TITLE */
.section-title {
  font-size: 0.9rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7280;
}

/* BANNER */
.banner-card {
  background: #fffbeb;
  border-radius: 18px;
  border: 1px solid #facc15;
  padding: 14px 16px;
}
.banner-icon {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: #fef3c7;
  color: #f59e0b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}
.banner-title {
  font-weight: 700;
  font-size: 0.95rem;
}
.banner-text {
  font-size: 0.85rem;
  color: #4b5563;
}
.banner-note {
  color: #6b7280;
}
.missing-chips {
  margin: 4px 0 4px;
}
.missing-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  background: #fef3c7;
  color: #92400e;
  margin: 0 6px 6px 0;
}
.completion-pill {
  background: #f3f4ff;
  color: #4338ca;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  text-align: center;
}
.banner-btn {
  min-width: 160px;
}

/* QUICK CARDS */
.quick-card {
  border-radius: 18px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: 0.2s ease;
  background: #ffffff;
  border: 1px solid #e5e7eb;
}
.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.09);
}
.quick-card h6 {
  margin-bottom: 2px;
  font-weight: 600;
}
.quick-card p {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
}
.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
}
.quick-arrow {
  margin-left: auto;
  color: #6b7280;
}

/* Quick card color variants */
.quick-blue {
  background: #eff6ff;
  border-color: #dbeafe;
}
.quick-blue .quick-icon {
  background: #dbeafe;
  color: #1d4ed8;
}
.quick-green {
  background: #ecfdf3;
  border-color: #bbf7d0;
}
.quick-green .quick-icon {
  background: #bbf7d0;
  color: #15803d;
}
.quick-purple {
  background: #f5f3ff;
  border-color: #ddd6fe;
}
.quick-purple .quick-icon {
  background: #ddd6fe;
  color: #6d28d9;
}
.quick-orange {
  background: #fff7ed;
  border-color: #fed7aa;
}
.quick-orange .quick-icon {
  background: #fed7aa;
  color: #c2410c;
}

/* TIPS CARD */
.tips-card {
  border-radius: 16px;
  border: 1px dashed #d1d5db;
  padding: 8px 12px;
  background: #f9fafb;
}

/* SUMMARY CARD */
.summary-card {
  border-radius: 18px;
}
.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.82rem;
  padding: 4px 0;
  border-bottom: 1px dashed #f3f4f6;
}
.summary-row:last-child {
  border-bottom: none;
}
.summary-label {
  color: #6b7280;
}
.summary-value {
  font-weight: 500;
  color: #111827;
}

/* FOOTNOTE */
.small {
  font-size: 0.8rem;
}
/* FIX: Make all quick cards equal height */
.quick-card {
  min-height: 110px; /* Adjust value until perfect */
  display: flex;
  flex-direction: row;
}
.quick-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

</style>
