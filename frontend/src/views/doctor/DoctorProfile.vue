<template>
  <div class="doctor-profile container py-4">
    <!-- ========= PAGE HEADER ========= -->
    <div
      class="d-flex justify-content-between flex-wrap align-items-center mb-4 page-header"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-person-badge"></i>
        </div>
        <div>
          <h2 class="page-title mb-1">My Profile</h2>
          <p class="page-subtitle text-muted mb-0">
            View and update your doctor profile details.
          </p>
        </div>
      </div>

      <span v-if="!loading" class="small text-muted">
        Last updated: <strong>{{ lastUpdatedLabel }}</strong>
      </span>
    </div>

    <!-- ========= STATE MESSAGES ========= -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border"></div>
      <div class="mt-2">Loading profile...</div>
    </div>

    <div v-if="error" class="alert alert-danger">
      <i class="bi bi-exclamation-triangle-fill me-1"></i>
      {{ error }}
    </div>

    <div v-if="success" class="alert alert-success">
      <i class="bi bi-check-circle-fill me-1"></i>
      Profile updated successfully!
    </div>

    <!-- ========= PROFILE FORM ========= -->
    <div v-if="!loading" class="card border-0 shadow-soft">
      <div class="card-body p-4">
        <form @submit.prevent="saveProfile">
          <div class="row g-4">
            <!-- FULL NAME -->
            <div class="col-md-6">
              <label class="form-label fw-semibold">Full Name</label>
              <input
                type="text"
                class="form-control"
                v-model="form.full_name"
                required
              />
            </div>

            <!-- EMAIL (readonly) -->
            <div class="col-md-6">
              <label class="form-label fw-semibold">Email (login)</label>
              <input
                type="email"
                class="form-control"
                v-model="form.email"
                readonly
              />
            </div>

            <!-- SPECIALIZATION -->
            <div class="col-md-6">
              <label class="form-label fw-semibold">Specialization</label>
              <input
                type="text"
                class="form-control"
                v-model="form.specialization"
              />
            </div>

            <!-- EXPERIENCE -->
            <div class="col-md-6">
              <label class="form-label fw-semibold">Experience (years)</label>
              <input
                type="number"
                min="0"
                class="form-control"
                v-model="form.experience"
              />
            </div>

            <!-- BIO -->
            <div class="col-12">
              <label class="form-label fw-semibold">About / Bio</label>
              <textarea
                class="form-control"
                rows="3"
                v-model="form.bio"
                placeholder="Short professional bio..."
              ></textarea>
            </div>
          </div>

          <!-- Save Button -->
          <div class="text-end mt-4">
            <button
              class="btn btn-primary rounded-pill px-4"
              type="submit"
              :disabled="saving"
            >
              <span
                v-if="saving"
                class="spinner-border spinner-border-sm me-2"
              ></span>
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/api/axios";

export default {
  name: "DoctorProfile",

  data() {
    return {
      form: {
        full_name: "",
        email: "",
        specialization: "",
        experience: "",
        bio: "",
      },

      loading: true,
      saving: false,
      error: null,
      success: false,
      lastUpdated: null,
    };
  },

  computed: {
    lastUpdatedLabel() {
      if (!this.lastUpdated) return "Not yet";
      return this.lastUpdated.toLocaleString();
    },
  },

  created() {
    this.loadProfile();
  },

  methods: {
    // Load doctor profile
    async loadProfile() {
      this.loading = true;
      this.error = null;

      try {
        const res = await api.get("/doctor/profile"); // -> /api/doctor/profile
        const data = res.data || {};

        this.form.full_name = data.full_name || "";
        this.form.email = data.email || "";
        this.form.specialization = data.specialization || "";
        this.form.experience = data.experience ?? "";
        this.form.bio = data.bio || "";

        this.lastUpdated = new Date();
      } catch (err) {
        console.error("Failed to load doctor profile:", err);
        this.error =
          err.response?.data?.message || "Failed to load profile.";
      } finally {
        this.loading = false;
      }
    },

    // Save doctor profile
    async saveProfile() {
      this.saving = true;
      this.error = null;
      this.success = false;

      try {
        // axios baseURL is /api, so this calls /api/doctor/profile
        await api.put("/doctor/profile", {
          full_name: this.form.full_name,
          specialization: this.form.specialization,
          experience: this.form.experience,
          bio: this.form.bio,
        });

        this.success = true;
        this.lastUpdated = new Date();
      } catch (err) {
        console.error("Failed to update doctor profile:", err);
        this.error =
          err.response?.data?.message || "Failed to update profile.";
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>

<style scoped>
.page-icon {
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

.shadow-soft {
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.page-title {
  font-weight: 600;
}

.page-subtitle {
  font-size: 0.9rem;
}

.form-label {
  font-size: 0.9rem;
}

textarea {
  resize: none;
}
</style>
