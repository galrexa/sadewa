// src/pages/Dashboard.jsx
import React, { useState, useEffect } from "react";
import {
  Shield,
  Activity,
  Users,
  FileText,
  Pill,
  AlertTriangle,
  CheckCircle,
  Wifi,
  WifiOff,
} from "lucide-react";
import PatientSelector from "../components/PatientSelector";
import DiagnosisSearch from "../components/DiagnosisSearch";
import MedicationInput from "../components/MedicationInput";
import InteractionResults from "../components/InteractionResults";
import { apiService } from "../services/api";

const Dashboard = () => {
  // State management
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedDiagnoses, setSelectedDiagnoses] = useState([]);
  const [medications, setMedications] = useState([]);
  const [systemHealth, setSystemHealth] = useState({
    status: "unknown",
    loading: true,
  });

  // Check system health on component mount
  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const result = await apiService.healthCheck();
      setSystemHealth({
        status: result.success ? "healthy" : "error",
        loading: false,
        data: result.data,
      });
    } catch (error) {
      setSystemHealth({
        status: "error",
        loading: false,
        error: error.message,
      });
    }
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    // Reset other selections when patient changes
    setSelectedDiagnoses([]);
    setMedications([]);
  };

  const getQuickStats = () => {
    return {
      patient: selectedPatient ? 1 : 0,
      diagnoses: selectedDiagnoses.length,
      medications: medications.length,
      readyForAnalysis: selectedPatient && medications.length > 0,
    };
  };

  const stats = getQuickStats();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Title */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Shield className="w-8 h-8 text-primary-600" />
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-900">SADEWA</h1>
                <p className="text-sm text-gray-500">
                  Smart Assistant for Drug & Evidence Warning
                </p>
              </div>
            </div>

            {/* System Status */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                {systemHealth.loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                ) : systemHealth.status === "healthy" ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                <span className="ml-2 text-sm text-gray-600">
                  {systemHealth.loading
                    ? "Checking..."
                    : systemHealth.status === "healthy"
                    ? "System Online"
                    : "System Error"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Quick Stats Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Patient Status */}
            <div className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full mr-2 ${
                  stats.patient ? "bg-green-500" : "bg-gray-300"
                }`}
              ></div>
              <div>
                <p className="text-xs text-gray-500">Patient</p>
                <p className="font-medium text-gray-900">
                  {stats.patient ? "Selected" : "Not Selected"}
                </p>
              </div>
            </div>

            {/* Diagnoses Count */}
            <div className="flex items-center">
              <FileText className="w-4 h-4 text-primary-600 mr-2" />
              <div>
                <p className="text-xs text-gray-500">Diagnoses</p>
                <p className="font-medium text-gray-900">{stats.diagnoses}</p>
              </div>
            </div>

            {/* Medications Count */}
            <div className="flex items-center">
              <Pill className="w-4 h-4 text-primary-600 mr-2" />
              <div>
                <p className="text-xs text-gray-500">New Medications</p>
                <p className="font-medium text-gray-900">{stats.medications}</p>
              </div>
            </div>

            {/* Analysis Status */}
            <div className="flex items-center">
              {stats.readyForAnalysis ? (
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-yellow-500 mr-2" />
              )}
              <div>
                <p className="text-xs text-gray-500">Analysis</p>
                <p className="font-medium text-gray-900">
                  {stats.readyForAnalysis ? "Ready" : "Pending"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Input Components */}
          <div className="lg:col-span-2 space-y-8">
            {/* Patient Selection */}
            <PatientSelector
              selectedPatient={selectedPatient}
              onPatientSelect={handlePatientSelect}
            />

            {/* Diagnosis Search */}
            <DiagnosisSearch
              selectedDiagnoses={selectedDiagnoses}
              onDiagnosesChange={setSelectedDiagnoses}
            />

            {/* Medication Input */}
            <MedicationInput
              medications={medications}
              onMedicationsChange={setMedications}
            />
          </div>

          {/* Right Column - Analysis Results */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <InteractionResults
                patient={selectedPatient}
                diagnoses={selectedDiagnoses}
                medications={medications}
                autoAnalyze={true}
              />
            </div>
          </div>
        </div>

        {/* Patient Context Panel */}
        {selectedPatient && (
          <div className="mt-8">
            <div className="card">
              <div className="flex items-center mb-4">
                <Users className="w-5 h-5 text-primary-600 mr-2" />
                <h2 className="text-lg font-semibold text-gray-900">
                  Patient Context
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Patient Info */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">
                    Patient Information
                  </h3>
                  <div className="space-y-1 text-sm">
                    <p>
                      <span className="text-gray-500">ID:</span>{" "}
                      {selectedPatient.id}
                    </p>
                    <p>
                      <span className="text-gray-500">Age:</span>{" "}
                      {selectedPatient.age} years
                    </p>
                    <p>
                      <span className="text-gray-500">Gender:</span>{" "}
                      {selectedPatient.gender}
                    </p>
                    {selectedPatient.weight_kg && (
                      <p>
                        <span className="text-gray-500">Weight:</span>{" "}
                        {selectedPatient.weight_kg} kg
                      </p>
                    )}
                  </div>
                </div>

                {/* Current Medications */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">
                    Current Medications
                  </h3>
                  {selectedPatient.current_medications &&
                  selectedPatient.current_medications.length > 0 ? (
                    <div className="space-y-1">
                      {selectedPatient.current_medications.map((med, index) => (
                        <div
                          key={index}
                          className="text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded"
                        >
                          {med}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">
                      No current medications
                    </p>
                  )}
                </div>

                {/* Existing Diagnoses */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">
                    Existing Diagnoses
                  </h3>
                  {selectedPatient.diagnoses_text &&
                  selectedPatient.diagnoses_text.length > 0 ? (
                    <div className="space-y-1">
                      {selectedPatient.diagnoses_text.map(
                        (diagnosis, index) => (
                          <div
                            key={index}
                            className="text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded"
                          >
                            {diagnosis}
                          </div>
                        )
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">
                      No recorded diagnoses
                    </p>
                  )}
                </div>

                {/* Allergies */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Allergies</h3>
                  {selectedPatient.allergies &&
                  selectedPatient.allergies.length > 0 ? (
                    <div className="space-y-1">
                      {selectedPatient.allergies.map((allergy, index) => (
                        <div
                          key={index}
                          className="text-sm text-red-600 bg-red-50 px-2 py-1 rounded border border-red-200"
                        >
                          ⚠️ {allergy}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No known allergies</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Getting Started Guide */}
        {!selectedPatient && (
          <div className="mt-8">
            <div className="card border-primary-200 bg-primary-50">
              <div className="flex items-center mb-4">
                <Activity className="w-5 h-5 text-primary-600 mr-2" />
                <h2 className="text-lg font-semibold text-primary-900">
                  Getting Started
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Users className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="font-medium text-primary-900 mb-2">
                    1. Select Patient
                  </h3>
                  <p className="text-sm text-primary-700">
                    Choose from 10 dummy patients with different medical
                    conditions
                  </p>
                </div>

                <div className="text-center">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Pill className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="font-medium text-primary-900 mb-2">
                    2. Add Medications
                  </h3>
                  <p className="text-sm text-primary-700">
                    Input new medications to check for potential interactions
                  </p>
                </div>

                <div className="text-center">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Activity className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="font-medium text-primary-900 mb-2">
                    3. Review Analysis
                  </h3>
                  <p className="text-sm text-primary-700">
                    Get AI-powered warnings and clinical recommendations
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Shield className="w-5 h-5 text-primary-600 mr-2" />
              <p className="text-sm text-gray-600">
                SADEWA v2.0 - Powered by Groq AI & Meta Llama
              </p>
            </div>
            <p className="text-xs text-gray-500">
              Meta Hacktiv8 "Accelerate with Llama" Competition 2025
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
