import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import TelemetryView from "./features/telemetry/TelemetryView";
import AuthPage from "./components/AuthPage";
import { apiHealth, type HealthResponse } from "./lib/api";
import "./App.css";

function Home() {
  const [health, setHealth] = useState<string>("checking...");

  useEffect(() => {
    apiHealth()
      .then((d: HealthResponse) => setHealth(d.status))
      .catch((e: unknown) => setHealth(`error: ${e instanceof Error ? e.message : String(e)}`));
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: 16 }}>
      <nav style={{ marginBottom: 20, padding: 16, background: "#f5f5f5", borderRadius: 8 }}>
        <Link to="/" style={{ marginRight: 16 }}>Accueil</Link>
        <Link to="/auth">Connexion Tesla</Link>
      </nav>
      <h1>Tesla Fleet Frontend</h1>
      <p>API health: {health}</p>
      <TelemetryView />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/auth" element={<AuthPage />} />
      </Routes>
    </BrowserRouter>
  );
}