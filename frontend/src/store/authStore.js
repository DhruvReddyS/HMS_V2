import { reactive } from 'vue'

const TOKEN_KEY = 'accessToken'
const ROLE_KEY = 'role'

export const authStore = reactive({
  token: sessionStorage.getItem(TOKEN_KEY) || null,
  role: sessionStorage.getItem(ROLE_KEY) || null,

  setAuth(token, role) {
    this.token = token
    this.role = role

    sessionStorage.setItem(TOKEN_KEY, token)
    sessionStorage.setItem(ROLE_KEY, role)

    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ROLE_KEY)
  },

  clear() {
    this.token = null
    this.role = null
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(ROLE_KEY)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ROLE_KEY)
  }
})
