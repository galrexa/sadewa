// src/services/drugService.js - Enhanced with complete database integration
import { apiService } from "./api";

export const drugService = {
  // Search drugs in database with autocomplete
  async searchDrugs(query, limit = 10) {
    try {
      console.log("🔍 Searching drugs:", { query, limit });

      if (!query || query.length < 1) {
        return { success: true, data: [] };
      }

      const response = await apiService.api.get("/api/drugs/search", {
        params: {
          q: query.trim(),
          limit: limit,
        },
      });

      console.log("✅ Drug search result:", response.data);

      return {
        success: true,
        data: response.data.drugs || [],
      };
    } catch (error) {
      console.error("❌ Drug search failed:", error);

      // Fallback to mock data for development
      const mockDrugs = [
        {
          id: 1,
          nama_obat: "Paracetamol",
          nama_obat_internasional: "Acetaminophen",
          is_active: true,
        },
        {
          id: 2,
          nama_obat: "Ibuprofen",
          nama_obat_internasional: "Ibuprofen",
          is_active: true,
        },
      ].filter(
        (drug) =>
          drug.nama_obat.toLowerCase().includes(query.toLowerCase()) ||
          drug.nama_obat_internasional
            .toLowerCase()
            .includes(query.toLowerCase())
      );

      return {
        success: true,
        data: mockDrugs,
      };
    }
  },

  // Get drug by exact name
  async getDrugByName(drugName) {
    try {
      console.log("🔍 Getting drug by name:", drugName);

      const response = await apiService.api.get("/api/drugs/by-name", {
        params: { name: drugName.trim() },
      });

      return {
        success: true,
        data: response.data.drug,
      };
    } catch (error) {
      console.error("❌ Get drug by name failed:", error);
      return { success: false, data: null };
    }
  },

  // Validate if drug exists in database
  async validateDrug(drugName) {
    try {
      const result = await this.searchDrugs(drugName, 1);
      if (result.success && result.data.length > 0) {
        // Check for exact match
        const exactMatch = result.data.find(
          (drug) =>
            drug.nama_obat.toLowerCase() === drugName.toLowerCase() ||
            drug.nama_obat_internasional.toLowerCase() ===
              drugName.toLowerCase()
        );

        return {
          success: true,
          isValid: !!exactMatch,
          suggestion: result.data[0], // Best match
          allMatches: result.data,
        };
      }

      return { success: true, isValid: false, suggestion: null };
    } catch (error) {
      console.error("❌ Drug validation failed:", error);
      return { success: false, isValid: false, suggestion: null };
    }
  },

  // Check drug-drug interactions
  async checkDrugInteractions(drugNames = []) {
    try {
      console.log("🔍 Checking drug interactions:", drugNames);

      if (!drugNames || drugNames.length < 2) {
        return {
          success: true,
          data: {
            input_drugs: drugNames,
            interactions_found: 0,
            interactions: [],
          },
        };
      }

      const drugNamesStr = drugNames.join(",");
      const response = await apiService.api.get(
        "/api/drugs/check-interactions",
        {
          params: { drug_names: drugNamesStr },
        }
      );

      console.log("✅ Drug interaction result:", response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Drug interaction check failed:", error);

      // Enhanced fallback with more interaction patterns
      const interactions = this.generateMockInteractions(drugNames);

      return {
        success: true,
        data: {
          input_drugs: drugNames,
          interactions_found: interactions.length,
          interactions: interactions,
          source: "fallback", // Indicate this is fallback data
        },
      };
    }
  },

  // Generate mock interactions for fallback (enhanced)
  generateMockInteractions(drugNames) {
    const interactions = [];
    const drugNamesLower = drugNames.map((d) => d.toLowerCase());

    // Define interaction patterns
    const interactionPatterns = [
      {
        drugs: ["warfarin", "ibuprofen"],
        severity: "Major",
        description: "Increased bleeding risk with concurrent use",
        recommendation:
          "Avoid concurrent use. Consider paracetamol as alternative.",
      },
      {
        drugs: ["warfarin", "aspirin"],
        severity: "Major",
        description: "Significantly increased bleeding risk",
        recommendation: "Avoid concurrent use unless closely monitored.",
      },
      {
        drugs: ["clopidogrel", "omeprazole"],
        severity: "Moderate",
        description: "Omeprazole may reduce effectiveness of Clopidogrel",
        recommendation: "Consider alternative PPI or H2 blocker.",
      },
      {
        drugs: ["metformin", "contrast"],
        severity: "Major",
        description: "Risk of lactic acidosis with iodinated contrast",
        recommendation: "Discontinue metformin before contrast procedures.",
      },
      {
        drugs: ["digoxin", "furosemide"],
        severity: "Moderate",
        description: "Increased digoxin levels due to electrolyte changes",
        recommendation: "Monitor digoxin levels and electrolytes closely.",
      },
      {
        drugs: ["simvastatin", "amlodipine"],
        severity: "Moderate",
        description: "Increased statin levels, risk of myopathy",
        recommendation: "Limit simvastatin dose to 20mg daily.",
      },
    ];

    // Check for interactions
    for (const pattern of interactionPatterns) {
      const hasAllDrugs = pattern.drugs.every((drug) =>
        drugNamesLower.some((inputDrug) => inputDrug.includes(drug))
      );

      if (hasAllDrugs) {
        // Find the actual drug names that match
        const matchedDrugs = pattern.drugs.map((patternDrug) => {
          const matchedInput = drugNames.find((inputDrug) =>
            inputDrug.toLowerCase().includes(patternDrug)
          );
          return matchedInput || patternDrug;
        });

        interactions.push({
          drug_a: matchedDrugs[0],
          drug_b: matchedDrugs[1],
          severity: pattern.severity,
          description: pattern.description,
          recommendation: pattern.recommendation,
          source: "pattern_matching",
        });
      }
    }

    // Add generic NSAID interactions
    const nsaids = ["ibuprofen", "diclofenac", "naproxen", "celecoxib"];
    const hasNSAID = drugNamesLower.some((drug) =>
      nsaids.some((nsaid) => drug.includes(nsaid))
    );
    const hasAnticoagulant = drugNamesLower.some((drug) =>
      ["warfarin", "heparin", "rivaroxaban", "apixaban"].some((anticoag) =>
        drug.includes(anticoag)
      )
    );

    if (hasNSAID && hasAnticoagulant && !interactions.length) {
      interactions.push({
        drug_a: "NSAID",
        drug_b: "Anticoagulant",
        severity: "Major",
        description: "Increased bleeding risk with concurrent use",
        recommendation:
          "Avoid concurrent use. Consider paracetamol as alternative.",
        source: "category_matching",
      });
    }

    return interactions;
  },

  // Get popular/common drugs
  async getPopularDrugs(limit = 10) {
    try {
      console.log("🔍 Getting popular drugs");

      const response = await apiService.api.get("/api/drugs/popular", {
        params: { limit },
      });

      return { success: true, data: response.data.drugs || [] };
    } catch (error) {
      console.error("❌ Get popular drugs failed:", error);

      // Return common Indonesian medications as fallback
      const commonDrugs = [
        { nama_obat: "Paracetamol", nama_obat_internasional: "Acetaminophen" },
        { nama_obat: "Ibuprofen", nama_obat_internasional: "Ibuprofen" },
        { nama_obat: "Amoxicillin", nama_obat_internasional: "Amoxicillin" },
        { nama_obat: "Omeprazole", nama_obat_internasional: "Omeprazole" },
        { nama_obat: "Metformin", nama_obat_internasional: "Metformin" },
        { nama_obat: "Amlodipine", nama_obat_internasional: "Amlodipine" },
        { nama_obat: "Simvastatin", nama_obat_internasional: "Simvastatin" },
        { nama_obat: "Losartan", nama_obat_internasional: "Losartan" },
        { nama_obat: "Atorvastatin", nama_obat_internasional: "Atorvastatin" },
        { nama_obat: "Aspirin", nama_obat_internasional: "Aspirin" },
      ];

      return { success: true, data: commonDrugs.slice(0, limit) };
    }
  },

  // Get drug database statistics
  async getDrugStats() {
    try {
      console.log("📊 Getting drug statistics");

      const response = await apiService.api.get("/api/drugs/stats");
      console.log("✅ Drug stats:", response.data);

      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Drug stats failed:", error);
      return {
        success: false,
        data: {
          total_drugs: 0,
          active_drugs: 0,
          sample_drugs: [],
          database_status: "unavailable",
        },
      };
    }
  },

  // Advanced drug search with filters
  async searchDrugsAdvanced(options = {}) {
    try {
      const {
        query = "",
        limit = 10,
        includeInactive = false,
        searchInternational = true,
      } = options;

      console.log("🔍 Advanced drug search:", options);

      const params = {
        q: query.trim(),
        limit,
        include_inactive: includeInactive,
        search_international: searchInternational,
      };

      const response = await apiService.api.get("/api/drugs/search/advanced", {
        params,
      });

      return {
        success: true,
        data: {
          drugs: response.data.drugs || [],
          total: response.data.total || 0,
          query_time: response.data.query_time || 0,
        },
      };
    } catch (error) {
      console.error("❌ Advanced drug search failed:", error);

      // Fallback to basic search
      return await this.searchDrugs(options.query, options.limit);
    }
  },

  // Batch validate multiple drugs
  async validateMultipleDrugs(drugNames = []) {
    try {
      console.log("🔍 Batch validating drugs:", drugNames);

      const results = await Promise.all(
        drugNames.map(async (drugName) => {
          const validation = await this.validateDrug(drugName);
          return {
            drugName,
            ...validation,
          };
        })
      );

      const validDrugs = results.filter((r) => r.isValid);
      const invalidDrugs = results.filter((r) => !r.isValid);

      return {
        success: true,
        data: {
          total: drugNames.length,
          valid: validDrugs.length,
          invalid: invalidDrugs.length,
          results: results,
          validDrugs: validDrugs,
          invalidDrugs: invalidDrugs,
        },
      };
    } catch (error) {
      console.error("❌ Batch drug validation failed:", error);
      return { success: false, data: null };
    }
  },

  // Get drug interactions with patient conditions
  async checkDrugConditionInteractions(drugNames = [], icdCodes = []) {
    try {
      console.log("🔍 Checking drug-condition interactions:", {
        drugNames,
        icdCodes,
      });

      const params = {
        drugs: drugNames.join(","),
        conditions: icdCodes.join(","),
      };

      const response = await apiService.api.get("/api/analyze-interactions", {
        params,
      });

      return { success: true, data: response.data };
    } catch (error) {
      console.error("❌ Drug-condition interaction check failed:", error);

      // Enhanced fallback with condition-specific warnings
      const warnings = this.generateConditionWarnings(drugNames, icdCodes);

      return {
        success: true,
        data: {
          drug_interactions: this.generateMockInteractions(drugNames),
          condition_warnings: warnings,
          analysis_type: "fallback",
        },
      };
    }
  },

  // Generate condition-specific warnings
  generateConditionWarnings(drugNames, icdCodes) {
    const warnings = [];
    const drugNamesLower = drugNames.map((d) => d.toLowerCase());

    // Define drug-condition contraindications
    const contraindications = [
      {
        drugs: ["metformin"],
        conditions: ["N18", "N19"], // Kidney disease
        severity: "Major",
        warning:
          "Metformin contraindicated in severe kidney disease due to lactic acidosis risk",
      },
      {
        drugs: ["nsaid", "ibuprofen", "diclofenac"],
        conditions: ["N18", "I50"], // Kidney disease, Heart failure
        severity: "Major",
        warning: "NSAIDs may worsen kidney function and heart failure",
      },
      {
        drugs: ["warfarin"],
        conditions: ["K92.2"], // GI bleeding
        severity: "Major",
        warning: "Anticoagulants contraindicated in active GI bleeding",
      },
      {
        drugs: ["aspirin"],
        conditions: ["J45"], // Asthma
        severity: "Moderate",
        warning: "Aspirin may trigger bronchospasm in aspirin-sensitive asthma",
      },
    ];

    // Check for contraindications
    for (const contra of contraindications) {
      const hasDrug = contra.drugs.some((drug) =>
        drugNamesLower.some((inputDrug) => inputDrug.includes(drug))
      );

      const hasCondition = contra.conditions.some((condition) =>
        icdCodes.some((icd) => icd.startsWith(condition))
      );

      if (hasDrug && hasCondition) {
        warnings.push({
          type: "contraindication",
          severity: contra.severity,
          message: contra.warning,
          drugs: contra.drugs,
          conditions: contra.conditions,
        });
      }
    }

    return warnings;
  },

  // Format drug name for display
  formatDrugName(drug) {
    if (!drug) return "";

    if (typeof drug === "string") {
      return drug;
    }

    // If drug object has both names, show both
    if (drug.nama_obat && drug.nama_obat_internasional) {
      if (
        drug.nama_obat.toLowerCase() ===
        drug.nama_obat_internasional.toLowerCase()
      ) {
        return drug.nama_obat;
      }
      return `${drug.nama_obat} (${drug.nama_obat_internasional})`;
    }

    return drug.nama_obat || drug.nama_obat_internasional || "Unknown drug";
  },

  // Get drug suggestions based on partial input
  async getDrugSuggestions(partialName, limit = 5) {
    try {
      if (!partialName || partialName.length < 2) {
        return { success: true, data: [] };
      }

      const result = await this.searchDrugs(partialName, limit);

      if (result.success) {
        // Sort by relevance (exact matches first)
        const suggestions = result.data.sort((a, b) => {
          const aName = a.nama_obat.toLowerCase();
          const bName = b.nama_obat.toLowerCase();
          const searchTerm = partialName.toLowerCase();

          // Exact matches first
          if (aName === searchTerm) return -1;
          if (bName === searchTerm) return 1;

          // Starts with search term
          if (aName.startsWith(searchTerm) && !bName.startsWith(searchTerm))
            return -1;
          if (bName.startsWith(searchTerm) && !aName.startsWith(searchTerm))
            return 1;

          // Alphabetical order
          return aName.localeCompare(bName);
        });

        return { success: true, data: suggestions };
      }

      return result;
    } catch (error) {
      console.error("❌ Get drug suggestions failed:", error);
      return { success: false, data: [] };
    }
  },
};
