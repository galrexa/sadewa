import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Plus,
  X,
  Pill,
  AlertCircle,
  Clock,
  Search,
  Loader2,
} from "lucide-react";
import { drugService } from "../services/drugService";

const MedicationInput = ({
  medications = [],
  onMedicationsChange,
  className = "",
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMedication, setNewMedication] = useState({
    name: "",
    dosage: "",
    frequency: "",
    notes: "",
  });
  const [errors, setErrors] = useState({});

  // Drug autocomplete state
  const [drugSuggestions, setDrugSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const suggestionTimeoutRef = useRef(null);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Common medications from database (akan di-load dinamis)
  const [commonMedications, setCommonMedications] = useState([
    { name: "Paracetamol", dosage: "500mg", frequency: "3x daily" },
    { name: "Ibuprofen", dosage: "400mg", frequency: "As needed" },
    { name: "Amoxicillin", dosage: "500mg", frequency: "3x daily" },
    { name: "Omeprazole", dosage: "20mg", frequency: "Once daily" },
    { name: "Metformin", dosage: "500mg", frequency: "2x daily" },
    { name: "Amlodipine", dosage: "5mg", frequency: "Once daily" },
  ]);

  // Load popular drugs from database on mount
  useEffect(() => {
    loadPopularDrugs();
  }, []);

  const loadPopularDrugs = async () => {
    try {
      const result = await drugService.searchDrugs("paracetamol", 1);
      if (result.success && result.data.length > 0) {
        // Update common medications with real database data
        const popularQueries = [
          "paracetamol",
          "ibuprofen",
          "amoxicillin",
          "omeprazole",
          "metformin",
          "amlodipine",
        ];

        const popularDrugs = [];
        for (const query of popularQueries) {
          const searchResult = await drugService.searchDrugs(query, 1);
          if (searchResult.success && searchResult.data.length > 0) {
            const drug = searchResult.data[0];
            popularDrugs.push({
              name: drug.nama_obat,
              dosage: "As prescribed",
              frequency: "As prescribed",
            });
          }
        }

        if (popularDrugs.length > 0) {
          setCommonMedications(popularDrugs);
        }
      }
    } catch (error) {
      console.log("Using default common medications");
    }
  };

  // Debounced drug search
  const debouncedDrugSearch = useCallback(async (query) => {
    if (!query || query.length < 2) {
      setDrugSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoadingSuggestions(true);

    try {
      const result = await drugService.searchDrugs(query, 8);
      if (result.success) {
        setDrugSuggestions(result.data);
        setShowSuggestions(true);
        setSelectedSuggestionIndex(-1);
      }
    } catch (error) {
      console.error("Drug search error:", error);
      setDrugSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, []);

  // Handle input change with debouncing
  const handleDrugNameChange = (value) => {
    setNewMedication((prev) => ({ ...prev, name: value }));

    // Clear previous timeout
    if (suggestionTimeoutRef.current) {
      clearTimeout(suggestionTimeoutRef.current);
    }

    // Clear errors
    if (errors.name) {
      setErrors((prev) => ({ ...prev, name: "" }));
    }

    // Set new timeout for search
    suggestionTimeoutRef.current = setTimeout(() => {
      debouncedDrugSearch(value);
    }, 300);
  };

  // Handle suggestion selection
  const selectSuggestion = (drug) => {
    setNewMedication((prev) => ({
      ...prev,
      name: drug.nama_obat,
    }));
    setShowSuggestions(false);
    setDrugSuggestions([]);
    setSelectedSuggestionIndex(-1);

    // Focus on next input
    setTimeout(() => {
      const dosageInput = document.querySelector(
        'input[placeholder="e.g., 500mg"]'
      );
      if (dosageInput) dosageInput.focus();
    }, 100);
  };

  // Handle keyboard navigation in suggestions
  const handleKeyDown = (e) => {
    if (!showSuggestions || drugSuggestions.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev < drugSuggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case "ArrowUp":
        e.preventDefault();
        setSelectedSuggestionIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;

      case "Enter":
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          selectSuggestion(drugSuggestions[selectedSuggestionIndex]);
        }
        break;

      case "Escape":
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target) &&
        !inputRef.current?.contains(event.target)
      ) {
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const validateForm = () => {
    const newErrors = {};

    if (!newMedication.name.trim()) {
      newErrors.name = "Nama obat harus diisi";
    }

    if (!newMedication.dosage.trim()) {
      newErrors.dosage = "Dosis harus diisi";
    }

    if (!newMedication.frequency.trim()) {
      newErrors.frequency = "Frekuensi harus diisi";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const addMedication = async () => {
    if (!validateForm()) return;

    // Verify drug exists in database
    try {
      const searchResult = await drugService.searchDrugs(newMedication.name, 1);
      let finalDrugName = newMedication.name;

      if (searchResult.success && searchResult.data.length > 0) {
        // Use exact name from database
        finalDrugName = searchResult.data[0].nama_obat;
      }

      const medicationToAdd = {
        id: Date.now(),
        name: finalDrugName,
        dosage: newMedication.dosage.trim(),
        frequency: newMedication.frequency.trim(),
        notes: newMedication.notes.trim(),
        addedAt: new Date().toISOString(),
      };

      const updatedMedications = [...medications, medicationToAdd];
      onMedicationsChange(updatedMedications);

      // Reset form
      setNewMedication({ name: "", dosage: "", frequency: "", notes: "" });
      setShowAddForm(false);
      setErrors({});
    } catch (error) {
      console.error("Error adding medication:", error);
      // Still add the medication even if verification fails
      const medicationToAdd = {
        id: Date.now(),
        name: newMedication.name.trim(),
        dosage: newMedication.dosage.trim(),
        frequency: newMedication.frequency.trim(),
        notes: newMedication.notes.trim(),
        addedAt: new Date().toISOString(),
      };

      const updatedMedications = [...medications, medicationToAdd];
      onMedicationsChange(updatedMedications);

      setNewMedication({ name: "", dosage: "", frequency: "", notes: "" });
      setShowAddForm(false);
      setErrors({});
    }
  };

  const addCommonMedication = (medication) => {
    const medicationToAdd = {
      id: Date.now(),
      name: medication.name,
      dosage: medication.dosage,
      frequency: medication.frequency,
      notes: "",
      addedAt: new Date().toISOString(),
    };

    const updatedMedications = [...medications, medicationToAdd];
    onMedicationsChange(updatedMedications);
  };

  const removeMedication = (medicationId) => {
    const updatedMedications = medications.filter(
      (med) => med.id !== medicationId
    );
    onMedicationsChange(updatedMedications);
  };

  const cancelAdd = () => {
    setNewMedication({ name: "", dosage: "", frequency: "", notes: "" });
    setShowAddForm(false);
    setErrors({});
    setShowSuggestions(false);
  };

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Pill className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Current Medications
            </h3>
            <p className="text-sm text-gray-500">
              {medications.length} medication
              {medications.length !== 1 ? "s" : ""} added
            </p>
          </div>
        </div>

        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Medication
          </button>
        )}
      </div>

      {/* Quick Add Common Medications */}
      {!showAddForm && medications.length === 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Quick Add Common Medications:
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {commonMedications.slice(0, 6).map((med, index) => (
              <button
                key={index}
                onClick={() => addCommonMedication(med)}
                className="text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
              >
                <div className="font-medium text-gray-900 text-sm">
                  {med.name}
                </div>
                <div className="text-xs text-gray-600">
                  {med.dosage} - {med.frequency}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Add New Medication
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Drug Name with Autocomplete */}
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Medication Name *
              </label>
              <div className="relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={newMedication.name}
                  onChange={(e) => handleDrugNameChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type to search medications..."
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.name ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {isLoadingSuggestions && (
                  <Loader2 className="absolute right-3 top-2.5 h-4 w-4 text-gray-400 animate-spin" />
                )}
              </div>

              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}

              {/* Suggestions Dropdown */}
              {showSuggestions && drugSuggestions.length > 0 && (
                <div
                  ref={suggestionsRef}
                  className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
                >
                  {drugSuggestions.map((drug, index) => (
                    <button
                      key={drug.id}
                      onClick={() => selectSuggestion(drug)}
                      className={`w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                        index === selectedSuggestionIndex
                          ? "bg-green-50 text-green-900"
                          : ""
                      }`}
                    >
                      <div className="font-medium text-sm">
                        {drug.nama_obat}
                      </div>
                      <div className="text-xs text-gray-600">
                        {drug.nama_obat_internasional}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Dosage */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dosage *
              </label>
              <input
                type="text"
                value={newMedication.dosage}
                onChange={(e) =>
                  setNewMedication((prev) => ({
                    ...prev,
                    dosage: e.target.value,
                  }))
                }
                placeholder="e.g., 500mg"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.dosage ? "border-red-300" : "border-gray-300"
                }`}
              />
              {errors.dosage && (
                <p className="mt-1 text-sm text-red-600">{errors.dosage}</p>
              )}
            </div>

            {/* Frequency */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequency *
              </label>
              <select
                value={newMedication.frequency}
                onChange={(e) =>
                  setNewMedication((prev) => ({
                    ...prev,
                    frequency: e.target.value,
                  }))
                }
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.frequency ? "border-red-300" : "border-gray-300"
                }`}
              >
                <option value="">Select frequency</option>
                <option value="Once daily">Once daily</option>
                <option value="Twice daily">Twice daily (2x daily)</option>
                <option value="Three times daily">
                  Three times daily (3x daily)
                </option>
                <option value="Four times daily">
                  Four times daily (4x daily)
                </option>
                <option value="As needed">As needed (PRN)</option>
                <option value="Every 4 hours">Every 4 hours</option>
                <option value="Every 6 hours">Every 6 hours</option>
                <option value="Every 8 hours">Every 8 hours</option>
                <option value="Every 12 hours">Every 12 hours</option>
              </select>
              {errors.frequency && (
                <p className="mt-1 text-sm text-red-600">{errors.frequency}</p>
              )}
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (Optional)
              </label>
              <input
                type="text"
                value={newMedication.notes}
                onChange={(e) =>
                  setNewMedication((prev) => ({
                    ...prev,
                    notes: e.target.value,
                  }))
                }
                placeholder="e.g., Take with food"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 mt-4">
            <button
              onClick={cancelAdd}
              className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={addMedication}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Add Medication
            </button>
          </div>
        </div>
      )}

      {/* Current Medications List */}
      {medications.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Current Medications ({medications.length}):
          </h4>

          {medications.map((medication) => (
            <div
              key={medication.id}
              className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h5 className="font-semibold text-gray-900">
                    {medication.name}
                  </h5>
                  <span className="text-sm text-green-600 bg-green-100 px-2 py-0.5 rounded">
                    {medication.dosage}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {medication.frequency}
                  </div>
                  {medication.notes && (
                    <div className="text-gray-500">
                      Note: {medication.notes}
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={() => removeMedication(medication.id)}
                className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                title="Remove medication"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {medications.length === 0 && !showAddForm && (
        <div className="text-center py-12 text-gray-500">
          <Pill className="h-12 w-12 mx-auto text-gray-300 mb-3" />
          <p className="text-lg font-medium mb-2">No medications added yet</p>
          <p className="text-sm">
            Add current medications to check for interactions and
            contraindications
          </p>
        </div>
      )}
    </div>
  );
};

export default MedicationInput;
