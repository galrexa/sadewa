// src/services/api.js
import axios from "axios";

const BASE_URL = "http://localhost:8000";

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(
      "❌ API Response Error:",
      error.response?.data || error.message
    );
    return Promise.reject(error);
  }
);

// API Service Functions
export const apiService = {
  // Health check
  async healthCheck() {
    try {
      const response = await api.get("/health");
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Patient services
  async getAllPatients() {
    try {
      const response = await api.get("/api/patients");
      return { success: true, data: response.data };
    } catch (error) {
      throw new Error(`Failed to fetch patients: ${error.message}`);
    }
  },

  async getPatientById(patientId) {
    try {
      const response = await api.get(`/api/patients/${patientId}`);
      return { success: true, data: response.data };
    } catch (error) {
      throw new Error(`Failed to fetch patient: ${error.message}`);
    }
  },

  // ICD-10 services
  async searchICD10(query, limit = 10) {
    try {
      const response = await api.get("/api/icd10/search", {
        params: { q: query, limit },
      });
      return { success: true, data: response.data };
    } catch (error) {
      throw new Error(`Failed to search ICD-10: ${error.message}`);
    }
  },

  // Drug interaction analysis
  async analyzeInteractions(payload) {
    try {
      const response = await api.post("/api/analyze-interactions", payload);
      return { success: true, data: response.data };
    } catch (error) {
      throw new Error(`Failed to analyze interactions: ${error.message}`);
    }
  },

  // Test Groq connection
  async testGroq() {
    try {
      const response = await api.get("/api/test-groq");
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },
};

export default api;
