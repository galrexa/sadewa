// src/components/PatientSelector.jsx
import React, { useState, useEffect } from "react";
import { Users, ChevronDown, Search, User } from "lucide-react";
import { apiService } from "../services/api";

const PatientSelector = ({
  selectedPatient,
  onPatientSelect,
  className = "",
}) => {
  const [patients, setPatients] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const result = await apiService.getAllPatients();
      setPatients(result.data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error("Error fetching patients:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPatients = patients.filter(
    (patient) =>
      patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handlePatientSelect = (patient) => {
    onPatientSelect(patient);
    setIsOpen(false);
    setSearchTerm("");
  };

  if (loading) {
    return (
      <div className={`card ${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Loading patients...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`card border-red-200 ${className}`}>
        <div className="flex items-center text-red-600">
          <div className="text-red-500 mr-3">⚠️</div>
          <div>
            <p className="font-medium">Error loading patients</p>
            <p className="text-sm text-red-500">{error}</p>
            <button
              onClick={fetchPatients}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center mb-4">
        <Users className="w-5 h-5 text-primary-600 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">Select Patient</h2>
      </div>

      <div className="relative">
        {/* Selected Patient Display */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full p-4 text-left bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors duration-200"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <User className="w-5 h-5 text-gray-400 mr-3" />
              <div>
                {selectedPatient ? (
                  <>
                    <p className="font-medium text-gray-900">
                      {selectedPatient.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {selectedPatient.id} • {selectedPatient.age} years •{" "}
                      {selectedPatient.gender}
                    </p>
                  </>
                ) : (
                  <p className="text-gray-500">Choose a patient...</p>
                )}
              </div>
            </div>
            <ChevronDown
              className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                isOpen ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>

        {/* Dropdown */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
            {/* Search Box */}
            <div className="p-3 border-b border-gray-100">
              <div className="relative">
                <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search patients..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Patient List */}
            <div className="max-h-60 overflow-y-auto">
              {filteredPatients.length > 0 ? (
                filteredPatients.map((patient) => (
                  <button
                    key={patient.id}
                    onClick={() => handlePatientSelect(patient)}
                    className="w-full p-4 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none border-b border-gray-50 last:border-b-0"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mr-3">
                        <User className="w-5 h-5 text-primary-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          {patient.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {patient.id} • {patient.age} years • {patient.gender}
                        </p>
                        {patient.current_medications &&
                          patient.current_medications.length > 0 && (
                            <p className="text-xs text-primary-600 mt-1">
                              {patient.current_medications.length} active
                              medications
                            </p>
                          )}
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="p-4 text-center text-gray-500">
                  <Search className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>No patients found</p>
                  <p className="text-sm">Try adjusting your search</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Patient Summary */}
      {selectedPatient && (
        <div className="mt-4 p-4 bg-primary-50 rounded-lg border border-primary-100">
          <h3 className="font-medium text-primary-900 mb-2">
            Current Medications
          </h3>
          {selectedPatient.current_medications &&
          selectedPatient.current_medications.length > 0 ? (
            <div className="space-y-1">
              {selectedPatient.current_medications.map((med, index) => (
                <div
                  key={index}
                  className="text-sm text-primary-700 bg-white px-2 py-1 rounded"
                >
                  💊 {med}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-primary-600">No active medications</p>
          )}
        </div>
      )}
    </div>
  );
};

export default PatientSelector;
