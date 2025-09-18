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

const SaveDiagnosisButton = ({
  diagnosisData,
  medications = [],
  interactionResults = null,
  onSuccess,
  disabled = false,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState("");
  const [patients, setPatients] = useState([]);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Fetch patients ketika modal dibuka
  const handleOpenModal = async () => {
    setShowModal(true);
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/patients/?limit=100");
      if (!response.ok) {
        throw new Error("Gagal mengambil data pasien");
      }

      const data = await response.json();
      setPatients(data.patients);
    } catch (err) {
      setError("Gagal memuat daftar pasien. " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedPatient) {
      setError("Pilih pasien terlebih dahulu");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const payload = {
        patient_id: parseInt(selectedPatient),
        diagnosis_code: diagnosisData?.code || null,
        diagnosis_text: diagnosisData?.text || null,
        medications: medications,
        interaction_results: interactionResults,
        notes: notes.trim() || null,
      };

      const response = await fetch(
        `/api/patients/${selectedPatient}/save-diagnosis`,
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
      setSelectedPatient("");
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
    setSelectedPatient("");
    setNotes("");
    setError("");
  };

  // Summary untuk preview
  const getSummary = () => {
    const summary = {
      diagnosis: diagnosisData?.text || "Tidak ada diagnosis",
      medicationCount: medications.length,
      hasInteractions: interactionResults?.interactions_found > 0,
    };
    return summary;
  };

  const summary = getSummary();

  return (
    <>
      {/* Save Button */}
      <button
        onClick={handleOpenModal}
        disabled={disabled || medications.length === 0}
        className="flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-medium transition-colors"
        title={
          medications.length === 0
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
                          {med}
                        </span>
                      ))}
                    </div>
                  </div>

                  {summary.hasInteractions && (
                    <div className="flex items-center gap-2 text-orange-600">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="font-medium">
                        Ditemukan {interactionResults.interactions_found}{" "}
                        interaksi obat
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Patient Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pilih Pasien *
                </label>

                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent"></div>
                    <span className="ml-2 text-gray-600">
                      Memuat daftar pasien...
                    </span>
                  </div>
                ) : patients.length === 0 ? (
                  <div className="text-center py-8 bg-gray-50 rounded-lg">
                    <Users className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                    <p className="text-gray-600">Belum ada pasien terdaftar</p>
                    <p className="text-sm text-gray-500">
                      Daftarkan pasien terlebih dahulu
                    </p>
                  </div>
                ) : (
                  <select
                    value={selectedPatient}
                    onChange={(e) => setSelectedPatient(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={saving}
                  >
                    <option value="">-- Pilih Pasien --</option>
                    {patients.map((patient) => (
                      <option key={patient.id} value={patient.id}>
                        {patient.name} ({patient.age} tahun,{" "}
                        {patient.gender === "male" ? "Laki-laki" : "Perempuan"})
                      </option>
                    ))}
                  </select>
                )}
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
                  disabled={saving || !selectedPatient || patients.length === 0}
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
