// sadewa-frontend/src/components/PatientDetailModal.jsx
import React, { useState, useEffect } from "react";
import {
  X,
  User,
  Calendar,
  Phone,
  FileText,
  Pill,
  Edit,
  Trash2,
  AlertCircle,
  CheckCircle,
  Activity,
  Clock,
} from "lucide-react";
import { apiService } from "../services/api";

const PatientDetailModal = ({
  isOpen,
  onClose,
  patientId,
  onEdit,
  onDelete,
  onRefresh,
}) => {
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("profile");

  useEffect(() => {
    if (isOpen && patientId) {
      fetchPatientDetail();
    }
  }, [isOpen, patientId]);

  const fetchPatientDetail = async () => {
    try {
      setLoading(true);
      setError("");

      console.log(`Fetching patient detail for ID: ${patientId}`);
      const response = await apiService.getPatientById(patientId);

      console.log("🔍 DEBUG - Full API Response:", response);
      console.log("🔍 DEBUG - response.success:", response.success);
      console.log("🔍 DEBUG - response.data:", response.data);

      // ✅ FIXED: Handle nested response structure
      if (response.success && response.data) {
        // Check if data is nested (response.data has success/data structure)
        const patientData = response.data.success
          ? response.data.data
          : response.data;

        console.log("🔍 DEBUG - Final patient data:", patientData);

        setPatient(patientData);
      } else {
        throw new Error("Failed to load patient detail");
      }
    } catch (err) {
      console.error("Error fetching patient detail:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    if (onEdit && patient) {
      onEdit(patient);
      onClose();
    }
  };

  const handleDelete = async () => {
    if (!patient) return;

    const confirmDelete = window.confirm(
      `Apakah Anda yakin ingin menghapus pasien ${patient.name}?\n\nTindakan ini tidak dapat dibatalkan dan akan menghapus semua riwayat medis pasien.`
    );

    if (confirmDelete) {
      try {
        // ✅ FIXED: Gunakan no_rm bukan id
        const patientId = patient.no_rm || patient.patient_code || patient.id;
        await apiService.deletePatient(patientId);
        if (onDelete) onDelete(patient);
        if (onRefresh) onRefresh();
        onClose();
        alert("Pasien berhasil dihapus");
      } catch (err) {
        alert(`Gagal menghapus pasien: ${err.message}`);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-blue-50">
          <div className="flex items-center gap-3">
            <User className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-bold text-gray-900">
              {loading ? "Loading..." : patient?.name || "Detail Pasien"}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-col h-[calc(90vh-120px)]">
          {loading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-500">Memuat data pasien...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-red-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-4" />
                <p>{error}</p>
                <button
                  onClick={fetchPatientDetail}
                  className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Coba Lagi
                </button>
              </div>
            </div>
          )}

          {!loading && !error && patient && (
            <>
              {/* Tabs */}
              <div className="flex border-b bg-gray-50">
                <button
                  onClick={() => setActiveTab("profile")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "profile"
                      ? "border-blue-500 text-blue-600 bg-white"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <User className="inline h-4 w-4 mr-2" />
                  Profil Pasien
                </button>
                <button
                  onClick={() => setActiveTab("medical")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "medical"
                      ? "border-blue-500 text-blue-600 bg-white"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <FileText className="inline h-4 w-4 mr-2" />
                  Riwayat Medis ({patient.medical_records?.length || 0})
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {activeTab === "profile" && (
                  <div className="space-y-6">
                    {/* Basic Info */}
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-900 mb-3">
                          Informasi Dasar
                        </h3>
                        <div className="space-y-3">
                          <div className="flex items-center gap-3">
                            <User className="h-4 w-4 text-gray-500" />
                            <div>
                              <p className="text-sm text-gray-500">
                                Nama Lengkap
                              </p>
                              <p className="font-medium">{patient.name}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <Calendar className="h-4 w-4 text-gray-500" />
                            <div>
                              <p className="text-sm text-gray-500">Umur</p>
                              <p className="font-medium">{patient.age} tahun</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <User className="h-4 w-4 text-gray-500" />
                            <div>
                              <p className="text-sm text-gray-500">
                                Jenis Kelamin
                              </p>
                              <p className="font-medium">
                                {patient.gender === "male"
                                  ? "Laki-laki"
                                  : "Perempuan"}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-900 mb-3">
                          Kontak & ID
                        </h3>
                        <div className="space-y-3">
                          <div className="flex items-center gap-3">
                            <FileText className="h-4 w-4 text-gray-500" />
                            <div>
                              <p className="text-sm text-gray-500">
                                No. Rekam Medis
                              </p>
                              <p className="font-medium font-mono">
                                {patient.no_rm || patient.patient_code}
                              </p>
                            </div>
                          </div>
                          {patient.phone && (
                            <div className="flex items-center gap-3">
                              <Phone className="h-4 w-4 text-gray-500" />
                              <div>
                                <p className="text-sm text-gray-500">Telepon</p>
                                <p className="font-medium">{patient.phone}</p>
                              </div>
                            </div>
                          )}
                          <div className="flex items-center gap-3">
                            <Clock className="h-4 w-4 text-gray-500" />
                            <div>
                              <p className="text-sm text-gray-500">Terdaftar</p>
                              <p className="font-medium">
                                {new Date(
                                  patient.created_at
                                ).toLocaleDateString("id-ID", {
                                  year: "numeric",
                                  month: "long",
                                  day: "numeric",
                                })}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Medical Info (if available) */}
                    {(patient.weight_kg || patient.ai_risk_score) && (
                      <div className="bg-blue-50 rounded-lg p-4">
                        <h3 className="font-semibold text-blue-900 mb-3">
                          Informasi Medis
                        </h3>
                        <div className="grid md:grid-cols-2 gap-4">
                          {patient.weight_kg && (
                            <div>
                              <p className="text-sm text-blue-600">
                                Berat Badan
                              </p>
                              <p className="font-medium text-blue-900">
                                {patient.weight_kg} kg
                              </p>
                            </div>
                          )}
                          {patient.ai_risk_score && (
                            <div>
                              <p className="text-sm text-blue-600">
                                AI Risk Score
                              </p>
                              <p className="font-medium text-blue-900">
                                {patient.ai_risk_score}/10
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "medical" && (
                  <div className="space-y-4">
                    {!patient.medical_records ||
                    patient.medical_records.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p className="text-lg font-medium">
                          Belum ada riwayat medis
                        </p>
                        <p className="text-sm">
                          Riwayat medis akan muncul di sini setelah pasien
                          melakukan diagnosis
                        </p>
                      </div>
                    ) : (
                      patient.medical_records.map((record, index) => (
                        <div
                          key={record.id}
                          className="bg-white border rounded-lg p-4"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-xs font-bold text-blue-600">
                                  {patient.medical_records.length - index}
                                </span>
                              </div>
                              <div>
                                <p className="font-medium text-gray-900">
                                  Record #{record.id}
                                </p>
                                <p className="text-sm text-gray-500">
                                  {new Date(
                                    record.created_at
                                  ).toLocaleDateString("id-ID", {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* Diagnosis */}
                          {(record.diagnosis_code || record.diagnosis_text) && (
                            <div className="mb-3">
                              <p className="text-sm font-medium text-gray-700 mb-1">
                                Diagnosis:
                              </p>
                              <div className="bg-green-50 rounded p-2">
                                {record.diagnosis_code && (
                                  <p className="text-sm font-mono text-green-800">
                                    {record.diagnosis_code}
                                  </p>
                                )}
                                {record.diagnosis_text && (
                                  <p className="text-sm text-green-700">
                                    {record.diagnosis_text}
                                  </p>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Medications */}
                          {record.medications &&
                            record.medications.length > 0 && (
                              <div className="mb-3">
                                <p className="text-sm font-medium text-gray-700 mb-1">
                                  Obat ({record.medications.length}):
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {record.medications.map((med, medIndex) => (
                                    <span
                                      key={medIndex}
                                      className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs"
                                    >
                                      <Pill className="inline h-3 w-3 mr-1" />
                                      {typeof med === "string"
                                        ? med
                                        : med.name || "Unknown"}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                          {/* Interactions Warning */}
                          {record.interactions && (
                            <div className="mb-3">
                              <p className="text-sm font-medium text-gray-700 mb-1">
                                Status Interaksi:
                              </p>
                              <div className="flex items-center gap-2">
                                {record.interactions.safe_to_prescribe ? (
                                  <>
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                    <span className="text-sm text-green-700">
                                      Aman untuk diresepkan
                                    </span>
                                  </>
                                ) : (
                                  <>
                                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                                    <span className="text-sm text-yellow-700">
                                      Perlu perhatian khusus
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Notes */}
                          {record.notes && (
                            <div className="mt-3 pt-3 border-t">
                              <p className="text-sm font-medium text-gray-700 mb-1">
                                Catatan:
                              </p>
                              <p className="text-sm text-gray-600 italic">
                                {record.notes}
                              </p>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              <div className="border-t p-4 bg-gray-50 flex justify-between">
                <div className="flex gap-2">
                  <button
                    onClick={handleEdit}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                  >
                    <Edit className="h-4 w-4" />
                    Edit Pasien
                  </button>
                  <button
                    onClick={handleDelete}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                    Hapus Pasien
                  </button>
                </div>
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  Tutup
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientDetailModal;
