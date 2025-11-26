// src/api/axios.js
import axios from 'axios'
import { authStore } from '../store/authStore'

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api'
})

// attach token on every request
api.interceptors.request.use(
  (config) => {
    const token =
      authStore.token || sessionStorage.getItem('accessToken') || null

    console.log('axios token:', token)

    if (token) {
      // Flask-JWT-Extended expects Bearer <token>
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

export default api
