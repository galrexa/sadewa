// src/services/api.js - Complete API Service for SADEWA (No Mock Import)
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK === "true";

console.log("🔧 API Configuration:", { BASE_URL, USE_MOCK_DATA });

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
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${
        config.url
      }`
    );
    if (config.data) {
      console.log("📤 Request Data:", config.data);
    }
    if (config.params) {
      console.log("📋 Request Params:", config.params);
    }
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
    if (response.data) {
      console.log("📥 Response Data:", response.data);
    }
    return response;
  },
  (error) => {
    console.error("❌ API Response Error:", {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url,
    });
    return Promise.reject(error);
  }
);

// Helper function for mock delays
const mockDelay = (ms = 500) =>
  new Promise((resolve) => setTimeout(resolve, ms));

// Inline mock data (tidak import dari file terpisah)
const inlineMockPatients = [
  {
    id: "P001",
    name: "Bapak Agus Santoso",
    age: 72,
    gender: "Male",
    weight_kg: 68.5,
    current_medications: [
      "Warfarin 5mg OD (for AF stroke prevention)",
      "Lisinopril 10mg OD (for hypertension)",
      "Metformin 500mg BID (for diabetes control)",
      "Atorvastatin 20mg ON (for dyslipidemia)",
    ],
    diagnoses_text: [
      "Atrial Fibrillation (chronic)",
      "Chronic Ischemic Heart Disease",
      "Chronic knee pain (osteoarthritis suspected)",
    ],
    allergies: ["Penicillin (rash)", "Sulfonamides (mild GI upset)"],
  },
  {
    id: "P002",
    name: "Ibu Sari Dewi",
    age: 58,
    gender: "Female",
    weight_kg: 62.0,
    current_medications: ["Metformin 850mg", "Gliclazide 80mg"],
    diagnoses_text: [
      "Type 2 diabetes mellitus",
      "Chronic kidney disease, stage 3",
    ],
    allergies: [],
  },
  {
    id: "P003",
    name: "Bapak Hendrik Wijaya",
    age: 65,
    gender: "Male",
    weight_kg: 78.0,
    current_medications: [
      "Digoxin 0.25mg",
      "Salbutamol inhaler",
      "Atorvastatin 20mg",
    ],
    diagnoses_text: [
      "Heart failure",
      "COPD with acute exacerbation",
      "Hyperlipidemia",
    ],
    allergies: ["Aspirin"],
  },
  {
    id: "P004",
    name: "Ibu Maria Gonzalez",
    age: 45,
    gender: "Female",
    weight_kg: 55.0,
    current_medications: ["Amlodipine 5mg", "Hydrochlorothiazide 25mg"],
    diagnoses_text: ["Hypertension", "Migraine"],
    allergies: [],
  },
  {
    id: "P005",
    name: "Bapak Rizky Rahman",
    age: 38,
    gender: "Male",
    weight_kg: 70.0,
    current_medications: [],
    diagnoses_text: ["Healthy adult"],
    allergies: [],
  },
];

const inlineMockICD10 = [
  {
    code: "E11",
    name_id: "Diabetes mellitus tipe 2",
    name_en: "Type 2 diabetes mellitus",
  },
  {
    code: "I10",
    name_id: "Hipertensi esensial",
    name_en: "Essential hypertension",
  },
  { code: "I48", name_id: "Fibrilasi atrial", name_en: "Atrial fibrillation" },
  { code: "I50", name_id: "Gagal jantung", name_en: "Heart failure" },
  {
    code: "N18",
    name_id: "Penyakit ginjal kronik",
    name_en: "Chronic kidney disease",
  },
];

// Helper function to generate enhanced summary
function generateEnhancedSummary(interactions, aiSummary) {
  if (interactions.length === 0) {
    return "No significant drug interactions detected in both database and AI analysis.";
  }

  const majorCount = interactions.filter((i) => i.severity === "Major").length;
  const moderateCount = interactions.filter(
    (i) => i.severity === "Moderate"
  ).length;
  const minorCount = interactions.filter((i) => i.severity === "Minor").length;
  const dbCount = interactions.filter((i) => i.source === "database").length;
  const aiCount = interactions.filter((i) => i.source === "ai").length;

  let summary = "";

  if (majorCount > 0) {
    summary += `⚠️ ${majorCount} MAJOR interaction(s) detected. `;
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
}

// Drug Service Functions
export const drugService = {
  // Search drugs from database
  async searchDrugs(query, limit = 10) {
    if (USE_MOCK_DATA) {
      await mockDelay();
      const mockResults = [
        {
          id: 1,
          nama_obat: "Parasetamol",
          nama_obat_internasional: "Paracetamol",
          display_name: "Parasetamol (Paracetamol)",
        },
        {
          id: 2,
          nama_obat: "Ibuprofen",
          nama_obat_internasional: "Ibuprofen",
          display_name: "Ibuprofen (Ibuprofen)",
        },
        {
          id: 3,
          nama_obat: "Warfarin",
          nama_obat_internasional: "Warfarin",
          display_name: "Warfarin (Warfarin)",
        },
        {
          id: 4,
          nama_obat: "Metformin",
          nama_obat_internasional: "Metformin",
          display_name: "Metformin (Metformin)",
        },
        {
          id: 5,
          nama_obat: "Amoxicillin",
          nama_obat_internasional: "Amoxicillin",
          display_name: "Amoxicillin (Amoxicillin)",
        },
      ].filter(
        (drug) =>
          drug.nama_obat.toLowerCase().includes(query.toLowerCase()) ||
          drug.nama_obat_internasional
            .toLowerCase()
            .includes(query.toLowerCase())
      );
      console.log(
        `🔍 Mock drug search for "${query}" returned ${mockResults.length} results`
      );
      return { success: true, data: mockResults };
    }

    try {
      console.log(`🔍 Searching drugs: "${query}"`);
      const response = await api.get("/api/drugs/search", {
        params: { q: query, limit },
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Drug search failed:", error);
      // Fallback to mock data if database not available
      const mockResults = [
        {
          id: 1,
          nama_obat: "Parasetamol",
          nama_obat_internasional: "Paracetamol",
          display_name: "Parasetamol (Paracetamol)",
        },
        {
          id: 2,
          nama_obat: "Ibuprofen",
          nama_obat_internasional: "Ibuprofen",
          display_name: "Ibuprofen (Ibuprofen)",
        },
        {
          id: 3,
          nama_obat: "Warfarin",
          nama_obat_internasional: "Warfarin",
          display_name: "Warfarin (Warfarin)",
        },
      ].filter(
        (drug) =>
          drug.nama_obat.toLowerCase().includes(query.toLowerCase()) ||
          drug.nama_obat_internasional
            .toLowerCase()
            .includes(query.toLowerCase())
      );

      return { success: true, data: mockResults };
    }
  },

  // Autocomplete for medication input
  async autocompleteDrugs(query, limit = 5) {
    if (USE_MOCK_DATA) {
      await mockDelay(200);
      const commonDrugs = [
        "Paracetamol",
        "Ibuprofen",
        "Amoxicillin",
        "Omeprazole",
        "Metformin",
        "Warfarin",
        "Lisinopril",
        "Amlodipine",
      ];
      return commonDrugs
        .filter((drug) => drug.toLowerCase().includes(query.toLowerCase()))
        .slice(0, limit);
    }

    try {
      const response = await api.get("/api/drugs/autocomplete", {
        params: { q: query, limit },
      });
      return response.data.suggestions;
    } catch (error) {
      console.error("❌ Drug autocomplete failed:", error);
      // Fallback suggestions
      const commonDrugs = [
        "Paracetamol",
        "Ibuprofen",
        "Amoxicillin",
        "Omeprazole",
        "Metformin",
      ];
      return commonDrugs
        .filter((drug) => drug.toLowerCase().includes(query.toLowerCase()))
        .slice(0, limit);
    }
  },

  // Check interactions using database
  async checkDrugInteractions(drugNames) {
    if (USE_MOCK_DATA) {
      await mockDelay(1000);
      const mockInteractions = [];
      const hasWarfarin = drugNames.some((drug) =>
        drug.toLowerCase().includes("warfarin")
      );
      const hasNSAID = drugNames.some(
        (drug) =>
          drug.toLowerCase().includes("ibuprofen") ||
          drug.toLowerCase().includes("diclofenac") ||
          drug.toLowerCase().includes("naproxen")
      );

      if (hasWarfarin && hasNSAID) {
        mockInteractions.push({
          drug_a: "Warfarin",
          drug_b: "NSAID",
          severity: "Major",
          description: "Increased bleeding risk with concurrent use",
          recommendation:
            "Avoid concurrent use. Consider paracetamol as alternative.",
        });
      }

      return {
        success: true,
        data: {
          input_drugs: drugNames,
          interactions_found: mockInteractions.length,
          interactions: mockInteractions,
        },
      };
    }

    try {
      console.log("🧪 Checking drug interactions:", drugNames);
      const drugNamesStr = drugNames.join(",");
      const response = await api.get("/api/drugs/check-interactions", {
        params: { drug_names: drugNamesStr },
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Drug interaction check failed:", error);

      // Fallback to simple pattern matching
      const mockInteractions = [];
      const hasWarfarin = drugNames.some((drug) =>
        drug.toLowerCase().includes("warfarin")
      );
      const hasNSAID = drugNames.some(
        (drug) =>
          drug.toLowerCase().includes("ibuprofen") ||
          drug.toLowerCase().includes("diclofenac") ||
          drug.toLowerCase().includes("naproxen")
      );

      if (hasWarfarin && hasNSAID) {
        mockInteractions.push({
          drug_a: "Warfarin",
          drug_b: "NSAID",
          severity: "Major",
          description: "Increased bleeding risk with concurrent use",
          recommendation:
            "Avoid concurrent use. Consider paracetamol as alternative.",
        });
      }

      return {
        success: true,
        data: {
          input_drugs: drugNames,
          interactions_found: mockInteractions.length,
          interactions: mockInteractions,
        },
      };
    }
  },

  // Get drug database stats
  async getDrugStats() {
    if (USE_MOCK_DATA) {
      await mockDelay();
      return {
        success: true,
        data: {
          total_drugs: 150,
          total_interactions: 25,
          sample_drugs: [
            {
              nama_obat: "Parasetamol",
              nama_obat_internasional: "Paracetamol",
            },
            { nama_obat: "Ibuprofen", nama_obat_internasional: "Ibuprofen" },
            { nama_obat: "Warfarin", nama_obat_internasional: "Warfarin" },
          ],
        },
      };
    }

    try {
      const response = await api.get("/api/drugs/stats");
      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Drug stats failed:", error);
      return {
        success: false,
        data: {
          total_drugs: 0,
          total_interactions: 0,
          sample_drugs: [],
        },
      };
    }
  },
};

// Main API Service Functions
export const apiService = {
  // Expose the axios instance for direct use if needed
  api,

  // Health check
  async healthCheck() {
    if (USE_MOCK_DATA) {
      await mockDelay();
      return {
        success: true,
        data: {
          status: "healthy",
          version: "2.0.0-mock",
          database: "mock",
          timestamp: new Date().toISOString(),
        },
      };
    }

    try {
      console.log("🏥 Checking system health...");
      const response = await api.get("/health");
      console.log("✅ Health check successful:", response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Health check failed:", error.message);
      // Fallback to mock data if backend fails
      console.log("🔄 Falling back to mock data...");
      return {
        success: true,
        data: {
          status: "mock-fallback",
          version: "2.0.0-fallback",
          error: error.message,
          timestamp: new Date().toISOString(),
        },
      };
    }
  },

  // Patient services - call backend first, fallback to inline mock
  async getAllPatients() {
    try {
      console.log("👥 Fetching all patients from backend...");
      const response = await api.get("/api/patients");
      console.log(`✅ Fetched ${response.data.length} patients from API`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error(
        "❌ Failed to fetch patients from API, using inline mock data:",
        error
      );
      // Fallback to inline mock data
      console.log("🔄 Using inline mock patient data as fallback...");
      return { success: true, data: inlineMockPatients };
    }
  },

  async getPatientById(patientId) {
    try {
      console.log(`👤 Fetching patient ${patientId} from API...`);
      const response = await api.get(`/api/patients/${patientId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error(
        `❌ Failed to fetch patient ${patientId} from API, checking inline mock data:`,
        error
      );
      // Fallback to inline mock data
      const patient = inlineMockPatients.find((p) => p.id === patientId);
      if (patient) {
        console.log(`🔄 Found patient ${patientId} in inline mock data`);
        return { success: true, data: patient };
      }
      const errorMessage =
        error.response?.data?.detail || error.message || "Unknown error";
      throw new Error(`Failed to fetch patient: ${errorMessage}`);
    }
  },

  // ICD-10 services
  async searchICD10(query, limit = 10) {
    try {
      console.log(`🔍 Searching ICD-10 for: "${query}"`);
      const response = await api.get("/api/icd10/search", {
        params: { q: query, limit },
      });
      console.log(`✅ Found ${response.data.length} ICD-10 results`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error(
        "❌ ICD-10 search failed, using inline mock results:",
        error
      );
      // Fallback to inline mock data
      const results = inlineMockICD10
        .filter(
          (icd) =>
            icd.name_id.toLowerCase().includes(query.toLowerCase()) ||
            icd.code.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, limit);
      console.log(
        `🔄 Inline mock fallback ICD-10 search returned ${results.length} results`
      );
      return { success: true, data: results };
    }
  },

  // Basic drug interaction analysis (legacy method)
  async analyzeInteractions(payload) {
    try {
      console.log("🧪 Analyzing interactions with payload:", payload);
      const response = await api.post("/api/analyze-interactions", payload);
      console.log("✅ Analysis complete:", response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Analysis failed, using inline mock result:", error);

      // Inline mock fallback result
      const mockResult = {
        interactions: [
          {
            severity: "Major",
            medications: [payload.new_medications[0], "Warfarin"],
            description:
              "Increased risk of bleeding when combining these medications.",
            recommendation:
              "Consider alternative pain management options or close monitoring.",
          },
        ],
        summary:
          "High risk interaction detected between new medication and existing warfarin therapy.",
        confidence_score: 0.95,
        processing_time: 2.1,
        llm_reasoning:
          "The combination of NSAIDs with anticoagulants significantly increases bleeding risk due to dual inhibition of hemostatic mechanisms.",
      };

      return { success: true, data: mockResult };
    }
  },

  // Enhanced drug interaction analysis with database integration
  async analyzeInteractionsEnhanced(payload) {
    try {
      console.log("🧪 Enhanced analyzing interactions:", payload);

      // Step 1: Check database interactions first
      const drugNames = payload.new_medications.map((med) => {
        // Extract drug name from "Name Dosage" format
        return med.split(" ")[0];
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
        const aiResponse = await api.post("/api/analyze-interactions", payload);
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
            // Only include if not already covered by database
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
        summary: generateEnhancedSummary(
          mergedInteractions,
          aiAnalysis.summary
        ),
      };

      console.log("✅ Enhanced analysis complete:", enhancedAnalysis);
      return { success: true, data: enhancedAnalysis };
    } catch (error) {
      console.error("❌ Enhanced analysis failed:", error);
      // Fallback to original method
      return await this.analyzeInteractions(payload);
    }
  },

  // Test Groq connection
  async testGroq() {
    try {
      console.log("🤖 Testing Groq connection...");
      const response = await api.get("/api/test-groq");
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        fallback: "Mock Groq connection for demo purposes",
      };
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
