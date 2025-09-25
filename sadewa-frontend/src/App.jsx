import React from "react";
import Dashboard from "./pages/Dashboard";
import { ToastProvider } from "./components/ToastNotification";
import "./index.css";

function App() {
  return (
    <ToastProvider>
      <div className="App">
        <Dashboard />
      </div>
    </ToastProvider>
  );
}

export default App;
