<template>
  <div class="patient-profile container py-4">
    <!-- HEADER -->
    <div
      class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-person-badge"></i>
        </div>
        <div>
          <h2 class="page-title">My Profile</h2>
          <p class="page-subtitle mb-0">
            Review and update your personal and health information used during
            consultations.
          </p>
        </div>
      </div>

      <div class="text-end small">
        <span class="badge rounded-pill me-2" :class="profileStatusClass">
          <i class="bi bi-activity me-1"></i>
          {{ profileStatusLabel }}
        </span>
        <div v-if="hasChanges" class="unsaved-pill">
          <i class="bi bi-pencil-square me-1"></i> Unsaved changes
        </div>
        <div v-else class="text-muted">
          <i class="bi bi-check2-circle me-1"></i> All changes saved
        </div>
      </div>
    </div>

    <!-- ERROR / SUCCESS -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="alert alert-success py-2 small mb-3">
      {{ successMessage }}
    </div>

    <!-- MAIN CARD -->
    <div class="card shadow-sm border-0 profile-card">
      <div class="card-body">
        <div class="row g-4">
          <!-- LEFT: SUMMARY & ACCOUNT -->
          <div class="col-lg-4 border-end-md">
            <div class="mb-3">
              <h6 class="section-heading mb-1">Account overview</h6>
              <p class="small text-muted mb-2">
                Basic details linked to your login. Some fields are managed by
                hospital staff.
              </p>
            </div>

            <div class="summary-tile mb-2">
              <div class="summary-label">Full Name</div>
              <div class="summary-value">
                {{ form.full_name || 'Not set' }}
              </div>
            </div>

            <div class="summary-tile mb-2">
              <div class="summary-label">Username</div>
              <div class="summary-value">
                {{ form.username || 'Not set' }}
              </div>
            </div>

            <div class="summary-tile mb-2">
              <div class="summary-label">Email</div>
              <div class="summary-value">
                {{ form.email || 'Not set' }}
              </div>
            </div>

            <div class="summary-tile mb-2">
              <div class="summary-label">Phone</div>
              <div class="summary-value">
                {{ form.phone || 'Not set' }}
              </div>
            </div>

            <div class="summary-tile mb-0">
              <div class="summary-label">Gender • Date of birth</div>
              <div class="summary-value">
                <span>{{ form.gender || 'N/A' }}</span>
                <span v-if="form.dob"> • {{ formattedDob }}</span>
                <span v-else> • DOB not set</span>
              </div>
            </div>

            <hr class="my-3 d-none d-lg-block" />

            <div class="small text-muted">
              <i class="bi bi-info-circle me-1"></i>
              For changes to your name, username or email, please contact the
              hospital administration.
            </div>
          </div>

          <!-- RIGHT: EDIT FORM -->
          <div class="col-lg-8">
            <form @submit.prevent="saveProfile">
              <div class="row g-3">
                <!-- Personal section -->
                <div class="col-12">
                  <h6 class="section-heading mb-1">Personal details</h6>
                  <p class="small text-muted mb-2">
                    Keep your contact and identity information up to date.
                  </p>
                </div>

                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Full Name</label>
                  <input
                    type="text"
                    v-model="form.full_name"
                    class="form-control form-control-sm"
                    :readonly="true"
                  />
                  <div class="form-text small">
                    Name changes are handled by hospital admin.
                  </div>
                </div>

                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Phone</label>
                  <input
                    type="tel"
                    v-model="form.phone"
                    class="form-control form-control-sm"
                    placeholder="10-digit mobile number"
                  />
                </div>

                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Gender</label>
                  <select
                    v-model="form.gender"
                    class="form-select form-select-sm"
                  >
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">
                      Prefer not to say
                    </option>
                  </select>
                </div>

                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Date of Birth</label>
                  <input
                    type="date"
                    v-model="form.dob"
                    class="form-control form-control-sm"
                  />
                </div>

                <div class="col-12">
                  <label class="form-label small fw-semibold">Address</label>
                  <textarea
                    v-model="form.address"
                    rows="2"
                    class="form-control form-control-sm"
                    placeholder="House / Flat, Street, City"
                  ></textarea>
                </div>

                <!-- Health section -->
                <div class="col-12 mt-2">
                  <h6 class="section-heading mb-1">Health profile</h6>
                  <p class="small text-muted mb-2">
                    Doctors refer to these details before and during your
                    consultation.
                  </p>
                </div>

                <div class="col-md-4">
                  <label class="form-label small fw-semibold">Height (cm)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    v-model.number="form.height_cm"
                    class="form-control form-control-sm"
                    placeholder="Eg: 170.5"
                  />
                </div>

                <div class="col-md-4">
                  <label class="form-label small fw-semibold">Weight (kg)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    v-model.number="form.weight_kg"
                    class="form-control form-control-sm"
                    placeholder="Eg: 65.3"
                  />
                </div>

                <div class="col-md-4">
                  <label class="form-label small fw-semibold">Blood Group</label>
                  <select
                    v-model="form.blood_group"
                    class="form-select form-select-sm"
                  >
                    <option value="">Select</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                  </select>
                </div>

                <div class="col-md-6">
                  <label class="form-label small fw-semibold">
                    Physically Challenged
                  </label>
                  <div class="d-flex gap-3">
                    <div class="form-check">
                      <input
                        class="form-check-input"
                        type="radio"
                        id="disabledYes"
                        :value="true"
                        v-model="form.is_disabled"
                      />
                      <label class="form-check-label small" for="disabledYes">
                        Yes
                      </label>
                    </div>
                    <div class="form-check">
                      <input
                        class="form-check-input"
                        type="radio"
                        id="disabledNo"
                        :value="false"
                        v-model="form.is_disabled"
                      />
                      <label class="form-check-label small" for="disabledNo">
                        No
                      </label>
                    </div>
                    <div class="form-check">
                      <input
                        class="form-check-input"
                        type="radio"
                        id="disabledNotSet"
                        :value="null"
                        v-model="form.is_disabled"
                      />
                      <label
                        class="form-check-label small"
                        for="disabledNotSet"
                      >
                        Prefer not to say
                      </label>
                    </div>
                  </div>
                  <div class="form-text small">
                    Sharing this helps staff arrange any special assistance if
                    needed.
                  </div>
                </div>

                <!-- ACTIONS -->
                <div class="col-12 mt-3">
                  <div
                    class="d-flex flex-wrap justify-content-between align-items-center gap-2"
                  >
                    <div class="small text-muted">
                      <i class="bi bi-shield-check me-1"></i>
                      Your details are stored securely and visible only to
                      authorized medical staff.
                    </div>
                    <div class="d-flex gap-2">
                      <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm"
                        @click="resetToOriginal"
                        :disabled="loading || !hasChanges"
                      >
                        Reset
                      </button>
                      <button
                        type="submit"
                        class="btn btn-primary btn-sm"
                        :disabled="loading || !hasChanges"
                      >
                        <span
                          v-if="loading"
                          class="spinner-border spinner-border-sm me-1"
                        ></span>
                        Save changes
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <!-- /row -->
            </form>
          </div>
        </div>
      </div>
    </div>

    <p class="small text-muted mt-3 mb-0">
      Tip: Completing your profile once helps doctors avoid repeated questions
      in every visit and speeds up your consultation.
    </p>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'
import api from '../../api/axios'

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const form = reactive({
  id: null,
  full_name: '',
  username: '',
  email: '',
  phone: '',
  gender: '',
  dob: '',
  address: '',
  height_cm: null,
  weight_kg: null,
  blood_group: '',
  is_disabled: null,
})

const original = ref(null) // snapshot to detect changes

const setFormFromPayload = (p) => {
  form.id = p.id || null
  form.full_name = p.full_name || ''
  form.username = p.username || ''
  form.email = p.email || ''
  form.phone = p.phone || ''
  form.gender = p.gender || ''
  form.dob = p.dob || ''
  form.address = p.address || ''
  form.height_cm = p.height_cm ?? null
  form.weight_kg = p.weight_kg ?? null
  form.blood_group = p.blood_group || ''
  form.is_disabled =
    p.is_disabled === true || p.is_disabled === false ? p.is_disabled : null
}

const snapshotCurrent = () => {
  original.value = {
    id: form.id,
    full_name: form.full_name,
    username: form.username,
    email: form.email,
    phone: form.phone,
    gender: form.gender,
    dob: form.dob,
    address: form.address,
    height_cm: form.height_cm,
    weight_kg: form.weight_kg,
    blood_group: form.blood_group,
    is_disabled: form.is_disabled,
  }
}

const loadProfile = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const res = await api.get('/patient/profile')
    const p = res.data || {}
    setFormFromPayload(p)
    snapshotCurrent()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load profile.'
  } finally {
    loading.value = false
  }
}

const resetToOriginal = () => {
  if (!original.value) return
  setFormFromPayload(original.value)
  errorMessage.value = ''
  successMessage.value = ''
}

const saveProfile = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await api.put('/patient/profile', {
      full_name: form.full_name || null, // backend currently ignores, but safe
      address: form.address || null,
      phone: form.phone || null,
      gender: form.gender || null,
      dob: form.dob || null,
      height_cm: form.height_cm,
      weight_kg: form.weight_kg,
      blood_group: form.blood_group || null,
      is_disabled:
        form.is_disabled === true || form.is_disabled === false
          ? form.is_disabled
          : null,
    })

    successMessage.value = 'Profile updated successfully.'
    snapshotCurrent()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to update profile.'
  } finally {
    loading.value = false
  }
}

/* ---- Computed helpers ---- */

const hasChanges = computed(() => {
  if (!original.value) return false
  const keys = Object.keys(original.value)
  return keys.some((k) => original.value[k] !== form[k])
})

const formattedDob = computed(() => {
  if (!form.dob) return ''
  const d = new Date(form.dob)
  if (isNaN(d.getTime())) return form.dob
  return d.toLocaleDateString()
})

const profileCompletion = computed(() => {
  const checks = [
    !!form.phone,
    !!form.gender,
    !!form.dob,
    !!form.address,
    !!form.height_cm,
    !!form.weight_kg,
    !!form.blood_group,
    form.is_disabled === true || form.is_disabled === false,
  ]
  const total = checks.length
  const filled = checks.filter(Boolean).length
  if (!total) return 0
  return Math.round((filled / total) * 100)
})

const profileStatusLabel = computed(() => {
  const p = profileCompletion.value
  if (p >= 90) return `Profile complete (${p}%)`
  if (p >= 60) return `Almost there (${p}%)`
  return `Incomplete (${p}%)`
})

const profileStatusClass = computed(() => {
  const p = profileCompletion.value
  if (p >= 90) return 'bg-success-subtle text-success-emphasis'
  if (p >= 60) return 'bg-warning-subtle text-warning-emphasis'
  return 'bg-danger-subtle text-danger-emphasis'
})

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.patient-profile {
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

/* Status pills */
.unsaved-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  background: #fee2e2;
  color: #b91c1c;
  font-size: 0.75rem;
}

/* Main card */
.profile-card {
  border-radius: 18px;
}

/* Left summary column */
.border-end-md {
  border-right: 0;
}
@media (min-width: 992px) {
  .border-end-md {
    border-right: 1px solid #e5e7eb;
  }
}

.section-heading {
  font-size: 0.9rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7280;
}

.summary-tile {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f9fafb;
}
.summary-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
  margin-bottom: 2px;
}
.summary-value {
  font-size: 0.85rem;
  color: #111827;
  font-weight: 500;
}

/* Forms */
.form-label {
  margin-bottom: 2px;
}
.form-text {
  color: #9ca3af;
}

/* Small text */
.small {
  font-size: 0.8rem;
}
</style>
