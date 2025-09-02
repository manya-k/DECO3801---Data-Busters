import axios from "axios";

const baseURL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: `${baseURL}/api`, // adjust if backend URL changes
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
