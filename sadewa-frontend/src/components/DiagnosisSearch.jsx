// src/components/DiagnosisSearch.jsx - PERBAIKAN UNTUK SINGLE DIAGNOSIS
import React, { useState, useEffect, useRef } from "react";
import { Search, Plus, X, FileText, AlertCircle } from "lucide-react";
import { apiService } from "../services/api";

const DiagnosisSearch = ({
  selectedDiagnosis = null, // ✅ UBAH ke single diagnosis
  onDiagnosisSelect, // ✅ UBAH nama function
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

  // ✅ PERBAIKI handler untuk single diagnosis
  const handleSelectDiagnosis = (diagnosis) => {
    onDiagnosisSelect(diagnosis); // Panggil function yang benar
    setSearchTerm("");
    setIsDropdownOpen(false);
  };

  // ✅ PERBAIKI handler untuk clear diagnosis
  const handleClearDiagnosis = () => {
    onDiagnosisSelect(null);
  };

  return (
    <div className={`${className}`}>
      <div className="flex items-center mb-4">
        <FileText className="w-5 h-5 text-blue-600 mr-2" />
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
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            disabled={selectedDiagnosis !== null} // Disable jika sudah ada diagnosis
          />
          {isSearching && (
            <div className="absolute right-3 top-3">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>

        {/* Search Results Dropdown */}
        {isDropdownOpen && searchResults.length > 0 && !selectedDiagnosis && (
          <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {searchResults.map((diagnosis) => (
              <button
                key={diagnosis.code}
                onClick={() => handleSelectDiagnosis(diagnosis)} // ✅ GUNAKAN handler yang benar
                className="w-full p-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none border-b border-gray-50 last:border-b-0"
              >
                <div className="flex items-start">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <span className="font-mono text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                        {diagnosis.code}
                      </span>
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
                  <Plus className="w-4 h-4 text-blue-500 mt-1 ml-2" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* No Results Message */}
        {isDropdownOpen &&
          searchResults.length === 0 &&
          searchTerm.length >= 2 &&
          !isSearching && (
            <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm text-gray-500">No diagnoses found</p>
              <p className="text-xs text-gray-400">
                Try different keywords or ICD-10 codes
              </p>
            </div>
          )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center text-red-600">
            <AlertCircle className="w-4 h-4 mr-2" />
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Usage Hint */}
      <p className="mt-3 text-xs text-gray-500">
        💡 Tip: Search by disease name or ICD-10 code. Example: "diabetes",
        "E11", "hypertension"
      </p>

      {/* ✅ SELECTED DIAGNOSIS DISPLAY - Single diagnosis */}
      {selectedDiagnosis && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Selected Diagnosis
          </h3>
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex-1">
              <div className="flex items-center mb-1">
                <span className="font-mono text-sm font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded mr-2">
                  {selectedDiagnosis.code}
                </span>
              </div>
              <p className="text-sm text-gray-900 font-medium">
                {selectedDiagnosis.name_id}
              </p>
              {selectedDiagnosis.name_en && (
                <p className="text-xs text-gray-500 mt-1">
                  {selectedDiagnosis.name_en}
                </p>
              )}
            </div>
            <button
              onClick={handleClearDiagnosis} // ✅ GUNAKAN handler yang benar
              className="ml-3 p-1 text-gray-400 hover:text-red-500 focus:text-red-500 focus:outline-none"
              title="Remove diagnosis"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!selectedDiagnosis && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 text-center">
          <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm text-gray-500">No diagnosis selected</p>
          <p className="text-xs text-gray-400">
            Search and select patient's primary diagnosis
          </p>
        </div>
      )}
    </div>
  );
};

export default DiagnosisSearch;
