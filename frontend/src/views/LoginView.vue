<template>
  <div class="auth-page d-flex align-items-center justify-content-center">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
          <div class="card shadow border-0 rounded-4 auth-card">
            <div class="card-body p-4 p-md-5">
              <div class="text-center mb-4">
                <h2 class="fw-bold mb-1">Welcome Back</h2>
                <p class="text-muted small mb-0">
                  Login to continue.
                </p>
              </div>

              <div v-if="errorMessage" class="alert alert-danger py-2 small">
                {{ errorMessage }}
              </div>

              <form @submit.prevent="handleLogin">
                <div class="mb-3">
                  <label class="form-label">Username</label>
                  <input
                    v-model="username"
                    type="text"
                    class="form-control"
                    placeholder="Enter username"
                    required
                  />
                </div>

                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input
                    v-model="password"
                    type="password"
                    class="form-control"
                    placeholder="Enter password"
                    required
                  />
                </div>

                <button
                  class="btn btn-primary w-100 py-2"
                  type="submit"
                  :disabled="loading"
                >
                  <span v-if="!loading">Login</span>
                  <span v-else>Logging in...</span>
                </button>
              </form>

              <div class="text-center mt-3 small">
                <span class="text-muted">New patient?</span>
                <router-link to="/register" class="ms-1">
                  Create an account
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'
import { authStore } from '../store/authStore'

const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

onMounted(() => {
  // whenever user visits /login, reset session (logout)
  authStore.clear()
})

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const res = await api.post('/auth/login', {
      username: username.value,
      password: password.value
    })

    console.log('Login Response:', res.data)

    const token = res.data.access_token
    const userObj = res.data.user || null
    const role = res.data.role || userObj?.role || 'patient'

    if (!token) throw new Error('No access token received')

    authStore.clear()
    authStore.setAuth(token, role)

    if (role === 'admin') {
      router.push('/admin/dashboard')
    } else if (role === 'doctor') {
      router.push('/doctor/dashboard')
    } else {
      router.push('/patient/dashboard')
    }
  } catch (err) {
    console.error('Login Error:', err)
    errorMessage.value =
      err?.response?.data?.message || err.message || 'Login failed.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #f5f7fb;
}

.auth-card {
  background: #fff;
  border-radius: 1rem;
}

.auth-card .form-control {
  border-radius: 0.7rem;
}
</style>
