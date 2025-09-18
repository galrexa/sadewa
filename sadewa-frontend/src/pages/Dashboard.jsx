// sadewa-frontend/src/pages/Dashboard.jsx - UPDATED
import React, { useState, useEffect } from "react";

// Existing components
import PatientSelector from "../components/PatientSelector";
import DiagnosisSearch from "../components/DiagnosisSearch";
import MedicationInput from "../components/MedicationInput";
import InteractionResults from "../components/InteractionResults";

// New components
import Navigation from "../components/Navigation";
import PatientRegistrationForm from "../components/PatientRegistrationForm";
import PatientList from "../components/PatientList";
import SaveDiagnosisButton from "../components/SaveDiagnosisButton";

const Dashboard = () => {
  // Navigation state
  const [activeTab, setActiveTab] = useState("dashboard");
  const [patientCount, setPatientCount] = useState(0);

  // Existing states
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedDiagnosis, setSelectedDiagnosis] = useState(null);
  const [medications, setMedications] = useState([]);
  const [interactionResults, setInteractionResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // New states
  const [patients, setPatients] = useState([]);

  // Load patient count
  useEffect(() => {
    const fetchPatientCount = async () => {
      try {
        const response = await fetch("/api/patients/?limit=1");
        if (response.ok) {
          const data = await response.json();
          setPatientCount(data.total);
        }
      } catch (error) {
        console.error("Failed to fetch patient count:", error);
      }
    };

    fetchPatientCount();
  }, [activeTab]);

  // Existing handlers
  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
  };

  const handleDiagnosisSelect = (diagnosis) => {
    setSelectedDiagnosis(diagnosis);
  };

  const handleMedicationChange = (newMedications) => {
    setMedications(newMedications);
    // Clear previous results when medications change
    setInteractionResults(null);
  };

  const handleAnalyze = async () => {
    if (medications.length === 0) return;

    setIsAnalyzing(true);
    try {
      // Call your existing interaction analysis API
      const response = await fetch("/api/analyze-interactions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patient_id: selectedPatient?.id || "unknown",
          new_medications: medications,
          notes: selectedDiagnosis?.name_id || "",
        }),
      });

      if (response.ok) {
        const results = await response.json();
        setInteractionResults(results);
      }
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // New handlers
  const handleSaveDiagnosisSuccess = (savedRecord) => {
    alert("Diagnosis berhasil disimpan ke rekam medis!");
    // Optionally refresh patient data or navigate
    if (selectedPatient) {
      setActiveTab("patient-list");
    }
  };

  const handlePatientRegistrationSuccess = (newPatient) => {
    setPatientCount((prev) => prev + 1);
    setActiveTab("patient-list");
  };

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
  };

  // Render different content based on active tab
  const renderContent = () => {
    switch (activeTab) {
      case "patient-registration":
        return (
          <div className="max-w-2xl mx-auto">
            <PatientRegistrationForm
              onSuccess={handlePatientRegistrationSuccess}
              onCancel={() => setActiveTab("dashboard")}
            />
          </div>
        );

      case "patient-list":
        return (
          <PatientList
            onSelectPatient={(patient) => {
              setSelectedPatient(patient);
              setActiveTab("dashboard");
            }}
            onAddPatient={() => setActiveTab("patient-registration")}
          />
        );

      case "drug-analysis":
      case "dashboard":
      default:
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Analisis Interaksi Obat
              </h1>
              <p className="text-gray-600">
                Sistem cerdas untuk menganalisis interaksi obat dan memberikan
                peringatan keamanan
              </p>
            </div>

            {/* Main Analysis Flow */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Left Column - Input */}
              <div className="space-y-6">
                {/* Patient Selection */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    1. Pilih Pasien
                  </h2>
                  <PatientSelector
                    selectedPatient={selectedPatient}
                    onPatientSelect={handlePatientSelect}
                  />
                  {selectedPatient && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        ✓ Pasien: <strong>{selectedPatient.name}</strong> (
                        {selectedPatient.age} tahun)
                      </p>
                    </div>
                  )}
                </div>

                {/* Diagnosis Search */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    2. Cari Diagnosis (ICD-10)
                  </h2>
                  <DiagnosisSearch
                    selectedDiagnosis={selectedDiagnosis}
                    onDiagnosisSelect={handleDiagnosisSelect}
                  />
                  {selectedDiagnosis && (
                    <div className="mt-4 p-3 bg-green-50 rounded-lg">
                      <p className="text-sm text-green-800">
                        ✓ Diagnosis: <strong>{selectedDiagnosis.code}</strong> -{" "}
                        {selectedDiagnosis.name_id}
                      </p>
                    </div>
                  )}
                </div>

                {/* Medication Input */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    3. Input Obat
                  </h2>
                  <MedicationInput
                    medications={medications}
                    onMedicationChange={handleMedicationChange}
                  />

                  {/* Action Buttons */}
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={handleAnalyze}
                      disabled={medications.length === 0 || isAnalyzing}
                      className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                    >
                      {isAnalyzing ? "Menganalisis..." : "Analisis Interaksi"}
                    </button>

                    {interactionResults && (
                      <SaveDiagnosisButton
                        diagnosisData={selectedDiagnosis}
                        medications={medications}
                        interactionResults={interactionResults}
                        onSuccess={handleSaveDiagnosisSuccess}
                        disabled={!selectedPatient}
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column - Results */}
              <div className="space-y-6">
                {/* Interaction Results */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    4. Hasil Analisis
                  </h2>

                  {!interactionResults && (
                    <div className="text-center py-12 text-gray-500">
                      <p>Hasil analisis akan muncul di sini</p>
                      <p className="text-sm">
                        Tambahkan obat dan klik "Analisis Interaksi"
                      </p>
                    </div>
                  )}

                  {interactionResults && (
                    <InteractionResults
                      results={interactionResults}
                      medications={medications}
                    />
                  )}
                </div>

                {/* Quick Stats */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Statistik Cepat
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Pasien:</span>
                      <span className="font-semibold">{patientCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Obat Dipilih:</span>
                      <span className="font-semibold">
                        {medications.length}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">
                        Interaksi Ditemukan:
                      </span>
                      <span className="font-semibold">
                        {interactionResults?.interactions_found || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Navigation */}
      <Navigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        patientCount={patientCount}
      />

      {/* Main Content */}
      <div className="flex-1 md:ml-0">
        <div className="p-6">{renderContent()}</div>
      </div>
    </div>
  );
};

export default Dashboard;
