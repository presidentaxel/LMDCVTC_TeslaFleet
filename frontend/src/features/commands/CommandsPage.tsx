import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { getCommandCatalog, runCommand } from "../../lib/api";

export default function CommandsPage() {
  const [params] = useSearchParams();
  const vehicleFromUrl = params.get("vehicle") ?? "";
  const [vehicleRef, setVehicleRef] = useState(vehicleFromUrl);
  const [catalog, setCatalog] = useState<Record<string, { name: string; label_fr: string; needs_body: boolean; body_hint: string | null }[]>>({});
  const [category, setCategory] = useState<string>("essentiel");
  const [bodyJson, setBodyJson] = useState("{}");
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setVehicleRef(vehicleFromUrl);
  }, [vehicleFromUrl]);

  useEffect(() => {
    getCommandCatalog()
      .then((c) => {
        setCatalog(c.categories);
        const first = Object.keys(c.categories)[0];
        if (first) setCategory(first);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const commands = useMemo(() => catalog[category] ?? [], [catalog, category]);

  const run = useCallback(
    async (commandName: string, needsBody: boolean) => {
      if (!vehicleRef.trim()) {
        setError("Indiquez un ID ou VIN véhicule.");
        return;
      }
      setLoading(true);
      setError(null);
      setResult("");
      try {
        let body: Record<string, unknown> | undefined;
        if (needsBody) {
          body = JSON.parse(bodyJson || "{}") as Record<string, unknown>;
        }
        const res = await runCommand(vehicleRef.trim(), commandName, body);
        setResult(JSON.stringify(res, null, 2));
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [vehicleRef, bodyJson],
  );

  const categories = Object.keys(catalog);

  return (
    <>
      <header className="page-header">
        <h1>Commandes</h1>
        <p>Contrôle à distance : sécurité, recharge, média, climat.</p>
      </header>

      <div className="card">
        <label style={{ fontSize: 12, color: "#5c5e62" }}>Véhicule (ID ou VIN)</label>
        <input
          className="input"
          value={vehicleRef}
          onChange={(e) => setVehicleRef(e.target.value)}
          placeholder="ID depuis la liste véhicules"
          style={{ marginTop: 6 }}
        />
        <p style={{ fontSize: 12, color: "#5c5e62", marginTop: 8 }}>
          <Link to="/vehicles">Choisir dans la liste</Link> · Clé virtuelle requise pour certaines commandes
        </p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="tabs" style={{ flexWrap: "wrap" }}>
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`tab${category === cat ? " active" : ""}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="card">
        <label style={{ fontSize: 12, color: "#5c5e62" }}>Corps JSON (commandes avancées)</label>
        <textarea
          className="input"
          rows={3}
          value={bodyJson}
          onChange={(e) => setBodyJson(e.target.value)}
          style={{ marginTop: 6, fontFamily: "monospace" }}
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
        {commands.map((cmd) => (
          <button
            key={cmd.name}
            type="button"
            className="card"
            style={{ textAlign: "left", cursor: "pointer" }}
            disabled={loading}
            onClick={() => run(cmd.name, cmd.needs_body)}
            title={cmd.body_hint ?? undefined}
          >
            <div style={{ fontWeight: 600, fontSize: 14 }}>{cmd.label_fr}</div>
            <code style={{ fontSize: 11, color: "#5c5e62" }}>{cmd.name}</code>
          </button>
        ))}
      </div>

      {result && (
        <pre className="card" style={{ background: "#f4f4f4", overflow: "auto", fontSize: 12 }}>
          {result}
        </pre>
      )}
    </>
  );
}
