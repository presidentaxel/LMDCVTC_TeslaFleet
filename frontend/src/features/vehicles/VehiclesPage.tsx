import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBusinessStatus, listBusinessVehicles } from "../../lib/api";

type VehicleRow = {
  id?: number | string;
  vin?: string;
  display_name?: string;
  state?: string;
};

export default function VehiclesPage() {
  const [rows, setRows] = useState<VehicleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [selectedId, setSelectedId] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const st = await getBusinessStatus();
      setConnected(st.token_active);
      if (!st.token_active) {
        setRows([]);
        return;
      }
      const data = await listBusinessVehicles();
      const list = (Array.isArray(data.response) ? data.response : []) as VehicleRow[];
      setRows(list);
      if (list[0]?.id != null) setSelectedId(String(list[0].id));
      else if (list[0]?.vin) setSelectedId(list[0].vin!);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1>Véhicules</h1>
          <p>Liste des véhicules de la flotte business.</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={load} disabled={loading}>
          Actualiser
        </button>
      </header>

      {!connected && (
        <div className="alert alert-info">
          <Link to="/setup">Configurer le consentement</Link> pour afficher les véhicules.
        </div>
      )}
      {error && <div className="alert alert-error">{error}</div>}

      <div className="table-wrap card" style={{ padding: 0 }}>
        {loading ? (
          <div className="empty-state">Chargement…</div>
        ) : rows.length === 0 ? (
          <div className="empty-state">
            <h3>Aucun véhicule</h3>
            <p>Ajoutez un véhicule dans Tesla for Business ou vérifiez le consentement.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Véhicule</th>
                <th>VIN</th>
                <th>État</th>
                <th>ID API</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((v) => {
                const id = String(v.id ?? v.vin ?? "");
                return (
                  <tr key={id}>
                    <td>{v.display_name ?? "—"}</td>
                    <td><code style={{ fontSize: 12 }}>{v.vin ?? "—"}</code></td>
                    <td>{v.state ?? "—"}</td>
                    <td><code style={{ fontSize: 12 }}>{id}</code></td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: "6px 12px", fontSize: 12 }}
                        onClick={() => setSelectedId(id)}
                      >
                        Sélectionner
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {selectedId && (
        <p style={{ marginTop: 16, fontSize: 14 }}>
          Véhicule sélectionné : <code>{selectedId}</code> —{" "}
          <Link to={`/commands?vehicle=${encodeURIComponent(selectedId)}`}>Commandes</Link>
        </p>
      )}
    </>
  );
}
