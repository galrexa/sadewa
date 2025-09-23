// sadewa-frontend/src/components/SaveDiagnosisButton.jsx
import React, { useState } from "react";
import {
  Save,
  User,
  FileText,
  Pill,
  AlertTriangle,
  CheckCircle,
  X,
  Users,
} from "lucide-react";
import { apiService } from "../services/api";

const SaveDiagnosisButton = ({
  diagnosisData,
  medications = [],
  interactionResults = null,
  selectedPatient,
  onSuccess,
  disabled = false,
}) => {
  console.log("DEBUG SaveDiagnosisButton:", {
    selectedPatient,
    medications,
    medicationsLength: medications.length,
    disabled,
    shouldBeDisabled: disabled || medications.length === 0 || !selectedPatient,
  });
  const [showModal, setShowModal] = useState(false);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleOpenModal = () => {
    setShowModal(true);
    setError("");
  };

  const handleSave = async () => {
    if (!selectedPatient) {
      setError("Tidak ada pasien yang dipilih");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const payload = {
        patient_id: selectedPatient?.patient_code || selectedPatient?.no_rm,
        diagnosis_code: diagnosisData?.code || null,
        diagnosis_text: diagnosisData?.name_id || diagnosisData?.text || null,
        medications: medications,
        interaction_results: interactionResults,
        notes: notes.trim() || null,
      };

      console.log("Saving diagnosis with payload:", payload);

      const response = await fetch(
        `${apiService.api.defaults.baseURL}/api/patients/${
          selectedPatient?.patient_code || selectedPatient?.no_rm
        }/save-diagnosis`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Gagal menyimpan diagnosis");
      }

      const result = await response.json();

      // Success
      setShowModal(false);
      setNotes("");

      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleCloseModal = () => {
    if (saving) return;
    setShowModal(false);
    setNotes("");
    setError("");
  };

  // Summary untuk preview
  const getSummary = () => {
    const summary = {
      diagnosis:
        diagnosisData?.name_id || diagnosisData?.text || "Tidak ada diagnosis",
      medicationCount: medications.length,
      hasInteractions:
        interactionResults?.warnings?.length > 0 ||
        interactionResults?.interactions_found > 0,
    };
    return summary;
  };

  const summary = getSummary();

  return (
    <>
      {/* Save Button */}
      <button
        onClick={handleOpenModal}
        disabled={disabled || !selectedPatient}
        className="flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-medium transition-colors"
        title={
          !selectedPatient
            ? "Pilih pasien terlebih dahulu"
            : medications.length === 0
            ? "Tambahkan obat terlebih dahulu"
            : "Simpan diagnosis ke rekam medis pasien"
        }
      >
        <Save className="h-4 w-4" />
        Simpan Diagnosis
      </button>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <div className="flex items-center gap-3">
                <Save className="h-6 w-6 text-green-500" />
                <h2 className="text-xl font-bold text-gray-900">
                  Simpan Diagnosis ke Rekam Medis
                </h2>
              </div>
              <button
                onClick={handleCloseModal}
                disabled={saving}
                className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Current Patient Info */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Simpan untuk Pasien:
                </h3>
                <div className="text-blue-800">
                  <p className="font-medium">{selectedPatient?.name}</p>
                  <p className="text-sm">
                    {selectedPatient?.age} tahun,{" "}
                    {selectedPatient?.gender === "male"
                      ? "Laki-laki"
                      : "Perempuan"}
                  </p>
                  <p className="text-xs text-blue-600">
                    ID:{" "}
                    {selectedPatient?.patient_code || selectedPatient?.no_rm}
                  </p>
                </div>
              </div>

              {/* Preview Diagnosis */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Preview Data yang akan Disimpan
                </h3>

                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">
                      Diagnosis:
                    </span>
                    <p className="text-gray-600 mt-1">{summary.diagnosis}</p>
                  </div>

                  <div>
                    <span className="font-medium text-gray-700">
                      Obat ({summary.medicationCount}):
                    </span>
                    <div className="mt-1">
                      {medications.map((med, index) => (
                        <span
                          key={index}
                          className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-2 mb-1"
                        >
                          {typeof med === "string"
                            ? med
                            : `${med.name || "Unknown"} ${med.dosage || ""}`}
                        </span>
                      ))}
                    </div>
                  </div>

                  {summary.hasInteractions && (
                    <div className="flex items-center gap-2 text-orange-600">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="font-medium">
                        Ditemukan{" "}
                        {interactionResults?.warnings?.length ||
                          interactionResults?.interactions_found ||
                          0}{" "}
                        peringatan interaksi obat
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Clinical Notes */}
              <div>
                <label
                  htmlFor="notes"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Catatan Klinis (Opsional)
                </label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Tambahkan catatan klinis, instruksi khusus, atau observasi..."
                  rows={4}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  disabled={saving}
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {/* Modal Actions */}
              <div className="flex gap-3 pt-4 border-t">
                <button
                  onClick={handleSave}
                  disabled={saving || !selectedPatient}
                  className="flex-1 flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-4 py-3 rounded-lg font-medium transition-colors"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Menyimpan...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Simpan ke Rekam Medis
                    </>
                  )}
                </button>

                <button
                  onClick={handleCloseModal}
                  disabled={saving}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  Batal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SaveDiagnosisButton;
