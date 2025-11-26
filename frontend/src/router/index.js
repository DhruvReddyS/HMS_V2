import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/authStore'

// Public views
import LandingPage from '../views/LandingPage.vue'
import LoginView from '../views/LoginView.vue'       // ✅ correct file name
import RegisterView from '../views/RegisterView.vue'

// Admin views
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import AdminDoctors from '../views/admin/AdminDoctors.vue'
import AdminPatients from '../views/admin/AdminPatients.vue'
import AdminAppointments from '../views/admin/AdminAppointments.vue'
import AdminAppointmentDetails from '../views/admin/AdminAppointmentDetails.vue'

// Doctor views
import DoctorDashboard from '../views/doctor/DoctorDashboard.vue'

// Patient views
import PatientDashboard from '../views/patient/PatientDashboard.vue'
import PatientProfile from '../views/patient/PatientProfile.vue'
import PatientAppointments from '../views/patient/PatientAppointments.vue'
import PatientBook from '../views/patient/PatientBook.vue'
import PatientDepartments from '../views/patient/PatientDepartments.vue'
import PatientDoctors from '../views/patient/PatientDoctors.vue'
import PatientHistory from '../views/patient/PatientHistory.vue'

const routes = [
  // ---------- Public ----------
  { path: '/', name: 'Landing', component: LandingPage },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/register', name: 'Register', component: RegisterView },

  // ---------- Admin ----------
  { path: '/admin/dashboard', name: 'AdminDashboard', component: AdminDashboard },
  { path: '/admin/doctors', name: 'AdminDoctors', component: AdminDoctors },
  { path: '/admin/patients', name: 'AdminPatients', component: AdminPatients },
  { path: '/admin/appointments', name: 'AdminAppointments', component: AdminAppointments },
  {
    path: '/admin/appointments/:id',
    name: 'AdminAppointmentDetails',
    component: AdminAppointmentDetails,
    props: true
  },

  // ---------- Doctor ----------
  { path: '/doctor/dashboard', name: 'DoctorDashboard', component: DoctorDashboard },

  // ---------- Patient ----------
  { path: '/patient/dashboard', name: 'PatientDashboard', component: PatientDashboard },
  { path: '/patient/profile', name: 'PatientProfile', component: PatientProfile },
  { path: '/patient/appointments', name: 'PatientAppointments', component: PatientAppointments },
  { path: '/patient/book', name: 'PatientBook', component: PatientBook },
  { path: '/patient/departments', name: 'PatientDepartments', component: PatientDepartments },
  { path: '/patient/doctors', name: 'PatientDoctors', component: PatientDoctors },
  { path: '/patient/history', name: 'PatientHistory', component: PatientHistory }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ❌ REMOVE the old localStorage restore lines completely:
// authStore.role  = localStorage.getItem("role")
// authStore.token = localStorage.getItem("accessToken")

// ------------------------------
// 🔐 Route Guards
// ------------------------------
router.beforeEach((to, from, next) => {
  const role = authStore.role
  const publicPaths = ['/', '/login', '/register']

  // 1) Not logged in → block all non-public routes
  if (!role && !publicPaths.includes(to.path)) {
    return next({ name: 'Login' })
  }

  // 2) Already logged in → avoid showing login/register again
  if (role && (to.path === '/login' || to.path === '/register')) {
    if (role === 'admin') return next({ name: 'AdminDashboard' })
    if (role === 'doctor') return next({ name: 'DoctorDashboard' })
    if (role === 'patient') return next({ name: 'PatientDashboard' })
    return next({ path: '/' })
  }

  // 3) Role-based protection
  if (to.path.startsWith('/admin') && role !== 'admin') {
    return next({ name: 'Login' })
  }
  if (to.path.startsWith('/doctor') && role !== 'doctor') {
    return next({ name: 'Login' })
  }
  if (to.path.startsWith('/patient') && role !== 'patient') {
    return next({ name: 'Login' })
  }

  next()
})

export default router
