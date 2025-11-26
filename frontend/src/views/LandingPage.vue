<template>
  <div class="landing-page">

    <!-- Hero Section -->
    <section class="hero-section py-5 bg-light">
      <div class="container">
        <div class="row align-items-center gy-4">
          <div class="col-lg-6">
            <span class="badge bg-primary mb-3">Hospital Management System V2</span>
            <h1 class="display-5 fw-bold mb-3">
              Smart, secure & seamless <span class="text-primary">Hospital Management</span>
            </h1>
            <p class="lead text-muted mb-4">
              A unified platform for Admins, Doctors, and Patients to manage appointments,
              treatment history, and hospital operations — efficiently and securely.
            </p>

            <div class="d-flex flex-wrap gap-2 mb-3">
              <router-link to="/login" class="btn btn-primary btn-lg">
                Login to Dashboard
              </router-link>
              <router-link to="/register" class="btn btn-outline-primary btn-lg">
                Patient Sign Up
              </router-link>
            </div>

            <div class="d-flex flex-wrap gap-4 mt-3 small text-muted">
              <div>
                <span class="fw-bold text-dark">Role-based Access</span><br />
                Admin • Doctor • Patient
              </div>
              <div>
                <span class="fw-bold text-dark">Tech Stack</span><br />
                Flask API • VueJS • SQLite • Redis
              </div>
            </div>
          </div>

          <div class="col-lg-6">
            <div class="card shadow border-0 rounded-4 overflow-hidden">
              <div class="card-body p-4">
                <h5 class="fw-bold mb-3">At a glance</h5>
                <div class="row text-center">
                  <div class="col-4 border-end">
                    <div class="fs-3 fw-bold text-primary">3+</div>
                    <div class="small text-muted">User Roles</div>
                  </div>
                  <div class="col-4 border-end">
                    <div class="fs-3 fw-bold text-primary">7d</div>
                    <div class="small text-muted">Doctor Availability</div>
                  </div>
                  <div class="col-4">
                    <div class="fs-3 fw-bold text-primary">24x7</div>
                    <div class="small text-muted">Access Anywhere</div>
                  </div>
                </div>

                <hr class="my-4" />

                <h6 class="fw-semibold mb-2">Appointment Lifecycle</h6>
                <ul class="list-unstyled mb-0 small">
                  <li class="mb-1">✔ Patient books or reschedules an appointment</li>
                  <li class="mb-1">✔ Doctor reviews, treats & updates visit notes</li>
                  <li class="mb-1">✔ Admin monitors hospital-wide activity in real-time</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- About Us -->
    <section id="about" class="py-5">
      <div class="container">
        <div class="row mb-4">
          <div class="col-lg-8">
            <h2 class="fw-bold mb-3">About HMS V2</h2>
            <p class="text-muted">
              HMS V2 is a role-based Hospital Management System built as part of an academic
              project to simulate how modern hospitals digitalize their operations. It focuses
              on clear separation between Admin, Doctor, and Patient workflows while ensuring
              data consistency, performance, and ease of use.
            </p>
          </div>
        </div>

        <div class="row gy-4">
          <div class="col-md-4">
            <div class="card h-100 shadow-sm border-0">
              <div class="card-body">
                <h5 class="card-title fw-bold">Admin-focused</h5>
                <p class="card-text text-muted">
                  Admins manage doctors, patients, appointments, and reports from a unified
                  dashboard. They can search records, blacklist users, and monitor system-wide activity.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 shadow-sm border-0">
              <div class="card-body">
                <h5 class="card-title fw-bold">Doctor-centric</h5>
                <p class="card-text text-muted">
                  Doctors get a view of their day/week schedule, patient history, and can update
                  diagnosis, treatment, and next-visit suggestions in a few clicks.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 shadow-sm border-0">
              <div class="card-body">
                <h5 class="card-title fw-bold">Patient-friendly</h5>
                <p class="card-text text-muted">
                  Patients can self-register, book or cancel appointments, and access their
                  complete treatment history — all from a clean, responsive interface.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- What We Offer / Role-wise -->
    <section id="offer" class="py-5 bg-light">
      <div class="container">
        <div class="text-center mb-5">
          <h2 class="fw-bold mb-3">What We Offer</h2>
          <p class="text-muted mb-0">
            A complete digital workflow for every hospital stakeholder — from first booking
            to treatment history exports.
          </p>
        </div>

        <div class="row gy-4">
          <!-- Admin -->
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <span class="badge bg-dark mb-2">Admin</span>
                <h5 class="fw-bold mb-3">Admin Dashboard</h5>
                <ul class="list-unstyled small text-muted mb-3">
                  <li>✔ Total doctors, patients & appointments</li>
                  <li>✔ Doctor onboarding & profile management</li>
                  <li>✔ Patient & doctor search by name/specialization</li>
                  <li>✔ Blacklist/remove users if required</li>
                </ul>
                <router-link to="/admin/dashboard" class="btn btn-outline-dark btn-sm">
                  Go to Admin Dashboard
                </router-link>
              </div>
            </div>
          </div>

          <!-- Doctor -->
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <span class="badge bg-primary mb-2">Doctor</span>
                <h5 class="fw-bold mb-3">Doctor Workspace</h5>
                <ul class="list-unstyled small text-muted mb-3">
                  <li>✔ View upcoming day/week appointments</li>
                  <li>✔ Update visit status (Booked → Completed/Cancelled)</li>
                  <li>✔ Enter diagnosis, prescription & notes</li>
                  <li>✔ Access full patient history for better decisions</li>
                </ul>
                <router-link to="/doctor/dashboard" class="btn btn-outline-primary btn-sm">
                  Go to Doctor Dashboard
                </router-link>
              </div>
            </div>
          </div>

          <!-- Patient -->
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <span class="badge bg-success mb-2">Patient</span>
                <h5 class="fw-bold mb-3">Patient Portal</h5>
                <ul class="list-unstyled small text-muted mb-3">
                  <li>✔ Self-registration & profile updates</li>
                  <li>✔ Browse departments & doctor availability</li>
                  <li>✔ Book, reschedule, or cancel appointments</li>
                  <li>✔ Export treatment history as CSV (async job)</li>
                </ul>
                <router-link to="/patient/dashboard" class="btn btn-outline-success btn-sm">
                  Go to Patient Dashboard
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-5">
      <div class="container">
        <div class="text-center mb-5">
          <h2 class="fw-bold mb-3">Key Features</h2>
          <p class="text-muted mb-0">
            Built using Flask, VueJS, SQLite, Redis and Celery — with a focus on
            performance, reliability, and clean separation of concerns.
          </p>
        </div>

        <div class="row gy-4">
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <h5 class="fw-bold">Role-based Access Control</h5>
                <p class="small text-muted">
                  JWT-based authentication with separate flows for Admin, Doctor, and Patient.
                  Ensures each user only sees what they are allowed to manage.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <h5 class="fw-bold">Smart Appointment Handling</h5>
                <p class="small text-muted">
                  Prevents double-booking of doctors, dynamically updates appointment statuses,
                  and keeps a complete log of every visit for audits and history.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <h5 class="fw-bold">Async Jobs & Reminders</h5>
                <p class="small text-muted">
                  Daily visit reminders, monthly doctor activity reports, and CSV exports
                  run through Redis + Celery as background batch jobs.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <h5 class="fw-bold">Caching & Performance</h5>
                <p class="small text-muted">
                  Frequently accessed data like department lists and doctor availability is cached
                  using Redis to reduce DB load and speed up responses.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <h5 class="fw-bold">Clean API-first Design</h5>
                <p class="small text-muted">
                  Flask-based REST APIs power the entire system, making it easy to extend,
                  integrate or replace the frontend in future.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <h5 class="fw-bold">Responsive & Demo-ready</h5>
                <p class="small text-muted">
                  Fully responsive layout optimized for classroom demos, project evaluation,
                  and future extension into a real-world HMS prototype.
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- Call to Action + Footer -->
    <section class="py-5 bg-dark text-white">
      <div class="container text-center">
        <h3 class="fw-bold mb-3">Ready to explore HMS V2?</h3>
        <p class="mb-4 text-light small">
          Log in as Admin, Doctor, or Patient to experience the full workflow end-to-end.
        </p>
        <div class="d-flex justify-content-center gap-2 flex-wrap">
          <router-link to="/login" class="btn btn-primary btn-lg">
            Get Started
          </router-link>
          <router-link to="/register" class="btn btn-outline-light btn-lg">
            Create Patient Account
          </router-link>
        </div>
        <p class="mt-4 mb-0 small text-secondary">
          Built with Flask · VueJS · SQLite · Redis · Celery
        </p>
      </div>
    </section>

  </div>
</template>

<script setup>
// purely presentational for now
</script>

<style scoped>
.hero-section {
  min-height: 60vh;
  display: flex;
  align-items: center;
}
</style>
