// sadewa-frontend/src/components/Navigation.jsx
import React, { useState } from "react";
import {
  Home,
  Users,
  UserPlus,
  Pill,
  Menu,
  X,
  Shield,
  Activity,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

const Navigation = ({ activeTab, onTabChange, patientCount = 0 }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isPatientMenuOpen, setIsPatientMenuOpen] = useState(false);

  const navigationItems = [
    {
      id: "dashboard",
      name: "Dashboard",
      icon: Home,
      description: "Halaman utama sistem",
    },
    {
      id: "drug-analysis",
      name: "Analisis Obat",
      icon: Pill,
      description: "Analisis interaksi obat",
    },
    {
      id: "patients",
      name: "Manajemen Pasien",
      icon: Users,
      description: `Kelola data pasien (${patientCount})`,
      hasSubmenu: true,
      submenu: [
        {
          id: "patient-list",
          name: "Daftar Pasien",
          icon: Users,
          description: "Lihat semua pasien",
        },
        {
          id: "patient-registration",
          name: "Tambah Pasien",
          icon: UserPlus,
          description: "Daftarkan pasien baru",
        },
      ],
    },
  ];

  const handleTabChange = (tabId) => {
    onTabChange(tabId);
    setIsMobileMenuOpen(false);

    // Close patient submenu when switching to other main tabs
    if (
      tabId !== "patients" &&
      tabId !== "patient-list" &&
      tabId !== "patient-registration"
    ) {
      setIsPatientMenuOpen(false);
    }
  };

  const handlePatientMenuToggle = () => {
    setIsPatientMenuOpen(!isPatientMenuOpen);
    if (!isPatientMenuOpen) {
      onTabChange("patients");
    }
  };

  const renderMenuItem = (item, isSubmenu = false) => {
    const Icon = item.icon;
    const isActive = activeTab === item.id;
    const hasActiveSubmenu = item.submenu?.some((sub) => activeTab === sub.id);

    return (
      <div key={item.id} className={isSubmenu ? "ml-4" : ""}>
        <button
          onClick={
            item.hasSubmenu
              ? handlePatientMenuToggle
              : () => handleTabChange(item.id)
          }
          className={`w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg transition-all duration-200 ${
            isActive || hasActiveSubmenu
              ? "bg-blue-100 text-blue-700 shadow-sm"
              : "text-gray-700 hover:bg-gray-100"
          } ${isSubmenu ? "text-sm" : ""}`}
        >
          <Icon
            className={`${isSubmenu ? "h-4 w-4" : "h-5 w-5"} ${
              isActive || hasActiveSubmenu ? "text-blue-600" : "text-gray-500"
            }`}
          />

          <div className="flex-1 min-w-0">
            <div className={`font-medium ${isSubmenu ? "text-sm" : ""}`}>
              {item.name}
            </div>
            {item.description && (
              <div
                className={`text-xs text-gray-500 ${isSubmenu ? "hidden" : ""}`}
              >
                {item.description}
              </div>
            )}
          </div>

          {item.hasSubmenu && (
            <div className="transition-transform duration-200">
              {isPatientMenuOpen ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </div>
          )}
        </button>

        {/* Submenu */}
        {item.hasSubmenu && isPatientMenuOpen && (
          <div className="mt-2 space-y-1 ml-4 pl-4 border-l-2 border-gray-200">
            {item.submenu.map((subItem) => renderMenuItem(subItem, true))}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:block w-64 bg-white shadow-lg h-screen sticky top-0">
        <div className="p-6">
          {/* Logo/Header */}
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Shield className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">SADEWA</h1>
              <p className="text-xs text-gray-500">Smart Drug Analysis</p>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="space-y-2">
            {navigationItems.map((item) => renderMenuItem(item))}
          </div>

          {/* Status Section */}
          <div className="mt-8 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">
                Status Sistem
              </span>
            </div>
            <div className="text-xs text-green-700">
              ✓ Database Connected
              <br />
              ✓ API Services Online
              <br />✓ Drug Analysis Ready
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <div className="md:hidden">
        {/* Mobile Header */}
        <div className="bg-white shadow-sm border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Shield className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900">SADEWA</h1>
              <p className="text-xs text-gray-500">Smart Drug Analysis</p>
            </div>
          </div>

          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            {isMobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>

        {/* Mobile Menu Overlay */}
        {isMobileMenuOpen && (
          <>
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40"
              onClick={() => setIsMobileMenuOpen(false)}
            />

            <div className="fixed top-0 right-0 h-full w-80 bg-white shadow-xl z-50 p-6 overflow-y-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Menu</h2>
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-2">
                {navigationItems.map((item) => renderMenuItem(item))}
              </div>

              {/* Mobile Status */}
              <div className="mt-8 p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium text-green-800">
                    Status Sistem
                  </span>
                </div>
                <div className="text-xs text-green-700">
                  ✓ Database Connected
                  <br />
                  ✓ API Services Online
                  <br />✓ Drug Analysis Ready
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Breadcrumb for mobile */}
      <div className="md:hidden bg-gray-50 px-4 py-2 text-sm">
        <div className="flex items-center text-gray-600">
          <Home className="h-4 w-4 mr-1" />
          <span>SADEWA</span>
          <span className="mx-2">Arah kanan</span>
          <span className="text-gray-900 font-medium">
            {navigationItems.find((item) => item.id === activeTab)?.name ||
              navigationItems
                .flatMap((item) => item.submenu || [])
                .find((sub) => sub.id === activeTab)?.name ||
              "Dashboard"}
          </span>
        </div>
      </div>
    </>
  );
};

export default Navigation;
