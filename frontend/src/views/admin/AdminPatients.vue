<template>
  <div class="manage-patients container py-4">

    <!-- =================== PAGE HEADER =================== -->
    <div class="page-header d-flex justify-content-between flex-wrap align-items-center mb-4">
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-person-heart"></i>
        </div>
        <div>
          <h2 class="page-title">Manage Patients</h2>
          <p class="page-subtitle">Search, filter, add and manage hospital patients.</p>
        </div>
      </div>

      <div class="header-actions d-flex flex-wrap gap-2">
        <span class="count-pill">
          <i class="bi bi-people-fill me-1"></i>{{ filteredPatients.length }} patients
        </span>

        <button class="btn rounded-pill btn-sm header-btn outline" @click="reload">
          <i class="bi bi-arrow-clockwise me-1"></i> Refresh
        </button>

        <button class="btn rounded-pill btn-sm header-btn primary" @click="startCreate">
          <i class="bi bi-plus-circle me-1"></i> Add Patient
        </button>
      </div>
    </div>

    <!-- =================== FILTERS =================== -->
    <div class="card filter-card shadow-sm border-0 mb-4">
      <div class="card-body pb-3">
        <div class="row g-3 align-items-center">
          <!-- Search -->
          <div class="col-md-5">
            <div class="input-group custom-search">
              <span class="input-group-text">
                <i class="bi bi-search text-muted"></i>
              </span>
              <input
                v-model="search"
                placeholder="Search by id, name, username, email, phone, gender, status..."
                class="form-control"
              />
            </div>
          </div>

          <!-- Status Filter -->
          <div class="col-md-4">
            <div class="status-toggle">
              <button
                class="status-btn"
                :class="{ active: filterStatus === 'all' }"
                @click="setFilterStatus('all')"
              >
                All
              </button>

              <button
                class="status-btn"
                :class="{ active: filterStatus === 'active' }"
                @click="setFilterStatus('active')"
              >
                Active
              </button>

              <button
                class="status-btn"
                :class="{ active: filterStatus === 'inactive' }"
                @click="setFilterStatus('inactive')"
              >
                Inactive
              </button>
            </div>
          </div>

          <!-- Sorting -->
          <div class="col-md-3 text-md-end">
            <div class="sort-box">
              <i class="bi bi-arrow-down-up sort-icon"></i>
              <select v-model="sortBy" class="form-select form-select-sm sort-select">
                <option value="name">Name (A–Z)</option>
                <option value="age">Age (High → Low)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- =================== ERROR =================== -->
    <div v-if="errorMessage" class="alert alert-danger py-2 small mb-3">
      {{ errorMessage }}
    </div>

    <!-- =================== TABLE =================== -->
    <div class="card patients-card shadow-sm border-0">
      <div class="card-body p-0">

        <div v-if="loading" class="loader-wrapper">
          <div class="spinner-border spinner-border-sm"></div>
          <p class="text-muted mt-2 small">Loading patients...</p>
        </div>

        <div v-else-if="filteredPatients.length === 0" class="no-results">
          <i class="bi bi-emoji-frown text-muted fs-3 d-block mb-2"></i>
          No patients match your search or filters.
        </div>

        <div v-else class="table-responsive">
          <table class="table patients-table align-middle mb-0">
            <thead>
              <tr>
                <th>#ID</th>
                <th>Name</th>
                <th>Username</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Gender</th>
                <th>Age</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="p in filteredPatients" :key="p.id">
                <td class="text-muted">#{{ p.id }}</td>

                <td class="fw-semibold">{{ p.full_name }}</td>

                <td>
                  <span class="username-chip">
                    <i class="bi bi-person-badge me-1"></i>@{{ p.username }}
                  </span>
                </td>

                <td class="text-muted">{{ p.email }}</td>

                <td>
                  <span class="pill pill-phone">
                    <i class="bi bi-telephone"></i> {{ p.phone || '—' }}
                  </span>
                </td>

                <td>
                  <span class="pill pill-gender">
                    <i class="bi bi-person"></i> {{ p.gender || '—' }}
                  </span>
                </td>

                <td>
                  <span class="pill pill-age">
                    <i class="bi bi-cake2"></i> {{ p.age ?? '—' }}
                  </span>
                </td>

                <td>
                  <span
                    class="status-badge"
                    :class="p.is_active ? 'active-badge' : 'inactive-badge'"
                  >
                    <i :class="p.is_active ? 'bi bi-check-circle-fill' : 'bi bi-x-octagon-fill'"></i>
                    {{ p.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>

                <td class="text-end">
                  <div class="btn-actions d-flex justify-content-end gap-2 flex-wrap">

                    <button class="action-btn neutral" @click="startEdit(p)">
                      <i class="bi bi-pencil-square"></i>
                      Edit
                    </button>

                    <button
                      v-if="p.is_active"
                      class="action-btn danger"
                      @click="openConfirmToggle(p)"
                    >
                      <i class="bi bi-person-x-fill"></i>
                      Deactivate
                    </button>

                    <button
                      v-else
                      class="action-btn success"
                      @click="openConfirmToggle(p)"
                    >
                      <i class="bi bi-person-check-fill"></i>
                      Activate
                    </button>

                  </div>
                </td>
              </tr>
            </tbody>

          </table>
        </div>
      </div>
    </div>

    <!-- =================== EDIT / CREATE FORM =================== -->
    <div
      v-if="showForm"
      ref="formSectionRef"
      class="card form-card shadow-sm border-0 mt-4"
    >
      <div class="card-body">

        <div class="form-header d-flex justify-content-between align-items-center mb-3">
          <div>
            <div class="d-flex align-items-center gap-2">
              <h5 class="fw-bold mb-0">
                <i class="bi" :class="editMode ? 'bi-pencil-square me-1' : 'bi-plus-circle me-1'"></i>
                {{ editMode ? 'Edit Patient' : 'Add Patient' }}
              </h5>
              <span v-if="editMode" class="edit-badge">
                ID #{{ form.id }}
              </span>
            </div>
            <p class="small text-muted mb-0 mt-1">
              {{ editMode ? 'Update patient details and confirm to save changes.' : 'Fill in details to register a new patient.' }}
            </p>
          </div>

          <button class="btn btn-sm btn-outline-secondary rounded-pill" @click="cancelForm">
            <i class="bi bi-x-lg"></i> Close
          </button>
        </div>

        <form @submit.prevent="onFormSubmit">
          <div class="row g-3">
            <div class="col-md-5">
              <label class="form-label small">Full Name</label>
              <input
                v-model="form.full_name"
                class="form-control form-control-sm"
                required
              />
            </div>

            <div class="col-md-3">
              <label class="form-label small">Username</label>
              <input
                v-model="form.username"
                class="form-control form-control-sm"
                :disabled="editMode"
                required
              />
            </div>

            <div class="col-md-4">
              <label class="form-label small">Email</label>
              <input
                v-model="form.email"
                type="email"
                class="form-control form-control-sm"
                required
              />
            </div>

            <div class="col-md-3">
              <label class="form-label small">Phone</label>
              <input
                v-model="form.phone"
                class="form-control form-control-sm"
                placeholder="+91..."
              />
            </div>

            <div class="col-md-2">
              <label class="form-label small">Age</label>
              <input
                v-model.number="form.age"
                type="number"
                min="0"
                class="form-control form-control-sm"
              />
            </div>

            <div class="col-md-3">
              <label class="form-label small">Gender</label>
              <select
                v-model="form.gender"
                class="form-select form-select-sm"
              >
                <option value="">Select...</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div v-if="!editMode" class="col-md-4">
              <label class="form-label small">Password</label>
              <input
                v-model="form.password"
                class="form-control form-control-sm"
                placeholder="default: patient123"
              />
            </div>
          </div>

          <div class="mt-3 d-flex gap-2 align-items-center">
            <button class="btn btn-primary btn-sm rounded-pill" type="submit" :disabled="saving">
              <span v-if="!saving">
                <i class="bi bi-check2-circle me-1"></i>
                {{ editMode ? 'Review & Save' : 'Create Patient' }}
              </span>
              <span v-else>
                <span class="spinner-border spinner-border-sm me-1"></span>
                Saving...
              </span>
            </button>

            <button
              class="btn btn-link btn-sm text-muted"
              type="button"
              @click="cancelForm"
              :disabled="saving"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- =================== CONFIRM POPUP: ACTIVATE / DEACTIVATE =================== -->
    <div v-if="showConfirmModal" class="confirm-overlay">
      <div class="confirm-box shadow-lg">
        <div class="d-flex gap-3">
          <div
            class="confirm-icon"
            :class="confirmAction === 'deactivate' ? 'danger-icon' : 'success-icon'"
          >
            <i :class="confirmAction === 'deactivate' ? 'bi bi-x-octagon-fill' : 'bi bi-check2'"></i>
          </div>

          <div>
            <h6 class="fw-bold mb-1">
              {{ confirmAction === 'deactivate' ? 'Deactivate Patient?' : 'Activate Patient?' }}
            </h6>
            <p class="small text-muted mb-0">
              Are you sure you want to
              <strong>{{ confirmAction }}</strong>
              patient
              <strong>{{ confirmPatient?.full_name }}</strong>?
            </p>
          </div>
        </div>

        <div class="d-flex justify-content-end gap-2 mt-3">
          <button
            class="btn btn-light btn-sm rounded-pill"
            type="button"
            @click="closeConfirmModal"
            :disabled="confirming"
          >
            Cancel
          </button>

          <button
            class="btn btn-sm rounded-pill"
            :class="confirmAction === 'deactivate' ? 'btn-danger' : 'btn-success'"
            type="button"
            @click="confirmToggle"
            :disabled="confirming"
          >
            <span v-if="!confirming">
              {{ confirmAction === 'deactivate' ? 'Deactivate' : 'Activate' }}
            </span>
            <span v-else>
              <span class="spinner-border spinner-border-sm me-1"></span>
              Processing...
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- =================== CONFIRM POPUP: SAVE EDIT =================== -->
    <div v-if="showFormConfirmModal" class="confirm-overlay">
      <div class="confirm-box shadow-lg">
        <div class="d-flex gap-3">
          <div class="confirm-icon info-icon">
            <i class="bi bi-pencil-square"></i>
          </div>

          <div>
            <h6 class="fw-bold mb-1">
              Save changes for {{ form.full_name || 'this patient' }}?
            </h6>
            <p class="small text-muted mb-0">
              You are about to update this patient's details. This will apply immediately.
            </p>
          </div>
        </div>

        <div class="d-flex justify-content-end gap-2 mt-3">
          <button
            class="btn btn-light btn-sm rounded-pill"
            type="button"
            @click="showFormConfirmModal = false"
            :disabled="saving"
          >
            Cancel
          </button>

          <button
            class="btn btn-primary btn-sm rounded-pill"
            type="button"
            @click="submitForm"
            :disabled="saving"
          >
            <span v-if="!saving">
              <i class="bi bi-check2-circle me-1"></i>Save Changes
            </span>
            <span v-else>
              <span class="spinner-border spinner-border-sm me-1"></span>
              Saving...
            </span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '../../api/axios'

const patients = ref([])
const search = ref('')
const loading = ref(false)
const errorMessage = ref('')

const filterStatus = ref('all') // all | active | inactive
const sortBy = ref('name')      // name | age

const showForm = ref(false)
const editMode = ref(false)
const saving = ref(false)

const showConfirmModal = ref(false)
const confirmPatient = ref(null)
const confirmAction = ref('') // activate | deactivate
const confirming = ref(false)

const showFormConfirmModal = ref(false)

const formSectionRef = ref(null)

const form = ref({
  id: null,
  full_name: '',
  username: '',
  email: '',
  phone: '',
  age: null,
  gender: '',
  password: '',
})

const scrollToForm = async () => {
  await nextTick()
  if (formSectionRef.value) {
    formSectionRef.value.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  }
}

const fetchPatients = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/admin/patients')
    patients.value = res.data || []
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to load patients.'
  } finally {
    loading.value = false
  }
}

const reload = () => {
  search.value = ''
  filterStatus.value = 'all'
  fetchPatients()
}

const filteredPatients = computed(() => {
  let list = patients.value

  // status filter
  if (filterStatus.value === 'active') {
    list = list.filter((p) => p.is_active)
  } else if (filterStatus.value === 'inactive') {
    list = list.filter((p) => !p.is_active)
  }

  // search across fields
  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase()
    list = list.filter((p) => {
      const statusText = p.is_active ? 'active' : 'inactive'
      return (
        String(p.id || '').toLowerCase().includes(q) ||
        (p.full_name || '').toLowerCase().includes(q) ||
        (p.username || '').toLowerCase().includes(q) ||
        (p.email || '').toLowerCase().includes(q) ||
        (p.phone || '').toLowerCase().includes(q) ||
        (p.gender || '').toLowerCase().includes(q) ||
        String(p.age || '').toLowerCase().includes(q) ||
        statusText.includes(q)
      )
    })
  }

  // sorting
  const copy = [...list]
  if (sortBy.value === 'name') {
    copy.sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''))
  } else if (sortBy.value === 'age') {
    copy.sort((a, b) => (b.age || 0) - (a.age || 0))
  }

  return copy
})

const setFilterStatus = (status) => {
  filterStatus.value = status
}

const startCreate = async () => {
  editMode.value = false
  showForm.value = true
  form.value = {
    id: null,
    full_name: '',
    username: '',
    email: '',
    phone: '',
    age: null,
    gender: '',
    password: '',
  }
  await scrollToForm()
}

const startEdit = async (p) => {
  editMode.value = true
  showForm.value = true
  form.value = {
    id: p.id,
    full_name: p.full_name,
    username: p.username,
    email: p.email,
    phone: p.phone,
    age: p.age,
    gender: p.gender,
    password: '',
  }
  await scrollToForm()
}

const cancelForm = () => {
  showForm.value = false
  showFormConfirmModal.value = false
}

const onFormSubmit = () => {
  if (editMode.value) {
    showFormConfirmModal.value = true
  } else {
    submitForm()
  }
}

const submitForm = async () => {
  saving.value = true
  errorMessage.value = ''
  try {
    if (editMode.value && form.value.id) {
      await api.put(`/admin/patients/${form.value.id}`, {
        full_name: form.value.full_name,
        email: form.value.email,
        phone: form.value.phone,
        age: form.value.age,
        gender: form.value.gender,
      })
    } else {
      await api.post('/admin/patients', {
        full_name: form.value.full_name,
        username: form.value.username,
        email: form.value.email,
        phone: form.value.phone,
        age: form.value.age,
        gender: form.value.gender,
        password: form.value.password || 'patient123',
      })
    }

    showForm.value = false
    showFormConfirmModal.value = false
    await fetchPatients()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || 'Failed to save patient.'
  } finally {
    saving.value = false
  }
}

const openConfirmToggle = (p) => {
  confirmPatient.value = p
  confirmAction.value = p.is_active ? 'deactivate' : 'activate'
  showConfirmModal.value = true
}

const closeConfirmModal = () => {
  showConfirmModal.value = false
  confirmPatient.value = null
  confirmAction.value = ''
}

const confirmToggle = async () => {
  if (!confirmPatient.value || !confirmAction.value) return
  confirming.value = true
  const p = confirmPatient.value
  const action = confirmAction.value

  try {
    if (action === 'deactivate') {
      await api.delete(`/admin/patients/${p.id}`)
    } else {
      await api.put(`/admin/patients/${p.id}`, { is_active: true })
    }
    await fetchPatients()
    closeConfirmModal()
  } catch (err) {
    errorMessage.value =
      err?.response?.data?.message || `Failed to ${action} patient.`
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  fetchPatients()
})
</script>

<style scoped>
.manage-patients {
  animation: fadeIn .35s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
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
  background: linear-gradient(135deg, #fee2f2, #e0f2fe);
  color: #ec4899;
  font-size: 1.4rem;
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

/* HEADER ACTIONS */
.header-actions .header-btn {
  font-weight: 500;
  transition: 0.2s ease;
}

.header-actions .header-btn.outline {
  border-color: #d0d5dd;
  background: #f9fafb;
}

.header-actions .header-btn.primary {
  background: linear-gradient(135deg, #ec4899, #8b5cf6);
  border: none;
  color: #fff;
  box-shadow: 0 4px 12px rgba(236,72,153,0.35);
}

.header-actions .header-btn:hover {
  transform: translateY(-1px);
  opacity: 0.95;
}

.count-pill {
  background: #fdf2ff;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  border: 1px solid rgba(236,72,153,0.18);
}

/* FILTER CARD */
.filter-card {
  border-radius: 18px;
}

/* Search */
.custom-search .input-group-text {
  background: #f8f9fb;
  border-radius: 999px 0 0 999px;
  border: 1px solid #e3e7ef;
}

.custom-search input {
  border-radius: 0 999px 999px 0;
  border: 1px solid #e3e7ef;
  font-size: 0.9rem;
}

/* STATUS BUTTON TOGGLE */
.status-toggle {
  display: inline-flex;
  padding: 3px;
  background: #f7f8fa;
  border-radius: 999px;
}

.status-btn {
  padding: 6px 16px;
  border-radius: 999px;
  border: none;
  background: transparent;
  font-size: 0.85rem;
  color: #6b7280;
  transition: .18s;
}

.status-btn.active {
  background: #ec4899;
  color: white;
  box-shadow: 0 2px 8px rgba(236,72,153,0.3);
}

/* SORT */
.sort-box {
  position: relative;
}

.sort-icon {
  position: absolute;
  left: 8px;
  top: 7px;
  color: #6c757d;
}

.sort-select {
  padding-left: 26px !important;
  font-size: 0.85rem;
}

/* PATIENTS TABLE */
.patients-card {
  border-radius: 18px;
  overflow: hidden;
}

.patients-table thead th {
  background: #f9fafb !important;
  font-size: .78rem;
  letter-spacing: 0.05em;
  padding: 12px 16px;
  font-weight: 600;
  text-transform: uppercase;
  color: #6b7280;
}

.patients-table tbody td {
  padding: 12px 16px !important;
  vertical-align: middle;
  font-size: 0.9rem;
}

.patients-table tbody tr:hover {
  background: #fdf2ff !important;
}

/* Username Chip */
.username-chip {
  background: #eef2ff;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  color: #374151;
}

/* Pills */
.pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
}

.pill-phone {
  background: #eff6ff;
  color: #1d4ed8;
}

.pill-gender {
  background: #e0f2fe;
  color: #0369a1;
}

.pill-age {
  background: #fef3c7;
  color: #92400e;
}

/* Status */
.status-badge {
  padding: 5px 12px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.75rem;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.active-badge {
  background: #e4f9ee;
  color: #15803d;
}

.inactive-badge {
  background: #fee2e2;
  color: #b91c1c;
}

/* Action Buttons */
.action-btn {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: .8rem;
  border: 1px solid #dee3eb;
  background: #f8f9fb;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: .2s;
}

.action-btn.neutral {
  border-color: #d0d5dd;
}

.action-btn.neutral:hover {
  background: #eef2ff;
}

.action-btn.danger {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff5f5;
}

.action-btn.danger:hover {
  background: #fee2e2;
}

.action-btn.success {
  border-color: #bbf7d0;
  color: #166534;
  background: #ecfdf3;
}

.action-btn.success:hover {
  background: #dcfce7;
}

/* FORM CARD */
.form-card {
  border-radius: 18px;
  border: 1px solid #f3e8ff;
}

.form-header {
  border-bottom: 1px solid #f1f3f9;
  padding-bottom: 10px;
  margin-bottom: 16px;
}

.edit-badge {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 999px;
  background: #f5f3ff;
  color: #7c3aed;
}

.form-label {
  font-weight: 600;
  color: #6b7280;
}

.form-control-sm,
.form-select-sm {
  font-size: .86rem;
  border-radius: 10px;
}

.form-control-sm:focus,
.form-select-sm:focus {
  border-color: #ec4899;
  box-shadow: 0 0 0 2px rgba(236,72,153,0.15);
}

/* CONFIRM MODALS */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.confirm-box {
  background: white;
  padding: 20px;
  width: 380px;
  border-radius: 16px;
}

.confirm-icon {
  width: 46px;
  height: 46px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}

.danger-icon {
  background: #fee2e2;
  color: #b91c1c;
}

.success-icon {
  background: #dcfce7;
  color: #15803d;
}

.info-icon {
  background: #e0f2fe;
  color: #0369a1;
}

/* No results & Loader */
.no-results {
  text-align: center;
  padding: 35px 0;
}

.loader-wrapper {
  padding: 30px 0;
  text-align: center;
}
</style>
