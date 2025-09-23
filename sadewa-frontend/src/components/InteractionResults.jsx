// src/components/InteractionResults.jsx - PERBAIKAN UNTUK DISPLAY RESULTS
import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Brain,
  Clock,
  RefreshCw,
  Zap,
  Target,
} from "lucide-react";
import { apiService } from "../services/api";

const InteractionResults = ({
  patient,
  diagnoses = [],
  medications = [],
  autoAnalyze = true,
  analysis: externalAnalysis = null, // ✅ TAMBAHKAN prop untuk results dari luar
  className = "",
}) => {
  const [analysis, setAnalysis] = useState(externalAnalysis);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastAnalyzedAt, setLastAnalyzedAt] = useState(null);

  // ✅ UPDATE: Gunakan external analysis jika ada
  useEffect(() => {
    if (externalAnalysis) {
      setAnalysis(externalAnalysis);
      setLastAnalyzedAt(new Date());
      return; // Jangan lakukan auto-analyze jika sudah ada hasil
    }

    // Auto-analyze hanya jika tidak ada external analysis
    if (autoAnalyze && patient && medications.length > 0) {
      handleAnalyze();
    }
  }, [patient, diagnoses, medications, autoAnalyze, externalAnalysis]);

  const handleAnalyze = async () => {
    if (!patient || medications.length === 0) {
      setError("Please select a patient and add at least one medication");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        patient_id: selectedPatient?.no_rm,
        new_medications: medications.map((med) => `${med.name} ${med.dosage}`),
        diagnoses: diagnoses.map((d) => d.code),
        notes: `Analysis for ${patient.name} (${patient.age}y, ${patient.gender})`,
      };

      console.log("🔍 Analyzing interactions with payload:", payload);

      const result = await apiService.analyzeInteractions(payload);
      setAnalysis(result.data);
      setLastAnalyzedAt(new Date());
    } catch (err) {
      setError(err.message);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case "major":
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case "moderate":
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case "minor":
        return <Info className="w-5 h-5 text-blue-500" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
  };

  const getSeverityBadgeClass = (severity) => {
    switch (severity?.toLowerCase()) {
      case "major":
        return "bg-red-100 text-red-800 border-red-200";
      case "moderate":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "minor":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-green-100 text-green-800 border-green-200";
    }
  };

  const getOverallRiskLevel = () => {
    if (!analysis?.warnings) return "safe";

    const warnings = analysis.warnings;
    if (warnings.some((w) => w.severity === "MAJOR")) return "major";
    if (warnings.some((w) => w.severity === "MODERATE")) return "moderate";
    if (warnings.some((w) => w.severity === "MINOR")) return "minor";
    return "safe";
  };

  const getOverallRiskColor = () => {
    const riskLevel = getOverallRiskLevel();
    switch (riskLevel) {
      case "major":
        return "border-red-300 bg-red-50";
      case "moderate":
        return "border-yellow-300 bg-yellow-50";
      case "minor":
        return "border-blue-300 bg-blue-50";
      default:
        return "border-green-300 bg-green-50";
    }
  };

  return (
    <div className={`${className}`}>
      {/* Header with Manual Analyze Button - Hanya tampil jika tidak ada external analysis */}
      {!externalAnalysis && (
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Interaction Analysis
          </h2>
          <button
            onClick={handleAnalyze}
            disabled={loading || !patient || medications.length === 0}
            className="flex items-center px-3 py-2 text-sm bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg transition-colors"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analyzing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-1" />
                {analysis ? "Re-analyze" : "Analyze"}
              </>
            )}
          </button>
        </div>
      )}

      {/* Analysis Status */}
      {lastAnalyzedAt && (
        <div className="flex items-center mb-4 text-sm text-gray-500">
          <Clock className="w-4 h-4 mr-1" />
          Last analyzed: {lastAnalyzedAt.toLocaleTimeString()}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 border border-red-200 rounded-lg bg-red-50">
          <div className="flex items-center text-red-600">
            <AlertCircle className="w-5 h-5 mr-2" />
            <div>
              <p className="font-medium">Analysis Error</p>
              <p className="text-sm text-red-500">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-flex items-center justify-center w-16 h-16 mb-4 bg-blue-100 rounded-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
          <p className="text-gray-600 font-medium">
            Analyzing drug interactions...
          </p>
          <p className="text-sm text-gray-500 mt-1">
            This may take a few seconds
          </p>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && !loading && (
        <div className="space-y-6">
          {/* Overall Risk Assessment */}
          <div className={`p-4 rounded-lg border-2 ${getOverallRiskColor()}`}>
            <div className="flex items-center mb-2">
              {getSeverityIcon(getOverallRiskLevel())}
              <h3 className="ml-2 font-semibold text-gray-900">
                Overall Risk Assessment:{" "}
                {analysis.overall_risk_level || "UNKNOWN"}
              </h3>
            </div>
            <p className="text-sm text-gray-700">
              {analysis.llm_reasoning ||
                `Based on current medications and patient conditions, the overall interaction risk is ${getOverallRiskLevel()}.`}
            </p>
            {analysis.confidence_score && (
              <div className="mt-2 flex items-center text-xs text-gray-600">
                <Zap className="w-3 h-3 mr-1" />
                Confidence: {Math.round(analysis.confidence_score * 100)}%
              </div>
            )}
          </div>

          {/* Interaction Warnings */}
          {analysis.warnings && analysis.warnings.length > 0 ? (
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">
                Drug Interaction Warnings ({analysis.warnings.length})
              </h3>
              <div className="space-y-3">
                {analysis.warnings.map((warning, index) => (
                  <div
                    key={index}
                    className="p-4 border border-gray-200 rounded-lg bg-white"
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0 mr-3 mt-0.5">
                        {getSeverityIcon(warning.severity)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityBadgeClass(
                              warning.severity
                            )} mr-2`}
                          >
                            {warning.severity?.toUpperCase() || "UNKNOWN"}
                          </span>
                          <span className="font-medium text-gray-900">
                            {warning.drugs_involved?.join(" + ") ||
                              "Drug Interaction"}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">
                          {warning.description}
                        </p>
                        {warning.clinical_significance && (
                          <p className="text-sm text-gray-600 mb-2">
                            <strong>Clinical Impact:</strong>{" "}
                            {warning.clinical_significance}
                          </p>
                        )}
                        {warning.recommendation && (
                          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                            <p className="text-sm text-blue-800">
                              <strong>Recommendation:</strong>{" "}
                              {warning.recommendation}
                            </p>
                          </div>
                        )}
                        {warning.monitoring_required && (
                          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                            <p className="text-xs text-yellow-800">
                              <strong>Monitoring:</strong>{" "}
                              {warning.monitoring_required}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-6 bg-green-50 border border-green-200 rounded-lg text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p className="font-medium text-green-900">
                No Major Interactions Detected
              </p>
              <p className="text-sm text-green-700">
                The proposed medications appear to be safe with current
                medications and conditions.
              </p>
            </div>
          )}

          {/* Contraindications */}
          {analysis.contraindications &&
            analysis.contraindications.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">
                  Contraindications ({analysis.contraindications.length})
                </h3>
                <div className="space-y-2">
                  {analysis.contraindications.map((contra, index) => (
                    <div
                      key={index}
                      className="p-3 bg-red-50 border border-red-200 rounded-lg"
                    >
                      <div className="flex items-start">
                        <AlertTriangle className="w-4 h-4 text-red-500 mr-2 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm text-red-800">
                            <strong>{contra.drug}</strong> is contraindicated
                            with <strong>{contra.diagnosis}</strong>
                          </p>
                          <p className="text-xs text-red-600 mt-1">
                            {contra.reason}
                          </p>
                          {contra.alternative_suggested && (
                            <p className="text-xs text-red-600 mt-1">
                              <strong>Alternative:</strong>{" "}
                              {contra.alternative_suggested}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Dosing Adjustments */}
          {analysis.dosing_adjustments &&
            analysis.dosing_adjustments.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">
                  Dosing Adjustments ({analysis.dosing_adjustments.length})
                </h3>
                <div className="space-y-2">
                  {analysis.dosing_adjustments.map((adjustment, index) => (
                    <div
                      key={index}
                      className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                    >
                      <div className="flex items-start">
                        <Info className="w-4 h-4 text-yellow-600 mr-2 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm text-yellow-800">
                            <strong>{adjustment.drug}</strong> requires dose
                            adjustment
                          </p>
                          <p className="text-xs text-yellow-700 mt-1">
                            Standard: {adjustment.standard_dose} → Recommended:{" "}
                            {adjustment.recommended_dose}
                          </p>
                          <p className="text-xs text-yellow-600 mt-1">
                            {adjustment.reason}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Monitoring Plan */}
          {analysis.monitoring_plan && analysis.monitoring_plan.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">
                Monitoring Plan
              </h3>
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <ul className="space-y-1">
                  {analysis.monitoring_plan.map((item, index) => (
                    <li
                      key={index}
                      className="text-sm text-blue-800 flex items-start"
                    >
                      <span className="w-2 h-2 bg-blue-400 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Performance Info */}
          {analysis.processing_time && (
            <div className="text-xs text-gray-500 flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              Analysis completed in {analysis.processing_time}s
              {analysis.from_cache && " (cached result)"}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!analysis && !loading && !error && medications.length === 0 && (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <Target className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 font-medium">Ready for Analysis</p>
          <p className="text-sm text-gray-400 mt-1">
            Add medications to check for potential interactions
          </p>
        </div>
      )}
    </div>
  );
};

export default InteractionResults;
