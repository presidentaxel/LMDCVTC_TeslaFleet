import { useCallback, useEffect, useState } from "react";
import {
  acquirePartnerToken,
  exchangeBusinessCode,
  getBusinessStatus,
  getConsentGuide,
  getPartnerFleetStatus,
  listFleetVehicles,
  partnerRegister,
  partnerTokenDebug,
  parseVehicleList,
  revokePartnerToken,
  type BusinessStatus,
  type ConsentGuide,
  type PartnerFleetStatus,
} from "../../lib/api";

type Tab = "m2m" | "consent" | "infra";

export default function SetupPage() {
  const [tab, setTab] = useState<Tab>("m2m");
  const [partner, setPartner] = useState<PartnerFleetStatus | null>(null);
  const [guide, setGuide] = useState<ConsentGuide | null>(null);
  const [bizStatus, setBizStatus] = useState<BusinessStatus | null>(null);
  const [authCode, setAuthCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err" | "info"; text: string } | null>(null);
  const [infraLog, setInfraLog] = useState("");
  const [testLog, setTestLog] = useState("");

  const refresh = useCallback(async () => {
    const [p, g, b] = await Promise.all([
      getPartnerFleetStatus(),
      getConsentGuide(),
      getBusinessStatus(),
    ]);
    setPartner(p);
    setGuide(g);
    setBizStatus(b);
  }, []);

  useEffect(() => {
    refresh().catch((e) =>
      setMessage({ type: "err", text: e instanceof Error ? e.message : String(e) }),
    );
  }, [refresh]);

  async function handleAcquireM2M() {
    setLoading(true);
    setMessage(null);
    setTestLog("");
    try {
      const d = await acquirePartnerToken(true);
      setTestLog(JSON.stringify(d, null, 2));
      if (d.success === false || d.error) {
        setMessage({
          type: "err",
          text: String(d.error ?? "Échec obtention token M2M — voir détails."),
        });
      } else {
        setMessage({
          type: "ok",
          text: `Token M2M actif (${String(d.access_token_preview ?? "OK")}). Utilisé automatiquement par le backend.`,
        });
      }
      await refresh();
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setLoading(false);
    }
  }

  async function handleTestVehicles() {
    setLoading(true);
    setMessage(null);
    setTestLog("");
    try {
      const data = await listFleetVehicles();
      const n = parseVehicleList(data).length;
      setTestLog(JSON.stringify(data, null, 2));
      setMessage({
        type: "ok",
        text: `Liste véhicules OK (${n} véhicule(s)) — token M2M sans consent business.`,
      });
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e);
      setTestLog(err);
      setMessage({ type: "err", text: err });
    } finally {
      setLoading(false);
    }
  }

  async function handleRevokeM2M() {
    setLoading(true);
    try {
      await revokePartnerToken();
      setMessage({ type: "info", text: "Cache token M2M vidé. Cliquez « Obtenir token M2M » pour en régénérer un." });
      await refresh();
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setLoading(false);
    }
  }

  async function handleExchange() {
    if (!authCode.trim()) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await exchangeBusinessCode(authCode.trim());
      setMessage({
        type: "ok",
        text: `Token business actif (${res.access_token_preview}) — optionnel si M2M suffit.`,
      });
      setAuthCode("");
      await refresh();
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setLoading(false);
    }
  }

  async function runInfra(action: "debug" | "register") {
    setLoading(true);
    setInfraLog("");
    try {
      if (action === "debug") {
        const d = await partnerTokenDebug(true);
        setInfraLog(JSON.stringify(d, null, 2));
      } else {
        const d = await partnerRegister();
        setInfraLog(JSON.stringify(d, null, 2));
        setMessage({ type: "ok", text: "Domaine enregistré (ou déjà connu)." });
      }
    } catch (e) {
      setInfraLog(e instanceof Error ? e.message : String(e));
      setMessage({ type: "err", text: "Échec étape infra - voir détails ci-dessous." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="page-header">
        <h1>Configuration</h1>
        <p>
          Flotte AXEL PROJECT : token <strong>M2M partenaire</strong> (recommandé). Le consent
          Tesla for Business est optionnel (apps tierces).
        </p>
      </header>

      <div className="tabs">
        <button
          type="button"
          className={`tab${tab === "m2m" ? " active" : ""}`}
          onClick={() => setTab("m2m")}
        >
          Token M2M
        </button>
        <button
          type="button"
          className={`tab${tab === "consent" ? " active" : ""}`}
          onClick={() => setTab("consent")}
        >
          Consent (optionnel)
        </button>
        <button
          type="button"
          className={`tab${tab === "infra" ? " active" : ""}`}
          onClick={() => setTab("infra")}
        >
          Infra partenaire
        </button>
      </div>

      {message && (
        <div
          className={`alert alert-${message.type === "ok" ? "success" : message.type === "err" ? "error" : "info"}`}
        >
          {message.text}
        </div>
      )}

      {partner && (
        <div className="card" style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
          <span>
            Token M2M :{" "}
            <span className={`badge ${partner.token_active ? "badge-ok" : "badge-warn"}`}>
              {partner.token_active ? "Actif" : "Absent"}
            </span>
          </span>
          <span>
            Credentials :{" "}
            {partner.client_id_set && partner.client_secret_set ? "OK (.env)" : "À configurer"}
          </span>
          <span style={{ fontSize: 12, color: "#5c5e62" }}>{partner.audience}</span>
          {bizStatus?.token_active && (
            <span style={{ fontSize: 12 }}>
              Business (consent) : <span className="badge badge-ok">Actif</span>
            </span>
          )}
        </div>
      )}

      {tab === "m2m" && partner && (
        <>
          <div className="alert alert-info">{partner.note}</div>
          <div className="card">
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Partner Token (client_credentials)</h2>
            <p style={{ color: "#5c5e62", fontSize: 14, lineHeight: 1.6 }}>
              Même principe que Postman : <code>grant_type=client_credentials</code> + client_id/secret.
              Le backend met le Bearer en cache et l&apos;injecte sur{" "}
              <code>/api/fleet/vehicles</code> et les commandes — pas de page « Autoriser » Tesla for
              Business si vous êtes propriétaire de l&apos;app et de la flotte.
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={loading}
                onClick={handleAcquireM2M}
              >
                {loading ? "…" : "Obtenir token M2M"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={loading}
                onClick={handleTestVehicles}
              >
                Tester liste véhicules
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={loading}
                onClick={handleRevokeM2M}
              >
                Vider le cache token
              </button>
            </div>
            {testLog && (
              <pre style={{ background: "#f4f4f4", padding: 12, overflow: "auto", fontSize: 12 }}>
                {testLog}
              </pre>
            )}
          </div>
          <p style={{ fontSize: 13, color: "#5c5e62" }}>
            Doc :{" "}
            <a
              href="https://developer.tesla.com/docs/fleet-api/authentication/partner-tokens"
              target="_blank"
              rel="noreferrer"
            >
              Partner Tokens
            </a>
            {" · "}
            Si 412 : enregistrez le domaine dans l&apos;onglet Infra.
          </p>
        </>
      )}

      {tab === "consent" && guide && (
        <>
          <div className="alert alert-info">
            Uniquement si une app <em>tiers</em> accède à votre flotte. Pour AXEL PROJECT + GestionLMDCVTC
            (même compte), préférez l&apos;onglet Token M2M.
          </div>
          <div className="card">
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Authorization code (consent)</h2>
            <input
              className="input"
              placeholder="Code depuis Consent Management"
              value={authCode}
              onChange={(e) => setAuthCode(e.target.value)}
              style={{ marginBottom: 12 }}
            />
            <button
              type="button"
              className="btn btn-primary"
              disabled={loading || !authCode.trim()}
              onClick={handleExchange}
            >
              {loading ? "Échange…" : "Échanger le code business"}
            </button>
          </div>
          <ol style={{ paddingLeft: 20, lineHeight: 1.8, fontSize: 14 }}>
            {guide.steps.map((s) => (
              <li key={s.step}>
                <strong>{s.title}</strong>
                {s.description ? ` - ${s.description}` : ""}
              </li>
            ))}
          </ol>
        </>
      )}

      {tab === "infra" && (
        <div className="card">
          <h2 style={{ marginTop: 0, fontSize: 18 }}>Domaine & token partenaire</h2>
          <p style={{ fontSize: 14, color: "#5c5e62" }}>
            À faire une fois sur le VPS (HTTPS + APP_DOMAIN dans .env).
          </p>
          <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
            <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => runInfra("debug")}>
              Tester token partenaire
            </button>
            <button type="button" className="btn btn-primary" disabled={loading} onClick={() => runInfra("register")}>
              Enregistrer le domaine Tesla
            </button>
          </div>
          {infraLog && (
            <pre style={{ background: "#f4f4f4", padding: 12, overflow: "auto", fontSize: 12 }}>{infraLog}</pre>
          )}
        </div>
      )}
    </>
  );
}
