import { useEffect, useState } from "react";

export default function TelemetryView() {
  const [lines, setLines] = useState<string[]>([]);
  useEffect(() => {
    const url = import.meta.env.VITE_TELEMETRY_URL ?? "http://localhost:8001/telemetry/stream";
    const es = new EventSource(url);
    es.onmessage = (e) => setLines((prev) => [e.data, ...prev].slice(0, 20));
    es.onerror = () => console.warn("SSE error");
    return () => es.close();
  }, []);
  return (
    <div style={{ padding: 16 }}>
      <h2>Telemetry (SSE)</h2>
      <pre>{lines.join("\n")}</pre>
    </div>
  );
}