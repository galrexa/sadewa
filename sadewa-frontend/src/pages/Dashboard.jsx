// sadewa-frontend/src/pages/Dashboard.jsx
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

import { apiService } from "../services/api";
import { useToast } from "../components/ToastNotification";

const Dashboard = () => {
  const toast = useToast();
  // Navigation state
  const [activeTab, setActiveTab] = useState("dashboard");
  const [patientCount, setPatientCount] = useState(0);

  // Existing states
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedDiagnosis, setSelectedDiagnosis] = useState(null);
  const [medications, setMedications] = useState([]);
  const [interactionResults, setInteractionResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRegistrationForm, setShowRegistrationForm] = useState(false);
  const [patientToEdit, setPatientToEdit] = useState(null);

  const [error, setError] = useState(null);

  // New states
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    const fetchPatientCount = async () => {
      try {
        const result = await apiService.getAllPatients();
        if (result.success) {
          setPatientCount(result.data.length);
        }
      } catch (error) {
        console.error("Failed to fetch patient count:", error);
        setPatientCount(0);
      }
    };

    fetchPatientCount();
  }, [activeTab]);

  // Existing handlers
  const handlePatientSelect = async (patient) => {
    console.log("🔄 Loading patient data:", patient);
    setSelectedPatient(patient);

    // Load current medications from database
    try {
      const result = await apiService.getCurrentMedications(
        patient.no_rm || patient.id
      );
      if (result.success && result.current_medications) {
        // Format medications for MedicationInput component
        const formattedMedications = result.current_medications.map((med) => ({
          id: med.id || Date.now() + Math.random(),
          name: med.name || med.medication_name,
          dosage: med.dosage || "",
          frequency: med.frequency || "",
          notes: med.notes || "",
        }));

        console.log("✅ Loaded medications:", formattedMedications);
        setMedications(formattedMedications);
      } else {
        console.log("ℹ️ No current medications found");
        setMedications([]);
      }
    } catch (error) {
      console.error("❌ Failed to load current medications:", error);
      setMedications([]); // Reset to empty if failed
    }
  };

  const handleAddPatient = () => {
    setShowRegistrationForm(true);
    setActiveTab("register");
  };

  const handleEditPatient = (patient) => {
    console.log("Setting patient to edit:", patient);
    setPatientToEdit(patient); // Simpan data pasien yang akan diedit
    setActiveTab("register"); // Pindah ke tab pendaftaran/edit
  };

  const handleRegistrationSuccess = (newPatient) => {
    setShowRegistrationForm(false);
    setPatientToEdit(null);
    setActiveTab("patients");
  };

  const handleRegistrationCancel = () => {
    setShowRegistrationForm(false);
    setPatientToEdit(null);
    setActiveTab("patients");
  };

  const handleDiagnosisSelect = (diagnosis) => {
    setSelectedDiagnosis(diagnosis);
  };

  const handleMedicationChange = (newMedications) => {
    setMedications(newMedications);
    setInteractionResults(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    console.log("DEBUG selectedPatient:", selectedPatient);
    console.log("DEBUG no_rm:", selectedPatient?.no_rm);
    console.log("DEBUG patient_code:", selectedPatient?.patient_code);
    console.log("DEBUG id:", selectedPatient?.id);

    if (medications.length === 0) {
      setError("Please add at least one medication");
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const payload = {
        patient_id:
          selectedPatient?.patient_code || selectedPatient?.no_rm || "unknown",
        new_medications: medications.map((med) => `${med.name} ${med.dosage}`),
        diagnoses: selectedDiagnosis ? [selectedDiagnosis.code] : [],
        notes: `Analysis for ${selectedPatient?.name || "Unknown Patient"} - ${
          selectedDiagnosis?.name_id || "No diagnosis"
        }`,
      };

      console.log("Analyzing interactions with payload:", payload);

      const result = await apiService.analyzeInteractions(payload);

      if (result.success) {
        setInteractionResults(result.data);
        console.log("Analysis successful:", result.data);
      } else {
        throw new Error(result.error || "Analysis failed");
      }
    } catch (error) {
      console.error("Analysis failed:", error);
      setError(error.message || "Failed to analyze interactions");
      setInteractionResults(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveDiagnosisSuccess = (savedRecord) => {
    toast.success("Diagnosis berhasil disimpan ke rekam medis!", {
      title: "Berhasil!",
      duration: 4000,
    });
    console.log("Saved record:", savedRecord);
    setSelectedPatient(null);
    setSelectedDiagnosis(null);
    setMedications([]);
    setInteractionResults(null);
    setError(null);
  };

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
  };

  const renderContent = () => {
    switch (activeTab) {
      case "patient-registration":
        return (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-6">
                Registrasi Pasien Baru
              </h1>
              <PatientRegistrationForm onSuccess={handleSaveDiagnosisSuccess} />
            </div>
          </div>
        );

      case "patient-list":
        return (
          <div className="max-w-6xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-6">
                Daftar Pasien
              </h1>
              <PatientList />
            </div>
          </div>
        );

      case "patients":
        return (
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Daftar Pasien
                </h2>
                <PatientList
                  onSelectPatient={handlePatientSelect}
                  onAddPatient={handleAddPatient}
                  onEditPatient={handleEditPatient}
                />
              </div>
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Registrasi Cepat
                </h2>
                <PatientRegistrationForm
                  compact
                  onSuccess={handleSaveDiagnosisSuccess}
                />
              </div>
            </div>
          </div>
        );

      case "register":
        return (
          <div>
            <button
              onClick={() => setActiveTab("patients")}
              className="mb-4 text-blue-500 hover:text-blue-700"
            >
              ← Kembali ke Daftar Pasien
            </button>
            <PatientRegistrationForm
              patientToEdit={patientToEdit}
              onSuccess={handleRegistrationSuccess}
              onCancel={handleRegistrationCancel}
            />
          </div>
        );

      case "drug-analysis":
        console.log(
          "DEBUG Dashboard drug-analysis - selectedPatient:",
          selectedPatient
        );
        return (
          <div className="max-w-6xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">
              Analisis Interaksi Obat
            </h1>
            <div className="grid lg:grid-cols-2 gap-6">
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
                    onMedicationsChange={handleMedicationChange}
                  />

                  {error && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">❌ {error}</p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={handleAnalyze}
                      disabled={medications.length === 0 || isAnalyzing}
                      className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                    >
                      {isAnalyzing ? (
                        <>
                          <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Menganalisis...
                        </>
                      ) : (
                        "Analisis Interaksi"
                      )}
                    </button>
                    {interactionResults && !error && (
                      <SaveDiagnosisButton
                        diagnosisData={selectedDiagnosis}
                        medications={medications}
                        interactionResults={interactionResults}
                        selectedPatient={selectedPatient}
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

                  {!interactionResults && !error && (
                    <div className="text-center py-12 text-gray-500">
                      <p>Hasil analisis akan muncul di sini</p>
                      <p className="text-sm">
                        Tambahkan obat dan klik "Analisis Interaksi"
                      </p>
                    </div>
                  )}

                  {interactionResults && !error && (
                    <InteractionResults
                      patient={selectedPatient}
                      diagnoses={selectedDiagnosis ? [selectedDiagnosis] : []}
                      medications={medications}
                      autoAnalyze={false}
                      analysis={interactionResults}
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
                        {interactionResults?.interactions?.length || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      default: // dashboard
        return (
          <div className="max-w-6xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">
              SADEWA Dashboard
            </h1>
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                {/* Patient Selection */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    1. Pilih Pasien
                  </h2>
                  <PatientSelector
                    selectedPatient={selectedPatient}
                    onPatientSelect={handlePatientSelect}
                    currentMedications={medications}
                  />
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
                    onMedicationsChange={handleMedicationChange}
                  />

                  {error && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">❌ {error}</p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={handleAnalyze}
                      disabled={medications.length === 0 || isAnalyzing}
                      className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                    >
                      {isAnalyzing ? (
                        <>
                          <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Menganalisis...
                        </>
                      ) : (
                        "Analisis Interaksi"
                      )}
                    </button>

                    {interactionResults && !error && (
                      <SaveDiagnosisButton
                        diagnosisData={selectedDiagnosis}
                        medications={medications}
                        interactionResults={interactionResults}
                        selectedPatient={selectedPatient} // ✅ FIXED: Added missing prop
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

                  {!interactionResults && !error && (
                    <div className="text-center py-12 text-gray-500">
                      <p>Hasil analisis akan muncul di sini</p>
                      <p className="text-sm">
                        Tambahkan obat dan klik "Analisis Interaksi"
                      </p>
                    </div>
                  )}

                  {interactionResults && !error && (
                    <InteractionResults
                      patient={selectedPatient}
                      diagnoses={selectedDiagnosis ? [selectedDiagnosis] : []}
                      medications={medications}
                      autoAnalyze={false}
                      analysis={interactionResults}
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
                        {interactionResults?.interactions?.length || 0}
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
