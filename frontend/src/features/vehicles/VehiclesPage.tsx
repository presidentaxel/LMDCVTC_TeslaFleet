import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getFleetAccessStatus,
  listFleetVehicles,
  parseVehicleList,
} from "../../lib/api";

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
  const [mode, setMode] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const st = await getFleetAccessStatus();
      setConnected(st.token_active);
      setMode(st.active_mode);
      if (!st.token_active) {
        setRows([]);
        return;
      }
      const data = await listFleetVehicles();
      const list = parseVehicleList(data) as VehicleRow[];
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
          <p>
            Liste via token API
            {mode ? ` (${mode === "partner" ? "M2M" : "business"})` : ""} — Bearer géré par le backend.
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={load} disabled={loading}>
          Actualiser
        </button>
      </header>

      {!connected && (
        <div className="alert alert-info">
          <Link to="/setup">Configuration → Token M2M</Link> : cliquez « Obtenir token M2M » puis « Tester liste
          véhicules ».
        </div>
      )}
      {error && <div className="alert alert-error">{error}</div>}

      <div className="table-wrap card" style={{ padding: 0 }}>
        {loading ? (
          <div className="empty-state">Chargement…</div>
        ) : rows.length === 0 ? (
          <div className="empty-state">
            <h3>Aucun véhicule</h3>
            <p>
              Véhicules dans Tesla for Business, token M2M obtenu, et domaine enregistré (onglet Infra).
            </p>
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
                    <td>{v.display_name ?? "-"}</td>
                    <td>
                      <code style={{ fontSize: 12 }}>{v.vin ?? "-"}</code>
                    </td>
                    <td>{v.state ?? "-"}</td>
                    <td>
                      <code style={{ fontSize: 12 }}>{id}</code>
                    </td>
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
          Véhicule sélectionné : <code>{selectedId}</code> -{" "}
          <Link to={`/commands?vehicle=${encodeURIComponent(selectedId)}`}>Commandes</Link>
        </p>
      )}
    </>
  );
}
