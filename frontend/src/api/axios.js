import axios from "axios";
import { authStore } from "../store/authStore";

const api = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
});

api.interceptors.request.use(
  (config) => {
    const token =
      authStore.token || sessionStorage.getItem("accessToken") || null;

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err.response && err.response.status === 401) {
      authStore.clear();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
