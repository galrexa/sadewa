// src/components/MedicationInput.jsx
import React, { useState } from "react";
import { Plus, X, Pill, AlertCircle, Clock } from "lucide-react";

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

  // Common medications for quick add
  const commonMedications = [
    { name: "Paracetamol", dosage: "500mg", frequency: "3x daily" },
    { name: "Ibuprofen", dosage: "400mg", frequency: "As needed" },
    { name: "Amoxicillin", dosage: "500mg", frequency: "3x daily" },
    { name: "Omeprazole", dosage: "20mg", frequency: "Once daily" },
    { name: "Metformin", dosage: "500mg", frequency: "2x daily" },
    { name: "Amlodipine", dosage: "5mg", frequency: "Once daily" },
  ];

  const validateMedication = (med) => {
    const newErrors = {};

    if (!med.name.trim()) {
      newErrors.name = "Medication name is required";
    }

    if (!med.dosage.trim()) {
      newErrors.dosage = "Dosage is required";
    }

    if (!med.frequency.trim()) {
      newErrors.frequency = "Frequency is required";
    }

    // Check for duplicates
    const isDuplicate = medications.some(
      (existing) => existing.name.toLowerCase() === med.name.toLowerCase()
    );

    if (isDuplicate) {
      newErrors.name = "This medication is already added";
    }

    return newErrors;
  };

  const handleAddMedication = () => {
    const validationErrors = validateMedication(newMedication);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    const medicationToAdd = {
      id: Date.now().toString(),
      name: newMedication.name.trim(),
      dosage: newMedication.dosage.trim(),
      frequency: newMedication.frequency.trim(),
      notes: newMedication.notes.trim(),
      addedAt: new Date().toISOString(),
    };

    onMedicationsChange([...medications, medicationToAdd]);

    // Reset form
    setNewMedication({ name: "", dosage: "", frequency: "", notes: "" });
    setErrors({});
    setShowAddForm(false);
  };

  const handleQuickAdd = (commonMed) => {
    const medicationToAdd = {
      id: Date.now().toString(),
      ...commonMed,
      notes: "",
      addedAt: new Date().toISOString(),
    };

    // Check for duplicates
    const isDuplicate = medications.some(
      (existing) => existing.name.toLowerCase() === commonMed.name.toLowerCase()
    );

    if (!isDuplicate) {
      onMedicationsChange([...medications, medicationToAdd]);
    }
  };

  const handleRemoveMedication = (medicationId) => {
    const updatedMedications = medications.filter(
      (med) => med.id !== medicationId
    );
    onMedicationsChange(updatedMedications);
  };

  const handleInputChange = (field, value) => {
    setNewMedication((prev) => ({ ...prev, [field]: value }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Pill className="w-5 h-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">
            New Medications
          </h2>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn-primary flex items-center text-sm"
        >
          <Plus className="w-4 h-4 mr-1" />
          Add Medication
        </button>
      </div>

      {/* Quick Add Section */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          Quick Add (Common Medications)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {commonMedications.map((med, index) => (
            <button
              key={index}
              onClick={() => handleQuickAdd(med)}
              disabled={medications.some(
                (existing) =>
                  existing.name.toLowerCase() === med.name.toLowerCase()
              )}
              className="p-2 text-left border border-gray-200 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="text-sm font-medium text-gray-900">
                {med.name}
              </div>
              <div className="text-xs text-gray-500">
                {med.dosage} • {med.frequency}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Add Medication Form */}
      {showAddForm && (
        <div className="mb-6 p-4 border-2 border-primary-200 rounded-lg bg-primary-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-primary-900">Add New Medication</h3>
            <button
              onClick={() => {
                setShowAddForm(false);
                setNewMedication({
                  name: "",
                  dosage: "",
                  frequency: "",
                  notes: "",
                });
                setErrors({});
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Medication Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Medication Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={newMedication.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                placeholder="e.g., Paracetamol"
                className={`input-field ${
                  errors.name ? "border-red-300 focus:ring-red-500" : ""
                }`}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-red-600 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {errors.name}
                </p>
              )}
            </div>

            {/* Dosage */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dosage <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={newMedication.dosage}
                onChange={(e) => handleInputChange("dosage", e.target.value)}
                placeholder="e.g., 500mg"
                className={`input-field ${
                  errors.dosage ? "border-red-300 focus:ring-red-500" : ""
                }`}
              />
              {errors.dosage && (
                <p className="mt-1 text-xs text-red-600 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {errors.dosage}
                </p>
              )}
            </div>

            {/* Frequency */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequency <span className="text-red-500">*</span>
              </label>
              <select
                value={newMedication.frequency}
                onChange={(e) => handleInputChange("frequency", e.target.value)}
                className={`input-field ${
                  errors.frequency ? "border-red-300 focus:ring-red-500" : ""
                }`}
              >
                <option value="">Select frequency...</option>
                <option value="Once daily">Once daily</option>
                <option value="2x daily">2x daily</option>
                <option value="3x daily">3x daily</option>
                <option value="4x daily">4x daily</option>
                <option value="As needed">As needed</option>
                <option value="Before meals">Before meals</option>
                <option value="After meals">After meals</option>
              </select>
              {errors.frequency && (
                <p className="mt-1 text-xs text-red-600 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {errors.frequency}
                </p>
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
                onChange={(e) => handleInputChange("notes", e.target.value)}
                placeholder="e.g., Take with food"
                className="input-field"
              />
            </div>
          </div>

          <div className="flex justify-end mt-4 space-x-2">
            <button
              onClick={() => {
                setShowAddForm(false);
                setNewMedication({
                  name: "",
                  dosage: "",
                  frequency: "",
                  notes: "",
                });
                setErrors({});
              }}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button onClick={handleAddMedication} className="btn-primary">
              Add Medication
            </button>
          </div>
        </div>
      )}

      {/* Added Medications List */}
      {medications.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Added Medications ({medications.length})
          </h3>
          <div className="space-y-3">
            {medications.map((medication) => (
              <div
                key={medication.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <Pill className="w-4 h-4 text-primary-600 mr-2" />
                    <span className="font-medium text-gray-900">
                      {medication.name}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm text-gray-600">
                    <div className="flex items-center">
                      <span className="font-medium mr-1">Dosage:</span>
                      {medication.dosage}
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      <span className="font-medium mr-1">Frequency:</span>
                      {medication.frequency}
                    </div>
                    {medication.notes && (
                      <div className="col-span-1 md:col-span-3">
                        <span className="font-medium mr-1">Notes:</span>
                        {medication.notes}
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveMedication(medication.id)}
                  className="ml-4 p-2 text-gray-400 hover:text-red-500 focus:text-red-500 focus:outline-none"
                  title="Remove medication"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {medications.length === 0 && (
        <div className="p-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 text-center">
          <Pill className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm text-gray-500">No medications added</p>
          <p className="text-xs text-gray-400">
            Add medications to analyze potential interactions
          </p>
        </div>
      )}
    </div>
  );
};

export default MedicationInput;
