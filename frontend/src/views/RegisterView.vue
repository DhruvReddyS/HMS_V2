<template>
  <div class="auth-page d-flex align-items-center justify-content-center">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-7 col-lg-6">

          <div class="card shadow border-0 rounded-4 auth-card">
            <div class="card-body p-4 p-md-5">

              <div class="text-center mb-4">
                <h2 class="fw-bold mb-1">Patient Sign Up</h2>
                <p class="text-muted small mb-0">
                  Create your patient account to book and manage appointments.
                </p>
              </div>

              <!-- Alert placeholder -->
              <div
                v-if="errorMessage"
                class="alert alert-danger py-2 small"
              >
                {{ errorMessage }}
              </div>

              <form @submit.prevent="handleRegister">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label class="form-label">Full Name</label>
                    <input
                      v-model="fullName"
                      type="text"
                      class="form-control"
                      placeholder="Enter your full name"
                      required
                    />
                  </div>

                  <div class="col-md-6 mb-3">
                    <label class="form-label">Username</label>
                    <input
                      v-model="username"
                      type="text"
                      class="form-control"
                      placeholder="Choose a username"
                      required
                    />
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label class="form-label">Email</label>
                    <input
                      v-model="email"
                      type="email"
                      class="form-control"
                      placeholder="you@example.com"
                      required
                    />
                  </div>

                  <div class="col-md-6 mb-3">
                    <label class="form-label">Phone</label>
                    <input
                      v-model="phone"
                      type="tel"
                      class="form-control"
                      placeholder="Contact number"
                    />
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label class="form-label">Password</label>
                    <input
                      v-model="password"
                      type="password"
                      class="form-control"
                      placeholder="Create a password"
                      required
                    />
                  </div>

                  <div class="col-md-6 mb-3">
                    <label class="form-label">Confirm Password</label>
                    <input
                      v-model="confirmPassword"
                      type="password"
                      class="form-control"
                      placeholder="Re-enter password"
                      required
                    />
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label">Address</label>
                  <textarea
                    v-model="address"
                    class="form-control"
                    rows="2"
                    placeholder="Residential address"
                  ></textarea>
                </div>

                <div class="d-flex justify-content-between align-items-center mb-3 small text-muted">
                  <span>
                    Note: Admin & Doctors are added from the Admin dashboard.
                  </span>
                </div>

                <button
                  class="btn btn-primary w-100 py-2"
                  type="submit"
                  :disabled="loading"
                >
                  <span v-if="!loading">Create Patient Account</span>
                  <span v-else>Creating Account...</span>
                </button>
              </form>

              <div class="text-center mt-3 small">
                <span class="text-muted">Already have an account?</span>
                <router-link to="/login" class="ms-1">
                  Login here
                </router-link>
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'

const router = useRouter()

const fullName = ref('')
const username = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const address = ref('')

const loading = ref(false)
const errorMessage = ref('')

const handleRegister = async () => {
  errorMessage.value = ''

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  loading.value = true

  try {
    await api.post('/auth/register', {
      full_name: fullName.value,
      username: username.value,
      email: email.value,
      phone: phone.value,
      password: password.value,
      address: address.value
    })

    // After successful registration -> go to login
    router.push('/login')
  } catch (err) {
    errorMessage.value =
      err.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>


<style scoped>
.auth-page {
  min-height: calc(100vh - 80px); /* adjust for fixed navbar */
  background: #f5f7fb;
}

.auth-card .form-control,
.auth-card textarea {
  border-radius: 0.6rem;
}
</style>
