// sadewa-frontend/src/components/PatientRegistrationForm.jsx
// ✅ COMPLETE FIXED VERSION - Match dengan database schema
import React, { useState, useEffect } from "react"; // ✅ IMPORTED: useEffect
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

// ✅ IMPORTED: apiService
import { apiService } from "../services/api";

// Menerima prop 'patientToEdit' untuk mode edit
const PatientRegistrationForm = ({ patientToEdit, onSuccess, onCancel }) => {
  // --- Initialization based on Mode ---
  const isEditMode = !!patientToEdit;
  const formTitle = isEditMode ? "Edit Data Pasien" : "Daftarkan Pasien Baru";
  const submitButtonText = isEditMode ? "Simpan Perubahan" : "Daftar Pasien";
  const successMessage = isEditMode
    ? "Pasien Berhasil Diperbarui!"
    : "Pasien Berhasil Didaftarkan!";

  const initialFormState = {
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
  };

  const [formData, setFormData] = useState(initialFormState);
  const [calculatedAge, setCalculatedAge] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  // ✅ ADDED: useEffect untuk mengisi form saat mode Edit
  useEffect(() => {
    if (isEditMode && patientToEdit) {
      // Set form data dari patientToEdit
      setFormData({
        no_rm: patientToEdit.no_rm || "",
        name: patientToEdit.name || "",
        // Pastikan format tanggal (YYYY-MM-DD)
        birth_date: patientToEdit.birth_date
          ? patientToEdit.birth_date.split("T")[0]
          : "",
        gender: patientToEdit.gender || "",
        address: patientToEdit.address || "",
        phone: patientToEdit.phone || "",
        // Konversi nilai numerik ke string untuk input form
        height_cm: String(patientToEdit.height_cm || ""),
        weight_kg: String(patientToEdit.weight_kg || ""),
        blood_types: patientToEdit.blood_types || "",
        allergies: patientToEdit.allergies || "",
      });
      // Hitung umur dari data yang di-load
      setCalculatedAge(calculateAge(patientToEdit.birth_date));
    } else {
      // Jika mode registrasi baru, reset form
      setFormData(initialFormState);
      setCalculatedAge(null);
    }
  }, [patientToEdit]); // Dependency: Jalankan saat patientToEdit berubah

  // ... (existing calculateAge function)
  const calculateAge = (birthDate) => {
    if (!birthDate) return null;

    const birth = new Date(birthDate);
    const today = new Date();

    if (birth > today) {
      return null;
    }

    let years = today.getFullYear() - birth.getFullYear();
    let months = today.getMonth() - birth.getMonth();
    let days = today.getDate() - birth.getDate();

    if (days < 0) {
      months--;
      const lastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
      days += lastMonth.getDate();
    }

    if (months < 0) {
      years--;
      months += 12;
    }

    return {
      years,
      months,
      days,
      totalYears: years,
      ageString: `${years} tahun, ${months} bulan, ${days} hari`,
    };
  };

  // ... (existing generateNoRM function)
  const generateNoRM = async () => {
    try {
      // Get all existing patients to find the highest number
      const response = await fetch("/api/patients/search?limit=1000");
      if (response.ok) {
        const data = await response.json();
        const patients = data.patients || [];

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

        const nextNumber = maxNumber + 1;
        return `rm${nextNumber.toString().padStart(4, "0")}`;
      }
    } catch (error) {
      console.error("Error generating No. RM:", error);
    }

    const random = Math.floor(Math.random() * 9000) + 1000;
    return `rm${random.toString().padStart(4, "0")}`;
  };

  // ... (existing handleChange function)
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (name === "birth_date") {
      const ageData = calculateAge(value);
      setCalculatedAge(ageData);
    }

    if (error) setError("");
  };

  // ... (existing handleGenerateNoRM function)
  const handleGenerateNoRM = async () => {
    const newNoRM = await generateNoRM();
    setFormData((prev) => ({
      ...prev,
      no_rm: newNoRM,
    }));
  };

  // ... (existing validateForm function)
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

  // ✅ MODIFIED: handleSubmit untuk mode POST dan PUT
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    setError("");

    // Payload yang disiapkan untuk dikirim ke API
    const payload = {
      ...formData,
      age: calculatedAge?.totalYears || 0,
      weight_kg: parseFloat(formData.weight_kg),
      height_cm: parseFloat(formData.height_cm),
    };

    try {
      let result;

      if (isEditMode) {
        // --- LOGIKA EDIT (PUT) ---
        const patientId = patientToEdit.id;
        console.log(`Updating patient ID: ${patientId}`, payload);

        // Menggunakan fungsi updatePatient yang baru ditambahkan
        result = await apiService.updatePatient(patientId, payload);
      } else {
        // --- LOGIKA REGISTRASI (POST) ---
        console.log("Registering new patient:", payload);

        // Menggunakan fungsi registerPatient yang baru ditambahkan
        result = await apiService.registerPatient(payload);
      }

      if (result.success) {
        setSuccess(true);

        if (onSuccess) {
          setTimeout(() => onSuccess(result.data), 1500);
        }
      } else {
        // Jika result.success false (jika ada error yang ditangani di apiService)
        throw new Error(result.message || "Gagal menyimpan data pasien.");
      }
    } catch (err) {
      // Tangkap error dari apiService
      setError(
        err.message || "Terjadi kesalahan saat komunikasi dengan server."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    // Di mode edit, reset hanya mengembalikan ke data awal
    if (isEditMode) {
      setFormData({
        no_rm: patientToEdit.no_rm,
        name: patientToEdit.name,
        birth_date: patientToEdit.birth_date
          ? patientToEdit.birth_date.split("T")[0]
          : "",
        gender: patientToEdit.gender,
        address: patientToEdit.address,
        phone: patientToEdit.phone,
        height_cm: String(patientToEdit.height_cm),
        weight_kg: String(patientToEdit.weight_kg),
        blood_types: patientToEdit.blood_types,
        allergies: patientToEdit.allergies,
      });
      setCalculatedAge(calculateAge(patientToEdit.birth_date));
    } else {
      // Di mode registrasi baru, kosongkan form
      setFormData(initialFormState);
      setCalculatedAge(null);
    }
    setError("");
    setSuccess(false);
  };

  if (success) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg">
        <div className="text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {successMessage}
          </h3>
          <p className="text-gray-600 mb-4">
            {formData.name} {isEditMode ? "(diperbarui)" : "(terdaftar)"} dengan
            No. RM: {formData.no_rm}
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
            {formTitle} {/* Judul dinamis */}
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
        {/* No. RM field with auto-generate */}
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
              disabled={isEditMode}
            />
            {/* Tombol Generate hanya muncul di mode Registrasi Baru */}
            {!isEditMode && (
              <button
                type="button"
                onClick={handleGenerateNoRM}
                className="px-3 py-2 bg-blue-50 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-100 focus:ring-2 focus:ring-blue-500 text-sm font-medium"
              >
                Generate
              </button>
            )}
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
              max={new Date().toISOString().split("T")[0]}
              required
            />
            {/* Display calculated age */}
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

        {/* Golongan Darah field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Heart className="inline h-4 w-4 mr-1" />
            Golongan Darah *
          </label>
          <select
            name="blood_types"
            value={formData.blood_types}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">Pilih golongan darah</option>
            <option value="A">A</option>
            <option value="B">B</option>
            <option value="AB">AB</option>
            <option value="O">O</option>
            <option value="Other">Lainnya/Tidak diketahui</option>
          </select>
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
                {isEditMode ? "Menyimpan..." : "Mendaftarkan..."}
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                {submitButtonText}
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500"
          >
            {isEditMode ? "Reset Form" : "Reset"}{" "}
            {/* Reset ke data awal/kosong */}
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500"
            >
              Kembali
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
