// src/components/InteractionResults.jsx
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
  className = "",
}) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastAnalyzedAt, setLastAnalyzedAt] = useState(null);

  // Auto-analyze when data changes
  useEffect(() => {
    if (autoAnalyze && patient && medications.length > 0) {
      handleAnalyze();
    }
  }, [patient, diagnoses, medications, autoAnalyze]);

  const handleAnalyze = async () => {
    if (!patient || medications.length === 0) {
      setError("Please select a patient and add at least one medication");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        patient_id: patient.id,
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
        return "status-major";
      case "moderate":
        return "status-moderate";
      case "minor":
        return "status-minor";
      default:
        return "status-safe";
    }
  };

  const getOverallRiskLevel = () => {
    if (!analysis?.interactions) return "safe";

    const interactions = analysis.interactions;
    if (interactions.some((i) => i.severity === "Major")) return "major";
    if (interactions.some((i) => i.severity === "Moderate")) return "moderate";
    if (interactions.some((i) => i.severity === "Minor")) return "minor";
    return "safe";
  };

  const getOverallRiskColor = () => {
    const risk = getOverallRiskLevel();
    switch (risk) {
      case "major":
        return "border-red-200 bg-red-50";
      case "moderate":
        return "border-yellow-200 bg-yellow-50";
      case "minor":
        return "border-blue-200 bg-blue-50";
      default:
        return "border-green-200 bg-green-50";
    }
  };

  if (!patient) {
    return (
      <div className={`card ${className}`}>
        <div className="text-center py-8">
          <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">Select a patient to begin analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Brain className="w-5 h-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">
            Interaction Analysis
          </h2>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading || !patient || medications.length === 0}
          className="btn-primary flex items-center text-sm disabled:opacity-50 disabled:cursor-not-allowed"
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
          <div className="inline-flex items-center justify-center w-16 h-16 mb-4 bg-primary-100 rounded-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
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
                Overall Risk Assessment
              </h3>
            </div>
            <p className="text-sm text-gray-700">
              {analysis.summary ||
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
          {analysis.interactions && analysis.interactions.length > 0 ? (
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">
                Drug Interactions Found ({analysis.interactions.length})
              </h3>
              <div className="space-y-3">
                {analysis.interactions.map((interaction, index) => (
                  <div
                    key={index}
                    className="p-4 border border-gray-200 rounded-lg bg-white"
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0 mr-3 mt-0.5">
                        {getSeverityIcon(interaction.severity)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <span
                            className={`${getSeverityBadgeClass(
                              interaction.severity
                            )} mr-2`}
                          >
                            {interaction.severity?.toUpperCase() || "UNKNOWN"}
                          </span>
                          <span className="font-medium text-gray-900">
                            {interaction.medications?.join(" + ") ||
                              "Drug Interaction"}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">
                          {interaction.description || interaction.warning}
                        </p>
                        {interaction.recommendation && (
                          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                            <p className="text-sm text-blue-800">
                              <strong>Recommendation:</strong>{" "}
                              {interaction.recommendation}
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

          {/* AI Reasoning */}
          {analysis.llm_reasoning && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                <Brain className="w-4 h-4 mr-2" />
                AI Clinical Reasoning
              </h4>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {analysis.llm_reasoning}
              </p>
            </div>
          )}

          {/* Performance Info */}
          {analysis.processing_time && (
            <div className="text-xs text-gray-500 flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              Analysis completed in {analysis.processing_time.toFixed(2)}s
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
