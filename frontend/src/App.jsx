import { useEffect, useState } from "react";
import { Route, BrowserRouter, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Assessment from "./pages/Assessment";
import Results from "./pages/Results";
import Climate from "./pages/Climate";
import { getHealth } from "./api";

export default function App() {
  const [backendOk, setBackendOk] = useState(null);

  useEffect(() => {
    getHealth()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-field-50">
        <Navbar />
        {backendOk === false && (
          <div className="bg-rose-50 px-4 py-2 text-center text-sm text-rose-700">
            Could not reach the backend API. Start the Flask server (see backend/README),
            then refresh.
          </div>
        )}
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assess" element={<Assessment />} />
            <Route path="/results" element={<Results />} />
            <Route path="/climate" element={<Climate />} />
          </Routes>
        </main>
        <footer className="mt-10 border-t border-field-200 py-6 text-center text-xs text-field-500">
          Field Shift &middot; NASA Space Apps &middot; Sheikhupura, Punjab, Pakistan &middot;
          Historical data 2016-2025
        </footer>
      </div>
    </BrowserRouter>
  );
}
