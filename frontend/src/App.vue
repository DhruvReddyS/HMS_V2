<template>
  <div id="app">
    <!-- NAVBAR -->
    <nav
      class="navbar navbar-expand-lg navbar-light bg-white shadow-sm fixed-top custom-navbar"
    >
      <div class="container">

        <!-- Brand -->
        <router-link
          class="navbar-brand fw-bold d-flex align-items-center brand-link"
          :to="brandTarget"
        >
          <div class="brand-icon-wrapper d-flex align-items-center justify-content-center me-2">
            <span class="brand-icon">🏥</span>
          </div>
          <div class="d-flex flex-column lh-1">
            <span class="brand-text-main">
              <span class="text-primary">HMS</span> V2
            </span>
            <span class="brand-text-sub" v-if="isLoggedIn">
              {{ roleLabel }} Portal
            </span>
            <span class="brand-text-sub" v-else>
              Smart Hospital Platform
            </span>
          </div>
        </router-link>

        <!-- Mobile Toggle -->
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navMenu"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navMenu">
          <ul
            class="navbar-nav ms-auto mb-2 mb-lg-0 align-items-lg-center gap-lg-2 nav-pill-group"
          >

            <!-- PUBLIC NAV: Landing, Login, Register (only when NOT logged in) -->
            <template v-if="isPublicRoute">
              <li class="nav-item">
                <router-link class="nav-link nav-link-btn" to="/">
                  Home
                </router-link>
              </li>

              <li class="nav-item">
                <button
                  class="nav-link nav-link-btn btn btn-link"
                  @click="goToSection('about')"
                >
                  About
                </button>
              </li>

              <li class="nav-item">
                <button
                  class="nav-link nav-link-btn btn btn-link"
                  @click="goToSection('offer')"
                >
                  What We Offer
                </button>
              </li>

              <li class="nav-item">
                <button
                  class="nav-link nav-link-btn btn btn-link"
                  @click="goToSection('features')"
                >
                  Features
                </button>
              </li>

              <li class="nav-item d-none d-lg-block">
                <span class="nav-divider mx-2"></span>
              </li>

              <li class="nav-item">
                <router-link class="nav-link nav-link-btn" to="/login">
                  Login
                </router-link>
              </li>

              <li class="nav-item">
                <router-link
                  class="btn btn-primary px-3 rounded-pill nav-cta-btn"
                  to="/register"
                >
                  Sign Up
                </router-link>
              </li>
            </template>

            <!-- AUTH NAV: after login -->
            <template v-else>
              <!-- Small role badge -->
              <li class="nav-item d-none d-lg-block me-lg-2">
                <span
                  class="badge rounded-pill bg-light text-muted border role-pill d-flex align-items-center gap-1"
                >
                  <i class="bi bi-person-badge"></i>
                  {{ roleLabel }}
                </span>
              </li>

              <!-- ADMIN NAVBAR -->
              <template v-if="role === 'admin'">
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/admin/dashboard">
                    Dashboard
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/admin/doctors">
                    Manage Doctors
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/admin/patients">
                    Manage Patients
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/admin/appointments">
                    Appointments
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/admin/reports">
                    Reports
                  </router-link>
                </li>
                <li class="nav-item">
                  <button class="btn btn-outline-danger ms-lg-3" @click="logout">
                    Logout
                  </button>
                </li>
              </template>

              <!-- DOCTOR NAVBAR -->
              <template v-else-if="role === 'doctor'">
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/doctor/dashboard">
                    Dashboard
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/doctor/appointments">
                    Appointments
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/doctor/patients">
                    My Patients
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/doctor/availability">
                    Availability
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link
                    class="nav-link nav-link-btn"
                    to="/doctor/statistics"
                  >
                    Statistics &amp; Reports
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/doctor/profile">
                    Profile
                  </router-link>
                </li>
                <li class="nav-item">
                  <button class="btn btn-outline-danger ms-lg-3" @click="logout">
                    Logout
                  </button>
                </li>
              </template>

              <!-- PATIENT NAVBAR -->
              <template v-else-if="role === 'patient'">
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/patient/dashboard">
                    Dashboard
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/patient/book">
                    Book Appointment
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link
                    class="nav-link nav-link-btn"
                    to="/patient/appointments"
                  >
                    My Appointments
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/patient/departments">
                    Departments
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/patient/doctors">
                    Doctors
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/patient/history">
                    Visit History
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/patient/profile">
                    Profile
                  </router-link>
                </li>
                <li class="nav-item">
                  <button class="btn btn-outline-danger ms-lg-3" @click="logout">
                    Logout
                  </button>
                </li>
              </template>

              <!-- Fallback if somehow no role but token exists -->
              <template v-else>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/">
                    Home
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link class="nav-link nav-link-btn" to="/login">
                    Login
                  </router-link>
                </li>
              </template>
            </template>

          </ul>
        </div>
      </div>
    </nav>

    <!-- CONTENT -->
    <main class="app-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authStore } from './store/authStore'

const router = useRouter()
const route = useRoute()

const role = computed(() => authStore.role)
const isLoggedIn = computed(() => !!authStore.token)

// Brand target:
// - Not logged in → landing ("/")
// - Logged in → respective dashboard
const brandTarget = computed(() => {
  if (!isLoggedIn.value) return '/'
  if (role.value === 'admin') return '/admin/dashboard'
  if (role.value === 'doctor') return '/doctor/dashboard'
  return '/patient/dashboard'
})

// Public routes only when NOT logged in
const publicPaths = ['/', '/login', '/register']
const isPublicRoute = computed(() => {
  return !isLoggedIn.value && publicPaths.includes(route.path)
})

// human-readable role
const roleLabel = computed(() => {
  if (role.value === 'admin') return 'Admin'
  if (role.value === 'doctor') return 'Doctor'
  if (role.value === 'patient') return 'Patient'
  return 'User'
})

// Scroll helpers for landing page
const scrollToElement = (id) => {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const goToSection = async (sectionId) => {
  // If not already on landing, go there first
  if (route.path !== '/') {
    await router.push('/')
    await nextTick()
  }
  setTimeout(() => scrollToElement(sectionId), 80)
}

// REAL logout function
const logout = () => {
  authStore.clear()
  router.push('/')
}
</script>

<style>
html {
  scroll-behavior: smooth;
}

.app-content {
  padding-top: 85px; /* space for fixed navbar */
}

/* ================= NAVBAR SHELL ================= */

.custom-navbar {
  z-index: 1050;
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(180, 180, 180, 0.2);
  padding-top: 10px !important;
  padding-bottom: 10px !important;
  transition: background 0.25s ease, box-shadow 0.25s ease;
}

/* Give nav links slight group spacing on desktop */
.nav-pill-group {
  gap: 0.25rem;
}

/* Brand icon + text */
.brand-link {
  text-decoration: none !important;
}

.brand-icon-wrapper {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: rgba(13, 110, 253, 0.08);
}

.brand-icon {
  font-size: 1.3rem;
}

.brand-text-main {
  font-weight: 800;
  letter-spacing: -0.3px;
  font-size: 1.1rem;
}

.brand-text-sub {
  font-size: 0.7rem;
  color: #6c757d;
}

/* Divider */
.nav-divider {
  width: 1px;
  height: 24px;
  background: rgba(0, 0, 0, 0.12);
}

/* Role pill */
.role-pill {
  font-size: 0.75rem;
  padding: 4px 10px;
}

/* ================= NAV LINKS (ALL ROLES) ================= */

.nav-link-btn {
  border-radius: 999px;
  padding: 8px 16px !important;
  font-weight: 500;
  font-size: 0.95rem;
  color: #262a30 !important;
  transition: 0.18s ease;
}

/* Button links (landing About, Features) */
.nav-link-btn.btn-link {
  text-decoration: none;
}

/* Hover */
.nav-link-btn:hover {
  background: rgba(13, 110, 253, 0.08);
  color: #0d6efd !important;
  transform: translateY(-1px);
}

/* ACTIVE (exact match) */
.nav-link-btn.router-link-exact-active {
  background: rgba(13, 110, 253, 0.16);
  color: #0d6efd !important;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.22);
  border: 1px solid rgba(13, 110, 253, 0.4);
  transform: translateY(-1px);
}

/* Partial active (e.g. nested routes) */
.nav-link-btn.router-link-active {
  color: #0d6efd !important;
}

/* CTA Sign Up button */
.nav-cta-btn {
  font-weight: 600;
  box-shadow: 0 4px 10px rgba(13, 110, 253, 0.35);
}

/* ================= LOGOUT BUTTON ================= */

.btn-outline-danger {
  border-radius: 999px;
  padding: 7px 18px !important;
  font-weight: 600;
  transition: 0.18s ease;
}

.btn-outline-danger:hover {
  background: #dc3545;
  color: #fff !important;
  box-shadow: 0 3px 10px rgba(220, 53, 69, 0.35);
  transform: translateY(-1px);
}

/* ================= MOBILE TWEAKS ================= */

@media (max-width: 991px) {
  .navbar-nav .nav-item {
    margin: 6px 0;
  }

  .nav-link-btn {
    width: 100%;
    text-align: left;
    padding: 9px 14px !important;
  }

  .custom-navbar {
    background: rgba(255, 255, 255, 0.96) !important;
    backdrop-filter: blur(20px);
  }

  .brand-text-sub {
    display: none;
  }
}
</style>
