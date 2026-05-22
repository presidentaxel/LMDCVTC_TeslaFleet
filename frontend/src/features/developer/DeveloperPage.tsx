import { useEffect, useState } from "react";
import { apiHealth, getBusinessStatus, partnerTokenDebug } from "../../lib/api";

export default function DeveloperPage() {
  const [health, setHealth] = useState("");
  const [debug, setDebug] = useState("");
  const [biz, setBiz] = useState("");

  useEffect(() => {
    apiHealth().then((h) => setHealth(h.status)).catch((e) => setHealth(`err: ${e}`));
    getBusinessStatus().then((s) => setBiz(JSON.stringify(s, null, 2))).catch(() => setBiz("{}"));
  }, []);

  async function loadDebug() {
    try {
      const d = await partnerTokenDebug(false);
      setDebug(JSON.stringify(d, null, 2));
    } catch (e) {
      setDebug(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <>
      <header className="page-header">
        <h1>Développeur</h1>
        <p>Diagnostics API — local puis production OVH.</p>
      </header>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Santé API</h3>
        <code>{health || "…"}</code>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Business status</h3>
        <pre style={{ fontSize: 12, overflow: "auto" }}>{biz}</pre>
      </div>

      <div className="card">
        <button type="button" className="btn btn-secondary" onClick={loadDebug}>
          Charger token-debug partenaire
        </button>
        {debug && (
          <pre style={{ marginTop: 12, fontSize: 11, overflow: "auto", background: "#f4f4f4", padding: 12 }}>
            {debug}
          </pre>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Variables locales (.env)</h3>
        <ul style={{ fontSize: 14, lineHeight: 1.8 }}>
          <li><code>TESLA_CLIENT_ID=0517a56f-d3fd-43f5-9b80-5e15b0488d5f</code></li>
          <li><code>TESLA_CLIENT_SECRET=</code> (secret du portail)</li>
          <li><code>TOKEN_STORE_TYPE=memory</code> en dev sans Supabase</li>
          <li><code>APP_DOMAIN=teslapi.axelproject.fr</code> en prod</li>
        </ul>
      </div>
    </>
  );
}
