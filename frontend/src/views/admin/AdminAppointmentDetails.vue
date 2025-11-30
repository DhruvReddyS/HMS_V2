<template>
  <div class="admin-appointment-details container py-4">
    <!-- HEADER -->
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <div class="d-flex align-items-center gap-2">
        <button
          class="btn btn-light btn-sm rounded-pill"
          type="button"
          @click="goBack"
        >
          <i class="bi bi-arrow-left-short"></i>
          Back to appointments
        </button>
        <h4 class="mb-0">
          Appointment #{{ id }}
        </h4>
      </div>

      <div class="small text-muted">
        Last updated:
        <strong>{{ lastUpdatedLabel }}</strong>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="error" class="alert alert-danger d-flex align-items-center gap-2">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border"></div>
      <div class="mt-2">Loading appointment details...</div>
    </div>

    <!-- CONTENT -->
    <div v-if="!loading && appointment" class="row g-3">
      <!-- APPOINTMENT INFO -->
      <div class="col-12">
        <div class="card shadow-soft border-0">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <div>
                <h5 class="mb-1">Appointment Information</h5>
                <p class="small text-muted mb-0">
                  Detailed information about this appointment.
                </p>
              </div>
              <div>
                <span :class="statusBadgeClass(appointment.status)">
                  {{ prettyStatus(appointment.status) }}
                </span>
              </div>
            </div>

            <div class="row">
              <div class="col-md-4 mb-2">
                <div class="text-muted small">Date</div>
                <div class="fw-semibold">{{ appointment.date || '—' }}</div>
              </div>
              <div class="col-md-4 mb-2">
                <div class="text-muted small">Time</div>
                <div class="fw-semibold">{{ appointment.time || '—' }}</div>
              </div>
              <div class="col-md-4 mb-2">
                <div class="text-muted small">Created At</div>
                <div class="fw-semibold">{{ formatDateTime(appointment.created_at) }}</div>
              </div>
            </div>

            <div class="mt-3">
              <div class="text-muted small">Appointment ID</div>
              <div class="fw-semibold">#{{ appointment.id }}</div>
            </div>

            <!-- STATUS ACTIONS -->
            <div class="mt-3">
              <div class="text-muted small mb-1">Update Status</div>
              <div class="btn-group btn-group-sm">
                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  :disabled="appointment.status === 'BOOKED' || updating"
                  @click="changeStatus('BOOKED')"
                >
                  Booked
                </button>
                <button
                  type="button"
                  class="btn btn-outline-success"
                  :disabled="appointment.status === 'COMPLETED' || updating"
                  @click="changeStatus('COMPLETED')"
                >
                  Completed
                </button>
                <button
                  type="button"
                  class="btn btn-outline-danger"
                  :disabled="appointment.status === 'CANCELLED' || updating"
                  @click="changeStatus('CANCELLED')"
                >
                  Cancelled
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- DOCTOR & PATIENT CARDS -->
      <div class="col-md-6">
        <div class="card shadow-soft border-0 h-100">
          <div class="card-body">
            <h5 class="mb-2">Doctor</h5>
            <div v-if="doctor">
              <div class="fw-semibold">{{ doctor.full_name }}</div>
              <div class="small text-muted">
                {{ doctor.specialization || 'Specialization N/A' }}
              </div>
              <div class="small mt-2">
                <span class="text-muted">Experience: </span>
                {{ doctor.experience_years || 0 }} years
              </div>
              <div class="small">
                <span class="text-muted">Username: </span>
                {{ doctor.username }}
              </div>
              <div class="small">
                <span class="text-muted">Email: </span>
                {{ doctor.email }}
              </div>
            </div>
            <div v-else class="text-muted small">
              Doctor information not available.
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card shadow-soft border-0 h-100">
          <div class="card-body">
            <h5 class="mb-2">Patient</h5>
            <div v-if="patient">
              <div class="fw-semibold">{{ patient.full_name }}</div>
              <div class="small text-muted">
                {{ patient.gender || 'Gender N/A' }},
                Age: {{ patient.age ?? 'N/A' }}
              </div>
              <div class="small mt-2">
                <span class="text-muted">Phone: </span>
                {{ patient.phone || 'N/A' }}
              </div>
              <div class="small">
                <span class="text-muted">Email: </span>
                {{ patient.email }}
              </div>
              <div class="small">
                <span class="text-muted">Address: </span>
                {{ patient.address || 'N/A' }}
              </div>
            </div>
            <div v-else class="text-muted small">
              Patient information not available.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- If not found -->
    <div v-if="!loading && !appointment && !error" class="alert alert-warning mt-3">
      Appointment not found.
    </div>
  </div>
</template>

<script>
import api from "@/api/axios";

export default {
  name: "AdminAppointmentDetails",
  props: {
    id: {
      type: [String, Number],
      required: true
    }
  },

  data() {
    return {
      loading: true,
      error: null,
      appointment: null,
      doctor: null,
      patient: null,
      updating: false,
      lastUpdated: null
    };
  },

  computed: {
    lastUpdatedLabel() {
      if (!this.lastUpdated) return "—";
      return this.lastUpdated.toLocaleString();
    }
  },

  created() {
    this.loadDetails();
  },

  methods: {
    async loadDetails() {
      this.loading = true;
      this.error = null;

      try {
        // 1) Get the appointment by id (using /admin/appointments?id=)
        const resAppt = await api.get("/admin/appointments", {
          params: { id: this.id }
        });
        const list = resAppt.data || [];
        this.appointment = list[0] || null;

        if (!this.appointment) {
          this.loading = false;
          return;
        }

        const { doctor_id, patient_id } = this.appointment;

        // 2) Fetch doctor and patient details in parallel
        const [resDoc, resPat] = await Promise.all([
          api.get(`/admin/doctors/${doctor_id}`),
          api.get(`/admin/patients/${patient_id}`)
        ]);

        this.doctor = resDoc.data || null;
        this.patient = resPat.data || null;
        this.lastUpdated = new Date();
      } catch (err) {
        this.error =
          err.response?.data?.message || "Failed to load appointment details.";
      } finally {
        this.loading = false;
      }
    },

    goBack() {
      this.$router.push({ name: "AdminAppointments" });
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

    async changeStatus(newStatus) {
      if (!this.appointment || this.appointment.status === newStatus) return;

      const pretty = this.prettyStatus(newStatus);
      const ok = window.confirm(
        `Change status of appointment #${this.appointment.id} to "${pretty}"?`
      );
      if (!ok) return;

      this.updating = true;
      this.error = null;

      try {
        await api.patch(`/admin/appointments/${this.appointment.id}/status`, {
          status: newStatus
        });
        this.appointment.status = newStatus;
        this.lastUpdated = new Date();
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to update appointment status.";
      } finally {
        this.updating = false;
      }
    }
  }
};
</script>

<style scoped>
.shadow-soft {
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}
</style>
