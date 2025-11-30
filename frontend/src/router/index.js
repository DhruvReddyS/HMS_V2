import { createRouter, createWebHistory } from "vue-router";
import { authStore } from "../store/authStore";

import LandingPage from "../views/LandingPage.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";

import AdminDashboard from "../views/admin/AdminDashboard.vue";
import AdminDoctors from "../views/admin/AdminDoctors.vue";
import AdminPatients from "../views/admin/AdminPatients.vue";
import AdminAppointments from "../views/admin/AdminAppointments.vue";
import AdminAppointmentDetails from "../views/admin/AdminAppointmentDetails.vue";
import AdminReports from "../views/admin/AdminReports.vue";

import DoctorDashboard from "../views/doctor/DoctorDashboard.vue";
import DoctorAppointments from "../views/doctor/DoctorAppointments.vue";
import DoctorPatientHistory from "../views/doctor/DoctorPatientHistory.vue";
import DoctorAvailability from "../views/doctor/DoctorAvailability.vue";
import DoctorProfile from "../views/doctor/DoctorProfile.vue";
import DoctorMyPatients from "../views/doctor/DoctorMyPatients.vue";
import DoctorStatistics from "../views/doctor/DoctorStatistics.vue";

import PatientDashboard from "../views/patient/PatientDashboard.vue";
import PatientProfile from "../views/patient/PatientProfile.vue";
import PatientAppointments from "../views/patient/PatientAppointments.vue";
import PatientBook from "../views/patient/PatientBook.vue";
import PatientDepartments from "../views/patient/PatientDepartments.vue";
import PatientDoctors from "../views/patient/PatientDoctors.vue";
import PatientHistory from "../views/patient/PatientHistory.vue";

const routes = [
  { path: "/", name: "Landing", component: LandingPage },
  { path: "/login", name: "Login", component: LoginView },
  { path: "/register", name: "Register", component: RegisterView },

  { path: "/admin/dashboard", name: "AdminDashboard", component: AdminDashboard },
  { path: "/admin/doctors", name: "AdminDoctors", component: AdminDoctors },
  { path: "/admin/patients", name: "AdminPatients", component: AdminPatients },
  { path: "/admin/appointments", name: "AdminAppointments", component: AdminAppointments },
  { path: "/admin/appointments/:id", name: "AdminAppointmentDetails", component: AdminAppointmentDetails, props: true },
  { path: "/admin/reports", name: "AdminReports", component: AdminReports },

  { path: "/doctor/dashboard", name: "DoctorDashboard", component: DoctorDashboard },
  { path: "/doctor/appointments", name: "DoctorAppointments", component: DoctorAppointments },
  { path: "/doctor/patient-history", name: "DoctorPatientHistory", component: DoctorPatientHistory },
  { path: "/doctor/availability", name: "DoctorAvailability", component: DoctorAvailability },
  { path: "/doctor/profile", name: "DoctorProfile", component: DoctorProfile },
  { path: "/doctor/patients", name: "DoctorMyPatients", component: DoctorMyPatients },
  { path: "/doctor/statistics", name: "DoctorStatistics", component: DoctorStatistics },

  { path: "/patient/dashboard", name: "PatientDashboard", component: PatientDashboard },
  { path: "/patient/profile", name: "PatientProfile", component: PatientProfile },
  { path: "/patient/appointments", name: "PatientAppointments", component: PatientAppointments },
  { path: "/patient/book", name: "PatientBook", component: PatientBook },
  { path: "/patient/departments", name: "PatientDepartments", component: PatientDepartments },
  { path: "/patient/doctors", name: "PatientDoctors", component: PatientDoctors },
  { path: "/patient/history", name: "PatientHistory", component: PatientHistory },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const role = authStore.role;
  const publicPaths = ["/", "/login", "/register"];

  if (!role && !publicPaths.includes(to.path)) {
    return next({ name: "Login" });
  }

  if (role && (to.path === "/login" || to.path === "/register")) {
    if (role === "admin") return next({ name: "AdminDashboard" });
    if (role === "doctor") return next({ name: "DoctorDashboard" });
    if (role === "patient") return next({ name: "PatientDashboard" });
    return next({ path: "/" });
  }

  if (to.path.startsWith("/admin") && role !== "admin") {
    return next({ name: "Login" });
  }
  if (to.path.startsWith("/doctor") && role !== "doctor") {
    return next({ name: "Login" });
  }
  if (to.path.startsWith("/patient") && role !== "patient") {
    return next({ name: "Login" });
  }

  next();
});

export default router;
