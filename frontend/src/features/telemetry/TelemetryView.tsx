import { useEffect, useState } from "react";

export default function TelemetryView() {
  const [lines, setLines] = useState<string[]>([]);
  const [enabled, setEnabled] = useState(false);
  
  useEffect(() => {
    // Ne se connecter que si VITE_TELEMETRY_URL est explicitement configuré
    const telemetryUrl = import.meta.env.VITE_TELEMETRY_URL;
    if (!telemetryUrl) {
      return; // Service de télémetry non configuré, ne rien faire
    }

    setEnabled(true);
    const es = new EventSource(telemetryUrl);
    
    es.onmessage = (e) => setLines((prev) => [e.data, ...prev].slice(0, 20));
    es.onerror = () => {
      console.warn("SSE error - Service de télémetry non disponible");
      setEnabled(false);
    };
    
    return () => es.close();
  }, []);

  // Ne rien afficher si le service n'est pas configuré
  if (!import.meta.env.VITE_TELEMETRY_URL) {
    return null;
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Telemetry (SSE)</h2>
      {enabled ? (
        <pre>{lines.length > 0 ? lines.join("\n") : "En attente de données..."}</pre>
      ) : (
        <p style={{ color: "#999" }}>Service de télémetry non disponible</p>
      )}
    </div>
  );
}