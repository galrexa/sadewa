// sadewa-frontend/src/components/PatientRegistrationForm.jsx
// ✅ COMPLETE FIXED VERSION - Match dengan database schema
import React, { useState } from "react";
import {
  User,
  Phone,
  Calendar,
  UserCheck,
  Save,
  AlertCircle,
  CheckCircle,
  IdCard,
  MapPin,
  Ruler,
  Weight,
  Heart,
  AlertTriangle,
} from "lucide-react";

const PatientRegistrationForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    no_rm: "",
    name: "",
    birth_date: "",
    gender: "",
    address: "",
    phone: "",
    height_cm: "",
    weight_kg: "",
    blood_types: "",
    allergies: "",
  });
  const [calculatedAge, setCalculatedAge] = useState(null); // ✅ ADDED: untuk display umur
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  // ✅ ADDED: Function untuk menghitung umur detail
  const calculateAge = (birthDate) => {
    if (!birthDate) return null;

    const birth = new Date(birthDate);
    const today = new Date();

    // Validasi tanggal lahir tidak boleh di masa depan
    if (birth > today) {
      return null;
    }

    let years = today.getFullYear() - birth.getFullYear();
    let months = today.getMonth() - birth.getMonth();
    let days = today.getDate() - birth.getDate();

    // Adjust untuk bulan negatif
    if (days < 0) {
      months--;
      const lastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
      days += lastMonth.getDate();
    }

    // Adjust untuk tahun negatif
    if (months < 0) {
      years--;
      months += 12;
    }

    return {
      years,
      months,
      days,
      totalYears: years, // Untuk backend compatibility
      ageString: `${years} tahun, ${months} bulan, ${days} hari`,
    };
  };
  const generateNoRM = async () => {
    try {
      // Get all existing patients to find the highest number
      const response = await fetch("/api/patients/search?limit=1000");
      if (response.ok) {
        const data = await response.json();
        const patients = data.patients || [];

        // Find the highest rm number
        let maxNumber = 0;
        patients.forEach((patient) => {
          const match = patient.no_rm?.match(/^rm(\d{4})$/i);
          if (match) {
            const num = parseInt(match[1]);
            if (num > maxNumber) {
              maxNumber = num;
            }
          }
        });

        // Generate next number with leading zeros
        const nextNumber = maxNumber + 1;
        return `rm${nextNumber.toString().padStart(4, "0")}`;
      }
    } catch (error) {
      console.error("Error generating No. RM:", error);
    }

    // Fallback: generate random if API call fails
    const random = Math.floor(Math.random() * 9000) + 1000; // 1000-9999
    return `rm${random.toString().padStart(4, "0")}`;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // ✅ ADDED: Auto-calculate age when birth_date changes
    if (name === "birth_date") {
      const ageData = calculateAge(value);
      setCalculatedAge(ageData);
    }

    // Clear error saat user mulai mengetik
    if (error) setError("");
  };

  const handleGenerateNoRM = async () => {
    const newNoRM = await generateNoRM();
    setFormData((prev) => ({
      ...prev,
      no_rm: newNoRM,
    }));
  };

  const validateForm = () => {
    if (!formData.no_rm.trim()) {
      setError("Nomor rekam medis wajib diisi");
      return false;
    }
    if (!formData.name.trim()) {
      setError("Nama pasien wajib diisi");
      return false;
    }
    if (!formData.birth_date) {
      setError("Tanggal lahir wajib diisi");
      return false;
    }

    // ✅ ADDED: Validate birth date
    const ageData = calculateAge(formData.birth_date);
    if (!ageData) {
      setError("Tanggal lahir tidak valid atau di masa depan");
      return false;
    }
    if (ageData.totalYears > 150) {
      setError("Umur tidak boleh lebih dari 150 tahun");
      return false;
    }

    if (!formData.gender) {
      setError("Jenis kelamin wajib dipilih");
      return false;
    }
    if (!formData.address.trim()) {
      setError("Alamat wajib diisi");
      return false;
    }
    if (
      !formData.height_cm ||
      formData.height_cm < 50 ||
      formData.height_cm > 250
    ) {
      setError("Tinggi badan harus antara 50-250 cm");
      return false;
    }
    if (
      !formData.weight_kg ||
      formData.weight_kg < 1 ||
      formData.weight_kg > 300
    ) {
      setError("Berat badan harus antara 1-300 kg");
      return false;
    }
    if (!formData.blood_types) {
      setError("Golongan darah wajib dipilih");
      return false;
    }
    if (!formData.allergies.trim()) {
      setError(
        "Riwayat alergi wajib diisi (jika tidak ada, tulis 'Tidak ada')"
      );
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    setError("");

    try {
      // ✅ FIXED: Ubah dari /api/patients/register ke /api/patients
      const response = await fetch("/api/patients", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...formData,
          age: calculatedAge?.totalYears || 0,
          weight_kg: parseFloat(formData.weight_kg), // ✅ CHANGED: Kirim umur yang sudah dihitung
          height_cm: parseFloat(formData.height_cm),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Gagal membuat pasien baru");
      }

      const result = await response.json();

      setSuccess(true);

      // Call success callback dengan data pasien
      if (onSuccess) {
        setTimeout(() => onSuccess(result), 1500);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      no_rm: "",
      name: "",
      birth_date: "",
      gender: "",
      address: "",
      phone: "",
      height_cm: "",
      weight_kg: "",
      blood_types: "",
      allergies: "",
    });
    setCalculatedAge(null); // ✅ ADDED: Reset calculated age
    setError("");
    setSuccess(false);
  };

  if (success) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg">
        <div className="text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Pasien Berhasil Didaftarkan!
          </h3>
          <p className="text-gray-600 mb-4">
            {formData.name} telah terdaftar dengan No. RM: {formData.no_rm}
            <br />
            <span className="text-sm text-gray-500">
              Umur: {calculatedAge?.ageString || "Tidak terhitung"}
            </span>
          </p>
          <p className="text-sm text-gray-500">
            Mengalihkan ke halaman utama...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      <div className="flex items-center justify-center mb-6">
        <div className="flex items-center space-x-3">
          <UserCheck className="h-8 w-8 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">
            Daftarkan Pasien Baru
          </h2>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* ✅ ADDED: No. RM field with auto-generate */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <IdCard className="inline h-4 w-4 mr-1" />
            Nomor Rekam Medis *
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              name="no_rm"
              value={formData.no_rm}
              onChange={handleChange}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Masukkan No. RM atau generate otomatis"
              required
            />
            <button
              type="button"
              onClick={handleGenerateNoRM}
              className="px-3 py-2 bg-blue-50 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-100 focus:ring-2 focus:ring-blue-500 text-sm font-medium"
            >
              Generate
            </button>
          </div>
        </div>

        {/* Basic Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="inline h-4 w-4 mr-1" />
              Nama Lengkap *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Masukkan nama lengkap pasien"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="inline h-4 w-4 mr-1" />
              Tanggal Lahir *
            </label>
            <input
              type="date"
              name="birth_date"
              value={formData.birth_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              max={new Date().toISOString().split("T")[0]} // ✅ Tidak boleh pilih tanggal masa depan
              required
            />
            {/* ✅ ADDED: Display calculated age */}
            {calculatedAge && (
              <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-700 font-medium">
                  📅 Umur: {calculatedAge.ageString}
                </p>
                <p className="text-xs text-blue-600">
                  ({calculatedAge.totalYears} tahun untuk sistem)
                </p>
              </div>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <UserCheck className="inline h-4 w-4 mr-1" />
            Jenis Kelamin *
          </label>
          <select
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">Pilih jenis kelamin</option>
            <option value="male">Laki-laki</option>
            <option value="female">Perempuan</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="inline h-4 w-4 mr-1" />
            Alamat Lengkap *
          </label>
          <textarea
            name="address"
            value={formData.address}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Masukkan alamat lengkap pasien"
            rows="3"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Weight className="inline h-4 w-4 mr-1" />
              Berat Badan (kg) *
            </label>
            <input
              type="number"
              name="weight_kg"
              value={formData.weight_kg}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="70"
              min="1"
              max="300"
              step="0.1"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Ruler className="inline h-4 w-4 mr-1" />
              Tinggi Badan (cm) *
            </label>
            <input
              type="number"
              name="height_cm"
              value={formData.height_cm}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="170"
              min="50"
              max="250"
              step="0.1"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <AlertTriangle className="inline h-4 w-4 mr-1" />
            Riwayat Alergi *
          </label>
          <textarea
            name="allergies"
            value={formData.allergies}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Sebutkan riwayat alergi (contoh: Penisilin, Udang) atau tulis 'Tidak ada'"
            rows="2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Phone className="inline h-4 w-4 mr-1" />
            Nomor Telepon
          </label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Masukkan nomor telepon (opsional)"
          />
        </div>

        <div className="flex space-x-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Mendaftarkan...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Daftar Pasien
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500"
          >
            Reset
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500"
            >
              Batal
            </button>
          )}
        </div>
      </form>

      <div className="mt-4 text-xs text-gray-500">
        <p>* Field yang wajib diisi</p>
        <p>
          💡 <strong>Tips:</strong> Klik "Generate" untuk membuat No. RM
          otomatis (format: rm0001, rm0002, ...)
        </p>
      </div>
    </div>
  );
};

export default PatientRegistrationForm;
