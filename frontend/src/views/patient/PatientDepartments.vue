<template>
  <div class="container py-4 patient-dept">
    <!-- HEADER -->
    <div
      class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon shadow-sm">
          <i class="bi bi-building"></i>
        </div>
        <div>
          <h2 class="page-title">Departments</h2>
          <p class="page-subtitle mb-0">
            Explore hospital specialties and continue to select a doctor and view availability.
          </p>
        </div>
      </div>

      <div class="small text-muted">
        <i class="bi bi-info-circle me-1"></i>
        Showing only departments that currently have active doctors.
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="text-center py-5 text-muted small">
      <div class="spinner-border spinner-border-sm mb-2"></div>
      <div>Loading departments...</div>
    </div>

    <!-- CONTENT -->
    <div v-else>
      <div
        v-if="departments.length === 0"
        class="alert alert-info py-2 small mb-3"
      >
        No departments available right now. Please check again later.
      </div>

      <div class="row g-4">
        <div
          v-for="d in departments"
          :key="d.key"
          class="col-md-6 col-lg-4"
        >
          <div
            class="dept-card shadow-sm"
            @click="goToDept(d)"
            role="button"
          >
            <!-- Icon + count -->
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div class="dept-icon-wrapper">
                <i :class="d.icon" class="dept-icon"></i>
              </div>
              <span class="badge rounded-pill doctor-count-pill">
                {{ d.doctorCount }}
                {{ d.doctorCount === 1 ? 'Doctor' : 'Doctors' }}
              </span>
            </div>

            <!-- Name + tagline -->
            <h5 class="dept-title mb-1">{{ d.name }}</h5>
            <p class="dept-tagline small mb-2">{{ d.tagline }}</p>

            <!-- Description -->
            <p class="dept-desc small text-muted mb-4">
              {{ d.desc }}
            </p>

            <!-- CTA -->
            <button
              class="btn btn-primary btn-sm rounded-pill w-100 mt-auto"
              type="button"
              @click.stop="goToDept(d)"
            >
              View doctors & availability
            </button>
          </div>
        </div>
      </div>

      <p class="small text-muted mt-3 mb-0">
        Tip: Choose a department to see all doctors under it and check their available slots
        before booking an appointment.
      </p>
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
const doctors = ref([])

/**
 * Static metadata for known specializations.
 * key = Doctor.specialization from DB.
 */
const DEPT_META = [
  {
    key: 'Cardiology',
    name: 'Cardiology',
    tagline: 'Heart & vascular care',
    desc: 'Diagnosis and treatment of chest pain, hypertension, palpitations and other heart-related conditions.',
    icon: 'bi bi-heart-pulse-fill',
  },
  {
    key: 'Orthopedics',
    name: 'Orthopedics',
    tagline: 'Bones, joints & spine',
    desc: 'Fractures, back pain, arthritis, sports injuries and joint problems affecting mobility and posture.',
    icon: 'bi bi-bandaid-fill',
  },
  {
    key: 'Neurology',
    name: 'Neurology',
    tagline: 'Brain, spine & nerves',
    desc: 'Migraine, seizures, stroke follow-up, neuropathy and other neurological conditions.',
    icon: 'bi bi-cpu-fill',
  },
  {
    key: 'Pediatrics',
    name: 'Pediatrics',
    tagline: 'Child & adolescent care',
    desc: 'Growth monitoring, vaccinations and treatment for common childhood illnesses and conditions.',
    icon: 'bi bi-balloon-heart-fill',
  },
  {
    key: 'General Medicine',
    name: 'General Medicine',
    tagline: 'Everyday & primary care',
    desc: 'Fever, infections, lifestyle diseases and routine adult health check-ups.',
    icon: 'bi bi-clipboard2-pulse-fill',
  },
  {
    key: 'Dermatology',
    name: 'Dermatology',
    tagline: 'Skin, hair & nails',
    desc: 'Acne, rashes, hair fall, pigmentation and other dermatological concerns.',
    icon: 'bi bi-droplet-half',
  },
  {
    key: 'Gynecology',
    name: 'Gynecology',
    tagline: 'Women’s health',
    desc: 'Menstrual issues, PCOS, antenatal care and other women’s health concerns.',
    icon: 'bi bi-gender-female',
  },
]

/**
 * Fallback generator for unknown specialization values.
 */
const buildFallbackMeta = (spec) => ({
  key: spec,
  name: spec || 'Other Specialty',
  tagline: 'Specialized clinical care',
  desc: 'Consult qualified specialists for focused evaluation and treatment in this department.',
  icon: 'bi bi-hospital-fill',
})

/**
 * Load doctors from backend:
 * GET /api/patient/doctors
 *
 * Uses your list_patient_doctors route:
 * - Only active doctors (User.is_active = True)
 * - Includes id, full_name, specialization, experience_years
 */
const loadDoctors = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/patient/doctors')
    doctors.value = res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load departments.'
  } finally {
    loading.value = false
  }
}

/**
 * Build departments list based on current doctors in DB.
 * - Group by Doctor.specialization
 * - Attach meta (name/tagline/desc/icon)
 * - Only show depts with at least 1 doctor
 */
const departments = computed(() => {
  const counts = new Map()

  doctors.value.forEach((d) => {
    const spec = d.specialization || 'General Medicine'
    counts.set(spec, (counts.get(spec) || 0) + 1)
  })

  const metaByKey = new Map(DEPT_META.map((m) => [m.key, m]))

  const result = []
  counts.forEach((count, spec) => {
    if (!count) return
    const baseMeta = metaByKey.get(spec) || buildFallbackMeta(spec)
    result.push({
      ...baseMeta,
      doctorCount: count,
    })
  })

  // Sort alphabetically by display name
  return result.sort((a, b) => a.name.localeCompare(b.name))
})

/**
 * Navigate to doctors listing filtered by department.
 * URL: /patient/doctors?dept=<specialization>
 */
const goToDept = (dept) => {
  router.push({
    path: '/patient/doctors',
    query: { dept: dept.key },
  })
}

onMounted(() => {
  loadDoctors()
})
</script>

<style scoped>
/* PAGE ANIMATION */
.patient-dept {
  animation: fadeIn 0.35s ease;
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
  border-bottom: 1px solid #eef0f6;
  padding-bottom: 14px;
}
.page-icon {
  height: 52px;
  width: 52px;
  background: linear-gradient(135deg, #e0f2fe, #f3e8ff);
  color: #4f46e5;
  border-radius: 16px;
  font-size: 1.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.page-title {
  font-weight: 800;
}
.page-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
}

/* DEPARTMENT CARDS */
.dept-card {
  border-radius: 18px;
  padding: 20px 18px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: 0.25s ease;
  position: relative;
  overflow: hidden;
}

/* Glow overlay */
.dept-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at top right,
    rgba(99, 102, 241, 0.08),
    transparent 55%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

/* Hover effect */
.dept-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.12);
  border-color: #c7d2fe;
}
.dept-card:hover::before {
  opacity: 1;
}

/* ICON + COUNT */
.dept-icon-wrapper {
  height: 56px;
  width: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #eef2ff, #e0f2fe);
  display: flex;
  align-items: center;
  justify-content: center;
}
.dept-icon {
  font-size: 1.6rem;
  color: #4f46e5;
}

.doctor-count-pill {
  background: #ecfdf3;
  color: #166534;
  font-size: 0.75rem;
}

/* TEXT */
.dept-title {
  font-weight: 700;
}
.dept-tagline {
  font-size: 0.9rem;
  color: #374151;
}
.dept-desc {
  min-height: 42px;
}

/* Small text */
.small {
  font-size: 0.8rem;
}
</style>
