// sadewa-frontend/src/components/PatientList.jsx
import React, { useState, useEffect } from "react";
import {
  Users,
  Search,
  Plus,
  Eye,
  Edit,
  Trash2,
  Phone,
  Calendar,
  UserCheck,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";

const PatientList = ({ onSelectPatient, onAddPatient, onEditPatient }) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
  });

  // Fetch patients dari API
  const fetchPatients = async (page = 1, search = "") => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: pagination.limit.toString(),
      });

      if (search.trim()) {
        params.append("search", search.trim());
      }

      const response = await fetch(`/api/patients/?${params}`);

      if (!response.ok) {
        throw new Error("Gagal mengambil data pasien");
      }

      const data = await response.json();

      setPatients(data.patients);
      setPagination((prev) => ({
        ...prev,
        page: data.page,
        total: data.total,
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load initial data
  useEffect(() => {
    fetchPatients();
  }, []);

  // Handle search
  const handleSearch = (e) => {
    const value = e.target.value;
    setSearchTerm(value);

    // Debounce search
    const timeoutId = setTimeout(() => {
      fetchPatients(1, value);
    }, 500);

    return () => clearTimeout(timeoutId);
  };

  // Handle pagination
  const handlePageChange = (newPage) => {
    if (
      newPage < 1 ||
      newPage > Math.ceil(pagination.total / pagination.limit)
    ) {
      return;
    }
    fetchPatients(newPage, searchTerm);
  };

  // Handle delete patient
  const handleDeletePatient = async (patientId, patientName) => {
    if (!confirm(`Yakin ingin menghapus pasien ${patientName}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/patients/${patientId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Gagal menghapus pasien");
      }

      // Refresh list
      fetchPatients(pagination.page, searchTerm);

      alert("Pasien berhasil dihapus");
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  // Format gender untuk display
  const formatGender = (gender) => {
    return gender === "male" ? "Laki-laki" : "Perempuan";
  };

  // Format tanggal
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("id-ID", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div className="flex items-center gap-2 mb-4 sm:mb-0">
          <Users className="h-6 w-6 text-blue-500" />
          <h2 className="text-xl font-bold text-gray-900">
            Daftar Pasien ({pagination.total})
          </h2>
        </div>

        <button
          onClick={onAddPatient}
          className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          Tambah Pasien
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Cari nama pasien..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          <span className="ml-2 text-gray-600">Memuat data pasien...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 mb-4">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
          <button
            onClick={() => fetchPatients(pagination.page, searchTerm)}
            className="ml-auto px-3 py-1 bg-red-100 hover:bg-red-200 rounded text-sm"
          >
            Coba Lagi
          </button>
        </div>
      )}

      {/* Patient List */}
      {!loading && !error && (
        <>
          {patients.length === 0 ? (
            <div className="text-center py-12">
              <Users className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Tidak ada pasien
              </h3>
              <p className="text-gray-600 mb-4">
                {searchTerm
                  ? "Tidak ditemukan pasien yang sesuai pencarian"
                  : "Belum ada pasien yang terdaftar"}
              </p>
              {!searchTerm && (
                <button
                  onClick={onAddPatient}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
                >
                  Tambah Pasien Pertama
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {patients.map((patient) => (
                <div
                  key={patient.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {patient.name}
                        </h3>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            patient.gender === "male"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-pink-100 text-pink-800"
                          }`}
                        >
                          {formatGender(patient.gender)}
                        </span>
                      </div>

                      <div className="flex items-center gap-6 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {patient.age} tahun
                        </div>
                        {patient.phone && (
                          <div className="flex items-center gap-1">
                            <Phone className="h-4 w-4" />
                            {patient.phone}
                          </div>
                        )}
                        <div className="text-xs text-gray-400">
                          Terdaftar: {formatDate(patient.created_at)}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => onSelectPatient(patient)}
                        className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Lihat Detail"
                      >
                        <Eye className="h-4 w-4" />
                      </button>

                      {onEditPatient && (
                        <button
                          onClick={() => onEditPatient(patient)}
                          className="p-2 text-green-500 hover:bg-green-50 rounded-lg transition-colors"
                          title="Edit Pasien"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                      )}

                      <button
                        onClick={() =>
                          handleDeletePatient(patient.id, patient.name)
                        }
                        className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="Hapus Pasien"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {pagination.total > pagination.limit && (
            <div className="flex items-center justify-between pt-6 border-t">
              <div className="text-sm text-gray-600">
                Menampilkan {(pagination.page - 1) * pagination.limit + 1} -{" "}
                {Math.min(pagination.page * pagination.limit, pagination.total)}{" "}
                dari {pagination.total} pasien
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>

                <span className="px-4 py-2 text-sm font-medium">
                  {pagination.page} /{" "}
                  {Math.ceil(pagination.total / pagination.limit)}
                </span>

                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={
                    pagination.page ===
                    Math.ceil(pagination.total / pagination.limit)
                  }
                  className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PatientList;
