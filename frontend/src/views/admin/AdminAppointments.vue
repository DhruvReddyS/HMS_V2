<template>
  <div class="admin-appointments container py-4">
    <!-- ========= HEADER ========= -->
    <div class="card border-0 shadow-soft mb-3 header-card">
      <div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-2">
          <div class="page-icon-sm">
            <i class="bi bi-calendar2-week"></i>
          </div>
          <div>
            <h4 class="mb-1">All Appointments</h4>
            <p class="small text-muted mb-0">
              View, filter and manage all hospital appointments.
            </p>
          </div>
        </div>

        <div class="text-end small text-muted">
          <div class="mb-1">
            <span class="pill-badge">
              <span class="pill-dot"></span>
              Admin view • All appointments
            </span>
          </div>
          <div>
            Last refreshed:
            <strong>{{ lastRefreshedLabel }}</strong>
          </div>
        </div>
      </div>
    </div>

    <!-- ========= FILTER BAR ========= -->
    <div class="card shadow-soft border-0 mb-3">
      <div class="card-body d-flex flex-wrap gap-2 align-items-end filters-bar">
        <div class="filter-item">
          <label class="form-label form-label-sm mb-1">Status</label>
          <select
            v-model="filters.status"
            class="form-select form-select-sm"
            @change="loadAppointments"
          >
            <option value="">All statuses</option>
            <option value="BOOKED">Booked</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        <div class="filter-item">
          <label class="form-label form-label-sm mb-1">Doctor</label>
          <select
            v-model.number="filters.doctor_id"
            class="form-select form-select-sm"
            @change="loadAppointments"
          >
            <option :value="null">All doctors</option>
            <option v-for="doc in doctors" :key="doc.id" :value="doc.id">
              {{ doc.full_name }} ({{ doc.specialization || 'General' }})
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label class="form-label form-label-sm mb-1">Patient</label>
          <select
            v-model.number="filters.patient_id"
            class="form-select form-select-sm"
            @change="loadAppointments"
          >
            <option :value="null">All patients</option>
            <option v-for="pat in patients" :key="pat.id" :value="pat.id">
              {{ pat.full_name || ('Patient #' + pat.id) }}
            </option>
          </select>
        </div>

        <div class="ms-auto d-flex gap-2">
          <button
            class="btn btn-outline-secondary btn-sm rounded-pill"
            type="button"
            @click="resetFilters"
          >
            <i class="bi bi-slash-circle me-1"></i>
            Clear filters
          </button>
          <button
            class="btn btn-light btn-sm rounded-pill"
            type="button"
            @click="loadAppointments"
          >
            <i class="bi bi-arrow-clockwise me-1"></i>
            Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- ========= ERROR ========= -->
    <div v-if="error" class="alert alert-danger d-flex align-items-center gap-2">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>

    <!-- ========= LOADING ========= -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border"></div>
      <div class="mt-2">Loading appointments...</div>
    </div>

    <!-- ========= TABLE ========= -->
    <div v-if="!loading" class="card shadow-soft border-0">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Date &amp; Time</th>
                <th>Doctor</th>
                <th>Patient</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="appt in appointments" :key="appt.id">
                <td class="fw-semibold">#{{ appt.id }}</td>
                <td>
                  <div class="small fw-semibold">
                    {{ appt.date || '—' }} • {{ appt.time || '—' }}
                  </div>
                  <div class="small text-muted">
                    Created: {{ formatDateTime(appt.created_at) }}
                  </div>
                </td>
                <td>
                  <div class="small fw-semibold">
                    {{ doctorName(appt.doctor_id) }}
                  </div>
                  <div class="small text-muted">
                    {{ doctorSpec(appt.doctor_id) }}
                  </div>
                </td>
                <td>
                  <div class="small fw-semibold">
                    {{ patientName(appt.patient_id) }}
                  </div>
                  <div class="small text-muted">
                    Patient #{{ appt.patient_id }}
                  </div>
                </td>
                <td>
                  <span :class="statusBadgeClass(appt.status)">
                    {{ prettyStatus(appt.status) }}
                  </span>
                </td>
                <td class="text-end">
                  <button
                    class="btn btn-outline-primary btn-sm rounded-pill"
                    @click="goToDetails(appt.id)"
                  >
                    <i class="bi bi-eye me-1"></i>
                    View
                  </button>
                </td>
              </tr>

              <tr v-if="appointments.length === 0">
                <td colspan="6" class="text-center text-muted py-4">
                  No appointments found for the selected filters.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from "@/api/axios";

export default {
  name: "AdminAppointments",

  data() {
    return {
      loading: true,
      error: null,
      lastRefreshed: null,
      appointments: [],
      doctors: [],
      patients: [],
      filters: {
        status: "",
        doctor_id: null,
        patient_id: null
      }
    };
  },

  computed: {
    lastRefreshedLabel() {
      if (!this.lastRefreshed) return "—";
      return this.lastRefreshed.toLocaleString();
    }
  },

  created() {
    this.initPage();
  },

  methods: {
    async initPage() {
      this.loading = true;
      this.error = null;
      try {
        await Promise.all([this.loadDoctors(), this.loadPatients()]);
        await this.loadAppointments();
      } catch (err) {
        this.error =
          err.response?.data?.message || "Failed to load appointments.";
      } finally {
        this.loading = false;
      }
    },

    async loadDoctors() {
      try {
        const res = await api.get("/admin/doctors", {
          params: { active_only: true }
        });
        this.doctors = res.data || [];
      } catch (err) {
        console.error("Failed to load doctors", err);
      }
    },

    async loadPatients() {
      try {
        const res = await api.get("/admin/patients");
      this.patients = res.data || [];
      } catch (err) {
        console.error("Failed to load patients", err);
      }
    },

    async loadAppointments() {
      this.loading = true;
      this.error = null;

      const params = {};
      if (this.filters.status) params.status = this.filters.status;
      if (this.filters.doctor_id) params.doctor_id = this.filters.doctor_id;
      if (this.filters.patient_id) params.patient_id = this.filters.patient_id;

      try {
        const res = await api.get("/admin/appointments", { params });
        this.appointments = res.data || [];
        this.lastRefreshed = new Date();
      } catch (err) {
        this.error =
          err.response?.data?.message || "Failed to load appointments.";
      } finally {
        this.loading = false;
      }
    },

    resetFilters() {
      this.filters.status = "";
      this.filters.doctor_id = null;
      this.filters.patient_id = null;
      this.loadAppointments();
    },

    doctorName(id) {
      const d = this.doctors.find((x) => x.id === id);
      return d ? d.full_name : `Doctor #${id}`;
    },

    doctorSpec(id) {
      const d = this.doctors.find((x) => x.id === id);
      return d && d.specialization ? d.specialization : "Specialization N/A";
    },

    patientName(id) {
      const p = this.patients.find((x) => x.id === id);
      return p ? p.full_name : `Patient #${id}`;
    },

    prettyStatus(status) {
      const s = (status || "").toUpperCase();
      if (s === "BOOKED") return "Booked";
      if (s === "COMPLETED") return "Completed";
      if (s === "CANCELLED") return "Cancelled";
      return status || "Unknown";
    },

    statusBadgeClass(status) {
      const s = (status || "").toUpperCase();
      if (s === "BOOKED")
        return "badge rounded-pill bg-info-subtle text-info";
      if (s === "COMPLETED")
        return "badge rounded-pill bg-success-subtle text-success";
      if (s === "CANCELLED")
        return "badge rounded-pill bg-danger-subtle text-danger";
      return "badge rounded-pill bg-secondary-subtle text-secondary";
    },

    formatDateTime(iso) {
      if (!iso) return "—";
      try {
        const d = new Date(iso);
        return d.toLocaleString();
      } catch {
        return iso;
      }
    },

    goToDetails(id) {
      this.$router.push({
        name: "AdminAppointmentDetails",
        params: { id }
      });
    }
  }
};
</script>

<style scoped>
.header-card {
  border-radius: 1rem;
}

.page-icon-sm {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e7f1ff;
  font-size: 1.2rem;
}

.pill-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  background-color: #f1f5ff;
  color: #3956d0;
}

.pill-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background-color: #28a745;
}

.filters-bar .filter-item {
  min-width: 180px;
}

.form-label-sm {
  font-size: 0.78rem;
  color: #6c757d;
  font-weight: 500;
}

.shadow-soft {
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}
</style>
