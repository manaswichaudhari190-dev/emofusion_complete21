import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:5000",
  timeout: 30000,
  withCredentials: true,
});

// Auto-attach token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("emo_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("emo_token");
      localStorage.removeItem("emo_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
