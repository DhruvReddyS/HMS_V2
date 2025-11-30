<template>
  <div class="doctor-stats container py-4">
    <!-- ================= PAGE HEADER ================= -->
    <div
      class="d-flex justify-content-between flex-wrap align-items-center mb-4 page-header"
    >
      <div class="d-flex align-items-center gap-3 mb-2 mb-md-0">
        <div class="page-icon">
          <i class="bi bi-bar-chart-line"></i>
        </div>
        <div>
          <h2 class="page-title mb-1">Statistics &amp; Reports</h2>
          <p class="page-subtitle text-muted mb-0">
            View insights, performance metrics and download monthly reports.
          </p>
        </div>
      </div>

      <div class="small text-muted">
        Last updated: <strong>{{ lastUpdatedLabel }}</strong>
      </div>
    </div>

    <!-- ================= STATE MESSAGES ================= -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border"></div>
      <div class="mt-2">Loading statistics...</div>
    </div>

    <div
      v-if="error"
      class="alert alert-danger d-flex gap-2 align-items-center"
    >
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>

    <!-- ================= STAT CARDS ================= -->
    <div v-if="!loading" class="row g-4 mb-4">
      <div class="col-md-3" v-for="card in statCards" :key="card.label">
        <div class="card stat-card shadow-soft border-0" :class="card.class">
          <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="stat-label">{{ card.label }}</span>
              <span class="stat-icon">
                <i :class="card.icon"></i>
              </span>
            </div>
            <div class="stat-number">{{ card.value }}</div>
            <div v-if="card.sub" class="stat-subtext">
              {{ card.sub }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= CHARTS: 2 x 2 GRID ================= -->
    <div class="row g-4" v-if="!loading">
      <!-- 1. LINE CHART -->
      <div class="col-lg-6">
        <div class="card shadow-soft border-0 h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h5 class="mb-0">Monthly Appointments</h5>
              <span class="badge bg-light text-muted small">
                Current year
              </span>
            </div>
            <p class="small text-muted mb-3">
              Total appointments per month (Jan–Dec).
            </p>
            <div class="chart-wrapper">
              <canvas ref="lineChartCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. DONUT CHART -->
      <div class="col-lg-6">
        <div class="card shadow-soft border-0 h-100">
          <div class="card-body">
            <h5 class="mb-2">Appointment Distribution</h5>
            <p class="small text-muted mb-3">
              Overall split of completed, booked and cancelled appointments.
            </p>
            <div class="chart-wrapper">
              <canvas ref="pieChartCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. BAR CHART (ALL-TIME COUNTS) -->
      <div class="col-lg-6">
        <div class="card shadow-soft border-0 h-100">
          <div class="card-body">
            <h5 class="mb-2">Overall Status Counts</h5>
            <p class="small text-muted mb-3">
              Total number of appointments in each status (all time).
            </p>
            <div class="chart-wrapper">
              <canvas ref="barChartCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. THIS-MONTH STATUS SPLIT (HORIZONTAL BAR) -->
      <div class="col-lg-6">
        <div class="card shadow-soft border-0 h-100">
          <div class="card-body">
            <h5 class="mb-2">This Month Status Split</h5>
            <p class="small text-muted mb-3">
              Completed, booked and cancelled appointments for the current month.
            </p>
            <div class="chart-wrapper">
              <canvas ref="monthStatusChartCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= REPORT DOWNLOAD ================= -->
    <div class="card border-0 shadow-soft mt-4">
      <div
        class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3"
      >
        <div>
          <h5 class="mb-1">Download Monthly Report (PDF)</h5>
          <p class="small text-muted mb-0">
            Export your appointment &amp; patient summary for any month as PDF.
          </p>
        </div>

        <div class="d-flex gap-2 align-items-center">
          <input
            type="month"
            v-model="selectedMonth"
            class="form-control form-control-sm"
            style="width: 190px"
          />

          <button
            class="btn btn-primary rounded-pill btn-sm"
            :disabled="!selectedMonth || downloading"
            @click="downloadReport"
          >
            <span
              v-if="downloading"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            Download PDF
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/api/axios";
import Chart from "chart.js/auto";

export default {
  name: "DoctorStatistics",

  data() {
    return {
      loading: true,
      error: null,

      lastUpdated: null,

      stats: {
        total_patients: 0,
        appointments_this_month: 0,
        completed: 0,
        cancelled: 0,
        monthly_trend: [],
        status_counts: {
          completed: 0,
          booked: 0,
          cancelled: 0,
        },
        this_month_status_counts: {
          completed: 0,
          booked: 0,
          cancelled: 0,
        },
      },

      lineChart: null,
      pieChart: null,
      barChart: null,
      monthStatusChart: null,

      selectedMonth: "",
      downloading: false,
    };
  },

  computed: {
    lastUpdatedLabel() {
      if (!this.lastUpdated) return "Not yet";
      return this.lastUpdated.toLocaleString();
    },

    statCards() {
      const totalAllTime =
        this.stats.status_counts.completed +
        this.stats.status_counts.booked +
        this.stats.status_counts.cancelled;

      const completionRateAllTime =
        totalAllTime > 0
          ? Math.round(
              (this.stats.status_counts.completed / totalAllTime) * 100
            )
          : 0;

      return [
        {
          label: "Total Patients",
          value: this.stats.total_patients,
          sub: "Unique patients seen",
          class: "stat-primary",
          icon: "bi bi-people-fill",
        },
        {
          label: "Appointments (This Month)",
          value: this.stats.appointments_this_month,
          sub: "All statuses this month",
          class: "stat-info",
          icon: "bi bi-calendar2-week",
        },
        {
          label: "Completed (All Time)",
          value: this.stats.completed,
          sub: `Completion rate: ${completionRateAllTime}%`,
          class: "stat-success",
          icon: "bi bi-check2-circle",
        },
        {
          label: "Cancelled (All Time)",
          value: this.stats.cancelled,
          sub: "Total cancelled visits",
          class: "stat-warning",
          icon: "bi bi-x-circle",
        },
      ];
    },
  },

  created() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, "0");
    this.selectedMonth = `${yyyy}-${mm}`;

    this.loadStats();
  },

  methods: {
    async loadStats() {
      this.loading = true;
      this.error = null;

      try {
        const res = await api.get("/doctor/stats");
        this.stats = { ...this.stats, ...(res.data || {}) };
        this.lastUpdated = new Date();

        this.$nextTick(() => {
          this.renderCharts();
        });
      } catch (err) {
        console.error("Failed to load doctor stats:", err);
        this.error =
          err.response?.data?.message || "Failed to load statistics.";
      } finally {
        this.loading = false;
      }
    },

    renderCharts() {
      const months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ];

      // Line chart
      if (this.lineChart) this.lineChart.destroy();
      const lineCtx = this.$refs.lineChartCanvas?.getContext("2d");
      if (lineCtx) {
        this.lineChart = new Chart(lineCtx, {
          type: "line",
          data: {
            labels: months,
            datasets: [
              {
                label: "Appointments",
                data: this.stats.monthly_trend,
                tension: 0.35,
                fill: true,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { precision: 0 },
              },
            },
          },
        });
      }

      // Donut chart
      if (this.pieChart) this.pieChart.destroy();
      const pieCtx = this.$refs.pieChartCanvas?.getContext("2d");
      if (pieCtx) {
        this.pieChart = new Chart(pieCtx, {
          type: "doughnut",
          data: {
            labels: ["Completed", "Booked", "Cancelled"],
            datasets: [
              {
                data: [
                  this.stats.status_counts.completed,
                  this.stats.status_counts.booked,
                  this.stats.status_counts.cancelled,
                ],
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "bottom" },
            },
            cutout: "60%",
          },
        });
      }

      // Bar chart (all-time)
      if (this.barChart) this.barChart.destroy();
      const barCtx = this.$refs.barChartCanvas?.getContext("2d");
      if (barCtx) {
        this.barChart = new Chart(barCtx, {
          type: "bar",
          data: {
            labels: ["Completed", "Booked", "Cancelled"],
            datasets: [
              {
                label: "Appointments (All Time)",
                data: [
                  this.stats.status_counts.completed,
                  this.stats.status_counts.booked,
                  this.stats.status_counts.cancelled,
                ],
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { precision: 0 },
              },
            },
          },
        });
      }

      // This month status split (horizontal bar)
      if (this.monthStatusChart) this.monthStatusChart.destroy();
      const monthStatusCtx =
        this.$refs.monthStatusChartCanvas?.getContext("2d");
      if (monthStatusCtx) {
        this.monthStatusChart = new Chart(monthStatusCtx, {
          type: "bar",
          data: {
            labels: ["Completed", "Booked", "Cancelled"],
            datasets: [
              {
                label: "This Month",
                data: [
                  this.stats.this_month_status_counts.completed,
                  this.stats.this_month_status_counts.booked,
                  this.stats.this_month_status_counts.cancelled,
                ],
              },
            ],
          },
          options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                beginAtZero: true,
                ticks: { precision: 0 },
              },
            },
          },
        });
      }
    },

    // Download PDF report
    async downloadReport() {
      if (!this.selectedMonth) return;

      this.downloading = true;
      this.error = null;

      try {
        const res = await api.get("/doctor/monthly-report", {
          params: { month: this.selectedMonth },
          responseType: "blob",
        });

        // Mark it explicitly as PDF
        const blob = new Blob([res.data], { type: "application/pdf" });
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `doctor_report_${this.selectedMonth}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Failed to download monthly report:", err);
        this.error =
          err.response?.data?.message || "Failed to download report.";
      } finally {
        this.downloading = false;
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
  color: var(--bs-primary, #0d6efd);
  font-size: 1.4rem;
}

.page-title {
  font-weight: 600;
}

.page-subtitle {
  font-size: 0.9rem;
}

/* Stat cards */
.stat-card {
  border-radius: 1rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.12);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #6c757d;
}

.stat-subtext {
  font-size: 0.8rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.stat-icon {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

/* Color variants */
.stat-primary {
  background: linear-gradient(135deg, #e7f1ff, #f4f8ff);
}

.stat-info {
  background: linear-gradient(135deg, #e3f6ff, #f3fbff);
}

.stat-success {
  background: linear-gradient(135deg, #e6f9f0, #f3fcf7);
}

.stat-warning {
  background: linear-gradient(135deg, #fff4e5, #fff9f0);
}

/* Charts */
.chart-wrapper {
  position: relative;
  width: 100%;
  min-height: 260px;
}

.shadow-soft {
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06);
}
</style>
