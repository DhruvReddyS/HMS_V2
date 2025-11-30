<template>
  <div class="doctor-my-patients container py-4">
    <!-- ============ PAGE HEADER ============ -->
    <div
      class="d-flex justify-content-between flex-wrap align-items-center mb-4 page-header"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-person-heart"></i>
        </div>
        <div>
          <h2 class="page-title mb-1">My Patients</h2>
          <p class="page-subtitle mb-0 text-muted">
            View all patients who have booked appointments with you.
          </p>
        </div>
      </div>

      <div class="header-actions d-flex flex-wrap gap-2 align-items-center">
        <span class="count-pill">
          <i class="bi bi-people-fill me-1"></i>
          {{ filteredPatients.length }} patients
        </span>

        <button
          class="btn btn-outline-secondary btn-sm rounded-pill"
          type="button"
          @click="reload"
          :disabled="loading"
        >
          <i
            class="bi bi-arrow-clockwise me-1"
            :class="{ 'spin-icon': loading }"
          ></i>
          Refresh
        </button>
      </div>
    </div>

    <!-- ============ FILTER BAR ============ -->
    <div class="card border-0 shadow-soft mb-3">
      <div class="card-body py-3">
        <div class="row g-3 align-items-center">
          <div class="col-md-6">
            <label class="form-label small text-muted mb-1">
              Search patients
            </label>
            <div class="input-group input-group-sm">
              <span class="input-group-text bg-light border-0">
                <i class="bi bi-search"></i>
              </span>
              <input
                v-model="searchTerm"
                type="text"
                class="form-control border-0"
                placeholder="Search by name, email or phone..."
              />
            </div>
          </div>

          <div class="col-md-3">
            <label class="form-label small text-muted mb-1">
              Sort by
            </label>
            <select
              v-model="sortBy"
              class="form-select form-select-sm border-0 bg-light"
            >
              <option value="name">Name (A–Z)</option>
              <option value="recent">Most recent visit</option>
              <option value="appointments">Most appointments</option>
            </select>
          </div>

          <div class="col-md-3">
            <label class="form-label small text-muted mb-1">
              Gender
            </label>
            <select
              v-model="genderFilter"
              class="form-select form-select-sm border-0 bg-light"
            >
              <option value="">All</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ STATE MESSAGES ============ -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm mb-2" role="status"></div>
      <div>Loading patients...</div>
    </div>

    <div
      v-else-if="error"
      class="alert alert-danger d-flex align-items-start gap-2"
    >
      <i class="bi bi-exclamation-triangle-fill mt-1"></i>
      <div>
        <strong>Failed to load patients.</strong>
        <div class="small">{{ error }}</div>
      </div>
    </div>

    <div
      v-else-if="!filteredPatients.length"
      class="card border-0 shadow-soft empty-card"
    >
      <div class="card-body text-center py-5 text-muted">
        <div class="mb-2">
          <i class="bi bi-people-slash fs-2"></i>
        </div>
        <h5 class="mb-1">No patients found</h5>
        <p class="small mb-0">
          Once patients start booking appointments with you, they will appear
          here.
        </p>
      </div>
    </div>

    <!-- ============ PATIENTS TABLE ============ -->
    <div v-else class="card border-0 shadow-soft">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th scope="col">Patient</th>
                <th scope="col" class="d-none d-md-table-cell">Age / Gender</th>
                <th scope="col">Contact</th>
                <th scope="col" class="d-none d-md-table-cell">Last visit</th>
                <th scope="col" class="d-none d-md-table-cell text-center">
                  Appointments
                </th>
                <th scope="col" class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="patient in filteredPatients" :key="patient.id">
                <td>
                  <div class="d-flex align-items-center gap-2">
                    <div class="avatar-circle">
                      <span>
                        {{
                          (patient.full_name || "P")
                            .trim()
                            .charAt(0)
                            .toUpperCase()
                        }}
                      </span>
                    </div>
                    <div>
                      <div class="fw-semibold">
                        {{ patient.full_name || "Unnamed patient" }}
                      </div>
                      <div class="small text-muted d-md-none">
                        {{ patient.age || "N/A" }} yrs
                        <span v-if="patient.gender"> • {{ patient.gender }}</span>
                      </div>
                    </div>
                  </div>
                </td>

                <td class="d-none d-md-table-cell">
                  <div class="small">
                    <strong>{{ patient.age || "N/A" }}</strong> yrs
                  </div>
                  <div class="small text-muted">
                    {{ patient.gender || "Not specified" }}
                  </div>
                </td>

                <td>
                  <div class="small">
                    <i class="bi bi-envelope me-1"></i>
                    <span>{{ patient.email || "No email" }}</span>
                  </div>
                  <div class="small text-muted">
                    <i class="bi bi-telephone me-1"></i>
                    <span>{{ patient.phone || "No phone" }}</span>
                  </div>
                </td>

                <td class="d-none d-md-table-cell">
                  <div class="small">
                    {{ formatDate(patient.last_visit) }}
                  </div>
                  <div class="small text-muted">
                    {{
                      patient.last_visit
                        ? "Last consultation"
                        : "No visits recorded"
                    }}
                  </div>
                </td>

                <td class="d-none d-md-table-cell text-center">
                  <span class="badge rounded-pill bg-light text-dark">
                    <i class="bi bi-calendar2-week me-1"></i>
                    {{ patient.total_appointments || 0 }}
                  </span>
                </td>

                <td class="text-end">
                  <!-- ✅ Only one History button -->
                  <button
                    class="btn btn-outline-primary btn-sm"
                    type="button"
                    @click="viewHistory(patient)"
                  >
                    <i class="bi bi-clock-history me-1"></i>
                    History
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          class="card-footer small text-muted d-flex justify-content-between flex-wrap gap-2"
        >
          <span>
            Showing {{ filteredPatients.length }} of
            {{ patients.length }} patients
          </span>
          <span>Updated: {{ lastRefreshedLabel }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/api/axios";

export default {
  name: "DoctorMyPatients",

  data() {
    return {
      patients: [],
      loading: false,
      error: null,

      searchTerm: "",
      sortBy: "name", // name | recent | appointments
      genderFilter: "",

      lastRefreshed: null,
    };
  },

  computed: {
    filteredPatients() {
      let list = [...this.patients];

      // search filter
      const term = this.searchTerm.trim().toLowerCase();
      if (term) {
        list = list.filter((p) => {
          const name = (p.full_name || "").toLowerCase();
          const email = (p.email || "").toLowerCase();
          const phone = (p.phone || "").toLowerCase();
          return (
            name.includes(term) || email.includes(term) || phone.includes(term)
          );
        });
      }

      // gender filter
      if (this.genderFilter) {
        list = list.filter((p) => p.gender === this.genderFilter);
      }

      // sorting
      if (this.sortBy === "name") {
        list.sort((a, b) =>
          (a.full_name || "").localeCompare(b.full_name || "")
        );
      } else if (this.sortBy === "recent") {
        list.sort((a, b) => {
          const da = a.last_visit ? new Date(a.last_visit) : new Date(0);
          const db = b.last_visit ? new Date(b.last_visit) : new Date(0);
          return db - da; // newest first
        });
      } else if (this.sortBy === "appointments") {
        list.sort(
          (a, b) =>
            (b.total_appointments || 0) - (a.total_appointments || 0)
        );
      }

      return list;
    },

    lastRefreshedLabel() {
      if (!this.lastRefreshed) return "Not yet";
      return this.lastRefreshed.toLocaleString();
    },
  },

  created() {
    this.loadPatients();
  },

  methods: {
    async loadPatients() {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get("/doctor/my-patients");
        // backend returns: { patients: [...] }
        this.patients = response.data?.patients || [];
        this.lastRefreshed = new Date();
      } catch (err) {
        console.error("Failed to load doctor patients:", err);
        this.error =
          err.response?.data?.message ||
          err.message ||
          "Something went wrong while fetching patients.";
      } finally {
        this.loading = false;
      }
    },

    reload() {
      this.loadPatients();
    },

    formatDate(value) {
      if (!value) return "No visits";
      const d = new Date(value);
      if (isNaN(d.getTime())) return value;
      return d.toLocaleDateString();
    },

    viewHistory(patient) {
      // ✅ This will generate /doctor/patient-history?patientId=<id>
      this.$router.push({
        name: "DoctorPatientHistory",
        query: { patientId: patient.id },
      });
    },
  },
};
</script>

<style scoped>
.page-header .page-icon {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--bs-primary-bg-subtle, #e7f1ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  color: var(--bs-primary, #0d6efd);
}

.page-title {
  font-weight: 600;
}

.page-subtitle {
  font-size: 0.9rem;
}

.count-pill {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  background: #f5f5f5;
  font-size: 0.8rem;
}

.shadow-soft {
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e9ecef;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
  color: #495057;
}

.spin-icon {
  animation: spin 0.7s linear infinite;
}

.empty-card {
  border-radius: 1rem;
}

.table > :not(caption) > * > * {
  padding: 0.9rem 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
