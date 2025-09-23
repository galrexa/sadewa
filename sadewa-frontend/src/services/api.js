// src/services/api.js - Clean API Service for SADEWA (No Mock Data)
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

console.log("API Configuration:", { BASE_URL });

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000, // 15 seconds timeout
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(
      `API Request: ${config.method?.toUpperCase()} ${config.baseURL}${
        config.url
      }`
    );
    if (config.data) {
      console.log("Request Data:", config.data);
    }
    if (config.params) {
      console.log("Request Params:", config.params);
    }
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    if (response.data) {
      console.log("Response Data:", response.data);
    }
    return response;
  },
  (error) => {
    console.error("API Response Error:", {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url,
    });
    return Promise.reject(error);
  }
);

// Drug Service Functions
export const drugService = {
  // Search drugs from database
  async searchDrugs(query, limit = 10) {
    try {
      console.log(`Searching drugs: "${query}"`);
      const response = await api.get("/api/drugs/search", {
        params: { q: query, limit },
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error("Drug search failed:", error);
      throw new Error(`Failed to search drugs: ${error.message}`);
    }
  },

  // Autocomplete for medication input
  async autocompleteDrugs(query, limit = 5) {
    try {
      const response = await api.get("/api/drugs/autocomplete", {
        params: { q: query, limit },
      });
      return response.data.suggestions;
    } catch (error) {
      console.error("Drug autocomplete failed:", error);
      throw new Error(`Failed to autocomplete drugs: ${error.message}`);
    }
  },

  // Check interactions using database
  async checkDrugInteractions(drugNames) {
    try {
      console.log("Checking drug interactions:", drugNames);
      const drugNamesStr = drugNames.join(",");
      const response = await api.get("/api/drugs/check-interactions", {
        params: { drug_names: drugNamesStr },
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error("Drug interaction check failed:", error);
      throw new Error(`Failed to check drug interactions: ${error.message}`);
    }
  },

  // Get drug database stats
  async getDrugStats() {
    try {
      const response = await api.get("/api/drugs/stats");
      return { success: true, data: response.data };
    } catch (error) {
      console.error("Drug stats failed:", error);
      throw new Error(`Failed to get drug stats: ${error.message}`);
    }
  },
};

// Main API Service Functions
export const apiService = {
  // Expose the axios instance for direct use if needed
  api,

  // Health check
  async healthCheck() {
    try {
      console.log("Checking system health...");
      const response = await api.get("/health");
      console.log("Health check successful:", response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error("Health check failed:", error.message);
      throw new Error(`Health check failed: ${error.message}`);
    }
  },

  // Patient services
  async getAllPatients() {
    try {
      console.log("Fetching all patients from backend...");

      const response = await api.get("/api/patients/search", {
        params: {
          page: 1,
          limit: 100,
        },
      });

      console.log("API Response:", response.data);

      if (response.data && response.data.patients) {
        console.log(
          `Fetched ${response.data.patients.length} patients from API`
        );
        return {
          success: true,
          data: response.data.patients,
          total: response.data.total,
        };
      } else {
        throw new Error("Invalid response structure");
      }
    } catch (error) {
      console.error("Failed to fetch patients from API:", error);
      throw new Error(`Failed to fetch patients: ${error.message}`);
    }
  },

  async getPatientById(patientId) {
    try {
      console.log(`Fetching patient ${patientId} from API...`);
      const response = await api.get(`/api/patients/${patientId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error(`Failed to fetch patient ${patientId} from API:`, error);
      const errorMessage =
        error.response?.data?.detail || error.message || "Unknown error";
      throw new Error(`Failed to fetch patient: ${errorMessage}`);
    }
  },

  // ICD-10 services
  async searchICD10(query, limit = 10) {
    try {
      console.log(`Searching ICD-10 for: "${query}"`);
      const response = await api.get("/api/icd10/search", {
        params: { q: query, limit },
      });
      console.log(`Found ${response.data.length} ICD-10 results`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error("ICD-10 search failed:", error);
      throw new Error(`Failed to search ICD-10: ${error.message}`);
    }
  },

  // Tambahkan di object apiService:
  async getCurrentMedications(patientId) {
    try {
      const response = await api.get(
        `/api/patients/${patientId}/current-medications`
      );
      console.log("Current medications response:", response.data);
      return { success: true, ...response.data };
    } catch (error) {
      console.error("Failed to get current medications:", error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message,
      };
    }
  },
  // Drug interaction analysis
  async analyzeInteractions(payload) {
    try {
      // Format payload dengan patient_id sebagai string
      const formattedPayload = {
        patient_id: String(payload.patient_id),
        new_medications: payload.new_medications || [],
        notes: payload.notes || null,
        diagnoses: payload.diagnoses || [],
      };

      console.log("Sending analysis payload:", formattedPayload);

      const response = await api.post(
        "/api/analyze-interactions",
        formattedPayload
      );
      console.log("Analysis response received:", response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error("Analysis failed:", {
        status: error.response?.status,
        data: error.response?.data,
        originalPatientId: payload.patient_id,
      });

      const errorMessage =
        error.response?.data?.detail || error.message || "Analysis failed";
      throw new Error(`Failed to analyze interactions: ${errorMessage}`);
    }
  },

  // Enhanced drug interaction analysis with database integration
  async analyzeInteractionsEnhanced(payload) {
    try {
      console.log("Enhanced analyzing interactions:", payload);

      // Step 1: Check database interactions first
      const drugNames = payload.new_medications.map((med) => {
        return med.split(" ")[0]; // Extract drug name from "Name Dosage" format
      });

      let dbInteractions = [];
      try {
        const dbResult = await drugService.checkDrugInteractions(drugNames);
        if (dbResult.success) {
          dbInteractions = dbResult.data.interactions || [];
        }
      } catch (error) {
        console.warn(
          "Database interaction check failed, continuing with AI analysis"
        );
      }

      // Step 2: Call AI analysis
      let aiAnalysis = {};
      try {
        const aiResponse = await this.analyzeInteractions(payload);
        aiAnalysis = aiResponse.data;
      } catch (error) {
        console.warn("AI analysis failed, using database results only");
        aiAnalysis = {
          interactions: [],
          summary: "AI analysis unavailable, using database interactions only.",
          confidence_score: 0.7,
          processing_time: 1.0,
          llm_reasoning:
            "Database-only analysis performed due to AI service unavailability.",
        };
      }

      // Step 3: Merge database and AI results
      const mergedInteractions = [
        // Database interactions (higher priority)
        ...dbInteractions.map((db) => ({
          severity: db.severity,
          medications: [db.drug_a, db.drug_b],
          description: db.description,
          recommendation: db.recommendation,
          source: "database",
          confidence: 0.95,
        })),
        // AI interactions (if not already covered by database)
        ...(aiAnalysis.interactions || [])
          .filter((ai) => {
            return !dbInteractions.some(
              (db) =>
                ai.medications &&
                ai.medications.some(
                  (med) =>
                    db.drug_a.toLowerCase().includes(med.toLowerCase()) ||
                    db.drug_b.toLowerCase().includes(med.toLowerCase())
                )
            );
          })
          .map((ai) => ({
            ...ai,
            source: "ai",
            confidence: aiAnalysis.confidence_score || 0.8,
          })),
      ];

      // Step 4: Enhanced analysis summary
      const enhancedAnalysis = {
        ...aiAnalysis,
        interactions: mergedInteractions,
        analysis_type: "hybrid",
        database_interactions: dbInteractions.length,
        ai_interactions: (aiAnalysis.interactions || []).length,
        total_interactions: mergedInteractions.length,
        summary: this.generateEnhancedSummary(
          mergedInteractions,
          aiAnalysis.summary
        ),
      };

      console.log("Enhanced analysis complete:", enhancedAnalysis);
      return { success: true, data: enhancedAnalysis };
    } catch (error) {
      console.error("Enhanced analysis failed:", error);
      // Fallback to original method
      return await this.analyzeInteractions(payload);
    }
  },

  // Helper function to generate enhanced summary
  generateEnhancedSummary(interactions, aiSummary) {
    if (interactions.length === 0) {
      return "No significant drug interactions detected in both database and AI analysis.";
    }

    const majorCount = interactions.filter(
      (i) => i.severity === "Major"
    ).length;
    const moderateCount = interactions.filter(
      (i) => i.severity === "Moderate"
    ).length;
    const minorCount = interactions.filter(
      (i) => i.severity === "Minor"
    ).length;
    const dbCount = interactions.filter((i) => i.source === "database").length;
    const aiCount = interactions.filter((i) => i.source === "ai").length;

    let summary = "";

    if (majorCount > 0) {
      summary += `${majorCount} MAJOR interaction(s) detected. `;
    }
    if (moderateCount > 0) {
      summary += `${moderateCount} moderate interaction(s) found. `;
    }
    if (minorCount > 0) {
      summary += `${minorCount} minor interaction(s) noted. `;
    }

    summary += `Analysis based on ${dbCount} database record(s) and ${aiCount} AI prediction(s).`;

    if (aiSummary) {
      summary += ` AI Analysis: ${aiSummary}`;
    }

    return summary;
  },

  // Test Groq connection
  async testGroq() {
    try {
      console.log("Testing Groq connection...");
      const response = await api.get("/api/test-groq");
      return { success: true, data: response.data };
    } catch (error) {
      console.error("Groq test failed:", error);
      throw new Error(`Failed to test Groq: ${error.message}`);
    }
  },

  // Additional utility methods
  async ping() {
    try {
      const startTime = Date.now();
      await api.get("/");
      const endTime = Date.now();
      return {
        success: true,
        responseTime: endTime - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      };
    }
  },
};

// Export individual services for modular usage
export default api;
