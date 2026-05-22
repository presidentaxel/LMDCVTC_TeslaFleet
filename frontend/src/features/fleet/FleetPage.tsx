import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBusinessStatus, listBusinessVehicles } from "../../lib/api";

export default function FleetPage() {
  const [status, setStatus] = useState<Awaited<ReturnType<typeof getBusinessStatus>> | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBusinessStatus().then(setStatus).catch(() => setStatus(null));
    listBusinessVehicles()
      .then((d) => {
        const list = Array.isArray(d.response) ? d.response : [];
        setCount(list.length);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <>
      <header className="page-header">
        <h1>Flotte</h1>
        <p>Vue d&apos;ensemble AXEL PROJECT — véhicules possédés et gérés.</p>
      </header>

      <div className="tabs">
        <button type="button" className="tab active">
          Owned Vehicles
        </button>
        <button type="button" className="tab" disabled title="Bientôt">
          Managed Vehicles
        </button>
      </div>

      {!status?.token_active && (
        <div className="alert alert-info">
          Flotte non connectée.{" "}
          <Link to="/setup">Configurer le consentement</Link>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16 }}>
        <div>
          <div style={{ fontSize: 12, color: "#5c5e62" }}>Véhicules</div>
          <div style={{ fontSize: 32, fontWeight: 600 }}>{count ?? "—"}</div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: "#5c5e62" }}>API</div>
          <div style={{ fontSize: 14 }}>{status?.audience?.split("/").pop() ?? "EU"}</div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: "#5c5e62" }}>Connexion</div>
          <span className={`badge ${status?.token_active ? "badge-ok" : "badge-warn"}`}>
            {status?.token_active ? "Connectée" : "En attente"}
          </span>
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <Link to="/vehicles" className="btn btn-primary">
          Voir les véhicules
        </Link>
      </div>
    </>
  );
}
