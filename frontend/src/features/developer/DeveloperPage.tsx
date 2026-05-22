import { useEffect, useState } from "react";
import {
  apiHealth,
  getFleetAccessStatus,
  getPartnerFleetStatus,
  partnerTokenDebug,
} from "../../lib/api";

export default function DeveloperPage() {
  const [health, setHealth] = useState("");
  const [debug, setDebug] = useState("");
  const [access, setAccess] = useState("");
  const [partner, setPartner] = useState("");

  useEffect(() => {
    apiHealth().then((h) => setHealth(h.status)).catch((e) => setHealth(`err: ${e}`));
    getFleetAccessStatus()
      .then((s) => setAccess(JSON.stringify(s, null, 2)))
      .catch(() => setAccess("{}"));
    getPartnerFleetStatus()
      .then((s) => setPartner(JSON.stringify(s, null, 2)))
      .catch(() => setPartner("{}"));
  }, []);

  async function loadDebug() {
    try {
      const d = await partnerTokenDebug(true);
      setDebug(JSON.stringify(d, null, 2));
    } catch (e) {
      setDebug(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <>
      <header className="page-header">
        <h1>Développeur</h1>
        <p>Diagnostics API — token M2M (client_credentials) en priorité.</p>
      </header>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Santé API</h3>
        <code>{health || "…"}</code>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Accès flotte (agrégé)</h3>
        <pre style={{ fontSize: 12, overflow: "auto" }}>{access}</pre>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Token M2M partenaire</h3>
        <pre style={{ fontSize: 12, overflow: "auto" }}>{partner}</pre>
      </div>

      <div className="card">
        <button type="button" className="btn btn-secondary" onClick={loadDebug}>
          token-debug (?refresh=1)
        </button>
        {debug && (
          <pre style={{ marginTop: 12, fontSize: 11, overflow: "auto", background: "#f4f4f4", padding: 12 }}>
            {debug}
          </pre>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Endpoints utiles</h3>
        <ul style={{ fontSize: 14, lineHeight: 1.8 }}>
          <li>
            <code>GET /api/fleet/partner/status</code> — cache M2M
          </li>
          <li>
            <code>GET /api/fleet/partner/token-debug?refresh=1</code> — nouveau token Tesla
          </li>
          <li>
            <code>GET /api/fleet/vehicles</code> — liste (Bearer auto)
          </li>
          <li>
            <code>POST /api/fleet/partner/register</code> — domaine (412)
          </li>
        </ul>
      </div>
    </>
  );
}
