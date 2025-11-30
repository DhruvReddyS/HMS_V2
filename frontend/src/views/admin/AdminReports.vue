<template>
  <div class="admin-reports container py-4">

    <!-- PAGE HEADER -->
    <div class="page-header d-flex justify-content-between flex-wrap mb-4">
      <div class="d-flex align-items-center gap-3 mb-2">
        <div class="page-icon">
          <i class="bi bi-file-earmark-bar-graph"></i>
        </div>
        <div>
          <h2 class="page-title mb-0">Hospital Reports</h2>
          <p class="page-subtitle mb-0 text-muted">
            Monthly analytics, hospital metrics & downloadable reports.
          </p>
        </div>
      </div>

      <div class="d-flex align-items-center gap-2">
        <input
          type="month"
          v-model="selectedMonth"
          class="form-control form-control-sm"
          style="width: 180px;"
          @change="loadStats"
        />
        <button
          class="btn btn-primary btn-sm rounded-pill"
          @click="downloadReport"
          :disabled="downloading"
        >
          <span v-if="downloading" class="spinner-border spinner-border-sm me-1"></span>
          Download Report (PDF)
        </button>
      </div>
    </div>

    <!-- ERROR BLOCK -->
    <div v-if="error" class="alert alert-danger d-flex align-items-center gap-2">
      <i class="bi bi-exclamation-circle"></i> {{ error }}
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border"></div>
      <div class="mt-2">Fetching reports...</div>
    </div>

    <div v-if="!loading">
      <!-- SUMMARY CARDS -->
      <div class="row g-4 mb-4">
        <div v-for="card in summaryCards" :key="card.label" class="col-md-3">
          <div class="card stat-card shadow-soft border-0 h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between mb-1">
                <span class="stat-label">{{ card.label }}</span>
                <i :class="card.icon"></i>
              </div>
              <div class="stat-number">{{ card.value }}</div>
              <div class="stat-subtext">{{ card.sub }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- CHARTS GRID 2x2 -->
      <div class="row g-4 mb-4">
        <!-- Line chart: daily appointments -->
        <div class="col-lg-6">
          <div class="card shadow-soft border-0 chart-card">
            <div class="card-body chart-card-body">
              <h5 class="mb-3">Daily Appointments Trend</h5>
              <div class="chart-wrapper">
                <canvas id="dailyChart"></canvas>
              </div>
            </div>
          </div>
        </div>

        <!-- Bar chart: specialization -->
        <div class="col-lg-6">
          <div class="card shadow-soft border-0 chart-card">
            <div class="card-body chart-card-body">
              <h5 class="mb-3">Appointments by Specialization</h5>
              <div class="chart-wrapper">
                <canvas id="specializationChart"></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <!-- Doughnut chart: status distribution -->
        <div class="col-lg-6">
          <div class="card shadow-soft border-0 chart-card">
            <div class="card-body chart-card-body">
              <h5 class="mb-3">Status Distribution</h5>
              <div class="chart-wrapper">
                <canvas id="statusChart"></canvas>
              </div>
            </div>
          </div>
        </div>

        <!-- Horizontal bar: top doctors -->
        <div class="col-lg-6">
          <div class="card shadow-soft border-0 chart-card">
            <div class="card-body chart-card-body">
              <h5 class="mb-3">Top Performing Doctors</h5>
              <div class="chart-wrapper">
                <canvas id="topDoctorsChart"></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RAW TABLES -->
      <div class="card shadow-soft border-0 mb-4">
        <div class="card-body">
          <h5 class="mb-3">Appointment Statistics (Table)</h5>

          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>Status</th>
                <th class="text-end">Count</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Booked</td>
                <td class="text-end">{{ stats.booked }}</td>
              </tr>
              <tr>
                <td>Completed</td>
                <td class="text-end">{{ stats.completed }}</td>
              </tr>
              <tr>
                <td>Cancelled</td>
                <td class="text-end">{{ stats.cancelled }}</td>
              </tr>
              <tr class="fw-bold table-light">
                <td>Total</td>
                <td class="text-end">{{ totalAppointments }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card shadow-soft border-0">
        <div class="card-body">
          <h5 class="mb-3">Top Performing Doctors (Table)</h5>

          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>Doctor Name</th>
                <th>Specialization</th>
                <th class="text-end">Completed Appointments</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in stats.top_doctors" :key="doc.doctor_id || doc.id">
                <td>{{ doc.name }}</td>
                <td>{{ doc.specialization }}</td>
                <td class="text-end">{{ doc.completed }}</td>
              </tr>
              <tr v-if="stats.top_doctors.length === 0">
                <td colspan="3" class="text-center text-muted py-3">No data found</td>
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
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

export default {
  name: "AdminReports",

  data() {
    return {
      loading: true,
      downloading: false,
      error: null,
      selectedMonth: "",
      // Core stats
      stats: {
        booked: 0,
        completed: 0,
        cancelled: 0,
        top_doctors: []
      },
      // Extra analytics from backend
      analytics: {
        daily_appointments: [],
        specialization_counts: []
      },
      // Chart instances
      dailyChartInstance: null,
      specializationChartInstance: null,
      statusChartInstance: null,
      topDoctorsChartInstance: null
    };
  },

  computed: {
    totalAppointments() {
      return this.stats.booked + this.stats.completed + this.stats.cancelled;
    },

    summaryCards() {
      return [
        {
          label: "Booked",
          value: this.stats.booked,
          sub: "Appointments this month",
          icon: "bi bi-calendar-event text-primary"
        },
        {
          label: "Completed",
          value: this.stats.completed,
          sub: "Successful visits",
          icon: "bi bi-check-circle text-success"
        },
        {
          label: "Cancelled",
          value: this.stats.cancelled,
          sub: "Cancelled visits",
          icon: "bi bi-x-circle text-danger"
        },
        {
          label: "Total",
          value: this.totalAppointments,
          sub: "Overall appointments",
          icon: "bi bi-bar-chart-line text-info"
        }
      ];
    }
  },

  created() {
    const now = new Date();
    this.selectedMonth = `${now.getFullYear()}-${String(
      now.getMonth() + 1
    ).padStart(2, "0")}`;
    this.loadStats();
  },

  methods: {
    async loadStats() {
      this.loading = true;
      this.error = null;

      try {
        const res = await api.get("/admin/reports-analytics", {
          params: { month: this.selectedMonth }
        });

        const data = res.data || {};

        // === Map status_counts (BOOKED / COMPLETED / CANCELLED) ===
        const sc = data.status_counts || {};
        this.stats.booked = sc.BOOKED || 0;
        this.stats.completed = sc.COMPLETED || 0;
        this.stats.cancelled = sc.CANCELLED || 0;

        // === Top doctors: backend key = doctor_productivity ===
        this.stats.top_doctors = data.doctor_productivity || [];

        // === Analytics arrays ===
        this.analytics.daily_appointments = data.daily_appointments || [];
        this.analytics.specialization_counts = data.specialization_counts || [];
      } catch (err) {
        this.error =
          err.response?.data?.message || "Failed to load report data.";
      } finally {
        this.loading = false;

        // Canvases exist now (v-if="!loading"), so render charts here
        this.$nextTick(() => {
          this.renderAllCharts();
        });
      }
    },

    destroyCharts() {
      if (this.dailyChartInstance) {
        this.dailyChartInstance.destroy();
        this.dailyChartInstance = null;
      }
      if (this.specializationChartInstance) {
        this.specializationChartInstance.destroy();
        this.specializationChartInstance = null;
      }
      if (this.statusChartInstance) {
        this.statusChartInstance.destroy();
        this.statusChartInstance = null;
      }
      if (this.topDoctorsChartInstance) {
        this.topDoctorsChartInstance.destroy();
        this.topDoctorsChartInstance = null;
      }
    },

    renderAllCharts() {
      this.destroyCharts();
      this.renderDailyChart();
      this.renderSpecializationChart();
      this.renderStatusChart();
      this.renderTopDoctorsChart();
    },

    renderDailyChart() {
      const canvas = document.getElementById("dailyChart");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      const labels = this.analytics.daily_appointments.map((d) =>
        d.date.slice(-2)
      );
      const booked = this.analytics.daily_appointments.map((d) => d.booked);
      const completed = this.analytics.daily_appointments.map(
        (d) => d.completed
      );
      const cancelled = this.analytics.daily_appointments.map(
        (d) => d.cancelled
      );

      this.dailyChartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Booked",
              data: booked,
              tension: 0.3,
              borderWidth: 2
            },
            {
              label: "Completed",
              data: completed,
              tension: 0.3,
              borderWidth: 2
            },
            {
              label: "Cancelled",
              data: cancelled,
              tension: 0.3,
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 }
            }
          }
        }
      });
    },

    renderSpecializationChart() {
      const canvas = document.getElementById("specializationChart");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      const labels = this.analytics.specialization_counts.map(
        (s) => s.specialization
      );
      const values = this.analytics.specialization_counts.map(
        (s) => s.appointments
      );

      this.specializationChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "Appointments",
              data: values,
              borderWidth: 1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 }
            }
          }
        }
      });
    },

    renderStatusChart() {
      const canvas = document.getElementById("statusChart");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      const labels = ["Booked", "Completed", "Cancelled"];
      const values = [
        this.stats.booked,
        this.stats.completed,
        this.stats.cancelled
      ];

      this.statusChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: values,
              borderWidth: 1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      });
    },

    renderTopDoctorsChart() {
      const canvas = document.getElementById("topDoctorsChart");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");

      const labels = this.stats.top_doctors.map((d) => d.name);
      const values = this.stats.top_doctors.map((d) => d.completed);

      this.topDoctorsChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "Completed Appointments",
              data: values,
              borderWidth: 1
            }
          ]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              beginAtZero: true,
              ticks: { precision: 0 }
            }
          }
        }
      });
    },

    async downloadReport() {
      this.downloading = true;
      this.error = null;

      try {
        const res = await api.get("/admin/monthly-report", {
          params: { month: this.selectedMonth },
          responseType: "blob"
        });

        const blob = new Blob([res.data], { type: "application/pdf" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");

        a.href = url;
        a.download = `hospital_report_${this.selectedMonth}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        this.error =
          err.response?.data?.message || "Failed to download the report.";
      }

      this.downloading = false;
    }
  },

  beforeUnmount() {
    this.destroyCharts();
  }
};
</script>

<style scoped>
.page-icon {
  width: 45px;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e7f1ff;
  border-radius: 12px;
  font-size: 1.4rem;
}

.stat-card {
  border-radius: 1rem;
  padding: 1rem;
  background: #f8fbff;
  transition: 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}

.stat-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  color: #6c757d;
}

.stat-number {
  font-size: 1.9rem;
  font-weight: 700;
}

.stat-subtext {
  font-size: 0.8rem;
  color: #6c757d;
}

/* ------- CHART LAYOUT (2x2, no full-screen stretch) ------- */

.chart-card {
  height: 340px;              /* fixed height for all chart cards */
  display: flex;
  flex-direction: column;
}

.chart-card-body {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem 1.25rem 1.25rem 1.25rem;
}

.chart-card-body h5 {
  flex: 0 0 auto;
}

.chart-wrapper {
  flex: 1 1 auto;
  position: relative;
}

/* canvas fits inside wrapper, no crazy stretching */
.chart-wrapper canvas {
  width: 100% !important;
  height: 100% !important;
}

/* override old min-height if any */
.card canvas {
  min-height: unset !important;
}
</style>
