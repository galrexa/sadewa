// src/components/DiagnosisSearch.jsx
import React, { useState, useEffect, useRef } from "react";
import { Search, Plus, X, FileText, AlertCircle } from "lucide-react";
import { apiService } from "../services/api";

const DiagnosisSearch = ({
  selectedDiagnoses = [],
  onDiagnosesChange,
  className = "",
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [error, setError] = useState(null);

  const searchTimeoutRef = useRef(null);
  const dropdownRef = useRef(null);

  // Debounced search
  useEffect(() => {
    if (searchTerm.length >= 2) {
      setIsSearching(true);

      // Clear previous timeout
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      // Set new timeout
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          const result = await apiService.searchICD10(searchTerm, 10);
          setSearchResults(result.data);
          setIsDropdownOpen(true);
          setError(null);
        } catch (err) {
          setError(err.message);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      }, 300);
    } else {
      setSearchResults([]);
      setIsDropdownOpen(false);
      setIsSearching(false);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchTerm]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleAddDiagnosis = (diagnosis) => {
    // Check if diagnosis already exists
    const isAlreadySelected = selectedDiagnoses.some(
      (d) => d.code === diagnosis.code
    );

    if (!isAlreadySelected) {
      const updatedDiagnoses = [...selectedDiagnoses, diagnosis];
      onDiagnosesChange(updatedDiagnoses);
    }

    setSearchTerm("");
    setIsDropdownOpen(false);
  };

  const handleRemoveDiagnosis = (diagnosisCode) => {
    const updatedDiagnoses = selectedDiagnoses.filter(
      (d) => d.code !== diagnosisCode
    );
    onDiagnosesChange(updatedDiagnoses);
  };

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center mb-4">
        <FileText className="w-5 h-5 text-primary-600 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">
          Diagnosis (ICD-10)
        </h2>
      </div>

      {/* Search Input */}
      <div className="relative" ref={dropdownRef}>
        <div className="relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search diagnosis (e.g., diabetes, hypertension)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10 pr-10"
          />
          {isSearching && (
            <div className="absolute right-3 top-3">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
            </div>
          )}
        </div>

        {/* Search Results Dropdown */}
        {isDropdownOpen && searchResults.length > 0 && (
          <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {searchResults.map((diagnosis) => (
              <button
                key={diagnosis.code}
                onClick={() => handleAddDiagnosis(diagnosis)}
                className="w-full p-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none border-b border-gray-50 last:border-b-0"
                disabled={selectedDiagnoses.some(
                  (d) => d.code === diagnosis.code
                )}
              >
                <div className="flex items-start">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <span className="font-mono text-sm font-medium text-primary-600 bg-primary-50 px-2 py-1 rounded">
                        {diagnosis.code}
                      </span>
                      {selectedDiagnoses.some(
                        (d) => d.code === diagnosis.code
                      ) && (
                        <span className="ml-2 text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                          Already selected
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-900 font-medium">
                      {diagnosis.name_id}
                    </p>
                    {diagnosis.name_en && (
                      <p className="text-xs text-gray-500 mt-1">
                        {diagnosis.name_en}
                      </p>
                    )}
                  </div>
                  <Plus className="w-4 h-4 text-gray-400 mt-1" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* No Results */}
        {isDropdownOpen &&
          searchResults.length === 0 &&
          searchTerm.length >= 2 &&
          !isSearching && (
            <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center">
              <Search className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-gray-500">No diagnosis found</p>
              <p className="text-sm text-gray-400">Try different keywords</p>
            </div>
          )}

        {/* Error Message */}
        {error && (
          <div className="absolute z-50 w-full mt-2 bg-white border border-red-200 rounded-lg shadow-lg p-4">
            <div className="flex items-center text-red-600">
              <AlertCircle className="w-4 h-4 mr-2" />
              <p className="text-sm">Error: {error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Search Helper */}
      <p className="text-xs text-gray-500 mt-2">
        💡 Type at least 2 characters to search. Example: "diabetes", "E11",
        "hypertension"
      </p>

      {/* Selected Diagnoses */}
      {selectedDiagnoses.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Selected Diagnoses ({selectedDiagnoses.length})
          </h3>
          <div className="space-y-2">
            {selectedDiagnoses.map((diagnosis) => (
              <div
                key={diagnosis.code}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="flex-1">
                  <div className="flex items-center mb-1">
                    <span className="font-mono text-sm font-medium text-primary-600 bg-primary-100 px-2 py-1 rounded mr-2">
                      {diagnosis.code}
                    </span>
                  </div>
                  <p className="text-sm text-gray-900 font-medium">
                    {diagnosis.name_id}
                  </p>
                </div>
                <button
                  onClick={() => handleRemoveDiagnosis(diagnosis.code)}
                  className="ml-3 p-1 text-gray-400 hover:text-red-500 focus:text-red-500 focus:outline-none"
                  title="Remove diagnosis"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {selectedDiagnoses.length === 0 && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 text-center">
          <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm text-gray-500">No diagnoses selected</p>
          <p className="text-xs text-gray-400">
            Search and add patient's current diagnoses
          </p>
        </div>
      )}
    </div>
  );
};

export default DiagnosisSearch;
