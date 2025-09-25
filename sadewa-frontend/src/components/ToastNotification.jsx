import React, { useState, useEffect } from "react";
import { CheckCircle, X, AlertTriangle, Info, XCircle } from "lucide-react";

// Toast Provider Context
const ToastContext = React.createContext();

// Toast Hook
export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};

// Toast Item Component with inline styles for reliability
const ToastItem = ({ toast, onRemove }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Animate in
    setTimeout(() => setIsVisible(true), 100);

    // Auto dismiss
    const timer = setTimeout(() => {
      handleDismiss();
    }, toast.duration || 5000);

    return () => clearTimeout(timer);
  }, []);

  const handleDismiss = () => {
    setIsLeaving(true);
    setTimeout(() => {
      onRemove(toast.id);
    }, 300);
  };

  const getToastStyles = () => {
    const baseStyles = {
      transform: isVisible && !isLeaving ? "translateX(0)" : "translateX(100%)",
      opacity: isVisible && !isLeaving ? 1 : 0,
      transition: "all 0.3s ease-in-out",
      marginBottom: "16px",
      maxWidth: "400px",
      width: "100%",
      background: "white",
      borderRadius: "8px",
      boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)",
      border: "1px solid #e5e7eb",
      overflow: "hidden",
      position: "relative",
    };

    let borderColor = "#3b82f6"; // blue
    if (toast.type === "success") borderColor = "#10b981"; // green
    if (toast.type === "error") borderColor = "#ef4444"; // red
    if (toast.type === "warning") borderColor = "#f59e0b"; // yellow

    return {
      ...baseStyles,
      borderLeft: `4px solid ${borderColor}`,
    };
  };

  const getIcon = () => {
    const iconProps = {
      size: 20,
      style: { marginRight: "12px", flexShrink: 0 },
    };

    switch (toast.type) {
      case "success":
        return (
          <CheckCircle
            {...iconProps}
            style={{ ...iconProps.style, color: "#10b981" }}
          />
        );
      case "error":
        return (
          <XCircle
            {...iconProps}
            style={{ ...iconProps.style, color: "#ef4444" }}
          />
        );
      case "warning":
        return (
          <AlertTriangle
            {...iconProps}
            style={{ ...iconProps.style, color: "#f59e0b" }}
          />
        );
      case "info":
      default:
        return (
          <Info
            {...iconProps}
            style={{ ...iconProps.style, color: "#3b82f6" }}
          />
        );
    }
  };

  return (
    <div style={getToastStyles()}>
      <div
        style={{
          padding: "16px",
          display: "flex",
          alignItems: "flex-start",
          paddingRight: "48px",
        }}
      >
        {getIcon()}
        <div style={{ flex: 1, minWidth: 0 }}>
          {toast.title && (
            <div
              style={{
                fontWeight: "600",
                fontSize: "14px",
                color: "#111827",
                marginBottom: "4px",
                lineHeight: "1.4",
              }}
            >
              {toast.title}
            </div>
          )}
          <div
            style={{
              fontSize: "13px",
              color: "#6b7280",
              lineHeight: "1.4",
              wordWrap: "break-word",
            }}
          >
            {toast.message}
          </div>
        </div>
      </div>

      {/* Close button */}
      <button
        onClick={handleDismiss}
        style={{
          position: "absolute",
          top: "12px",
          right: "12px",
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "4px",
          borderRadius: "4px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#6b7280",
          transition: "color 0.2s",
        }}
        onMouseEnter={(e) => (e.target.style.color = "#374151")}
        onMouseLeave={(e) => (e.target.style.color = "#6b7280")}
      >
        <X size={16} />
      </button>

      {/* Progress bar */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          height: "3px",
          background:
            toast.type === "success"
              ? "#10b981"
              : toast.type === "error"
              ? "#ef4444"
              : toast.type === "warning"
              ? "#f59e0b"
              : "#3b82f6",
          animation: `shrink ${toast.duration || 5000}ms linear`,
          transformOrigin: "left",
        }}
      />

      <style>
        {`
          @keyframes shrink {
            from { width: 100%; }
            to { width: 0%; }
          }
        `}
      </style>
    </div>
  );
};

// Toast Container
const ToastContainer = ({ toasts, removeToast }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: "20px",
        right: "20px",
        zIndex: 9999,
        pointerEvents: "none",
      }}
    >
      {toasts.map((toast) => (
        <div key={toast.id} style={{ pointerEvents: "auto" }}>
          <ToastItem toast={toast} onRemove={removeToast} />
        </div>
      ))}
    </div>
  );
};

// Toast Provider Component
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = (toast) => {
    const id = Date.now() + Math.random();
    const newToast = {
      id,
      type: "info",
      duration: 5000,
      ...toast,
    };

    setToasts((prev) => [...prev, newToast]);
    return id;
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const removeAllToasts = () => {
    setToasts([]);
  };

  // Convenience methods
  const success = (message, options = {}) => {
    return addToast({
      type: "success",
      message,
      ...options,
    });
  };

  const error = (message, options = {}) => {
    return addToast({
      type: "error",
      message,
      duration: 8000,
      ...options,
    });
  };

  const warning = (message, options = {}) => {
    return addToast({
      type: "warning",
      message,
      ...options,
    });
  };

  const info = (message, options = {}) => {
    return addToast({
      type: "info",
      message,
      ...options,
    });
  };

  const value = {
    toasts,
    addToast,
    removeToast,
    removeAllToasts,
    success,
    error,
    warning,
    info,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
};

// Demo component
function ToastDemo() {
  const toast = useToast();

  const showSuccessToast = () => {
    toast.success("Diagnosis berhasil disimpan ke rekam medis!", {
      title: "Berhasil!",
      duration: 4000,
    });
  };

  const showErrorToast = () => {
    toast.error("Gagal menyimpan diagnosis. Silakan coba lagi.", {
      title: "Error",
    });
  };

  const showWarningToast = () => {
    toast.warning("Pastikan semua field sudah diisi dengan benar.", {
      title: "Peringatan",
    });
  };

  const showInfoToast = () => {
    toast.info("Data pasien telah diperbarui.", {
      title: "Informasi",
    });
  };

  return (
    <div style={{ padding: "32px", maxWidth: "800px", margin: "0 auto" }}>
      <h2
        style={{
          fontSize: "24px",
          fontWeight: "bold",
          color: "#1f2937",
          marginBottom: "24px",
        }}
      >
        Toast Notification Demo
      </h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: "16px",
          marginBottom: "32px",
        }}
      >
        <button
          onClick={showSuccessToast}
          style={{
            padding: "12px 16px",
            backgroundColor: "#10b981",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) => (e.target.style.backgroundColor = "#059669")}
          onMouseLeave={(e) => (e.target.style.backgroundColor = "#10b981")}
        >
          Success Toast
        </button>

        <button
          onClick={showErrorToast}
          style={{
            padding: "12px 16px",
            backgroundColor: "#ef4444",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) => (e.target.style.backgroundColor = "#dc2626")}
          onMouseLeave={(e) => (e.target.style.backgroundColor = "#ef4444")}
        >
          Error Toast
        </button>

        <button
          onClick={showWarningToast}
          style={{
            padding: "12px 16px",
            backgroundColor: "#f59e0b",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) => (e.target.style.backgroundColor = "#d97706")}
          onMouseLeave={(e) => (e.target.style.backgroundColor = "#f59e0b")}
        >
          Warning Toast
        </button>

        <button
          onClick={showInfoToast}
          style={{
            padding: "12px 16px",
            backgroundColor: "#3b82f6",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) => (e.target.style.backgroundColor = "#2563eb")}
          onMouseLeave={(e) => (e.target.style.backgroundColor = "#3b82f6")}
        >
          Info Toast
        </button>
      </div>

      <div
        style={{
          marginTop: "32px",
          padding: "16px",
          backgroundColor: "#f3f4f6",
          borderRadius: "8px",
        }}
      >
        <h3
          style={{ fontSize: "16px", fontWeight: "600", marginBottom: "8px" }}
        >
          Penggunaan:
        </h3>
        <pre
          style={{
            fontSize: "12px",
            backgroundColor: "#1f2937",
            color: "#10b981",
            padding: "12px",
            borderRadius: "4px",
            overflow: "auto",
            margin: 0,
          }}
        >
          {`// 1. Wrap app dengan ToastProvider
// 2. Import useToast hook  
// 3. const toast = useToast();
// 4. toast.success("Message");`}
        </pre>
      </div>
    </div>
  );
}

// Export wrapped component
export default function App() {
  return (
    <ToastProvider>
      <ToastDemo />
    </ToastProvider>
  );
}
