import axios from "axios";

/**
 * Axios API instance
 *
 * Creates a pre-configured Axios instance (`api`) that can be reused
 * across the frontend to communicate with the backend.
 *
 * Configuration:
 * - `baseURL`: points to the backend API root (default: http://127.0.0.1:8000/api).
 *   → Adjust this if the backend URL changes 
 * - `headers`: sets default request headers.
 *   → Currently enforces JSON payloads with "Content-Type: application/json".
 *
 * Benefits of using a central Axios instance:
 * - Keeps API calls consistent and easy to update.
 * - Allows adding interceptors (e.g., for authentication tokens or error logging).
 * - Prevents duplication of baseURL and header configs in every API file.
 *
 * @module api
 * @returns {AxiosInstance} A configured Axios instance for making HTTP requests.
 */
const api = axios.create({
  baseURL: "http://127.0.0.1:9000/api", // adjust if backend URL changes
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
