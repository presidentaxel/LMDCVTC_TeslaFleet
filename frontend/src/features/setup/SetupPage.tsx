import { useCallback, useEffect, useState } from "react";
import {
  exchangeBusinessCode,
  getBusinessStatus,
  getConsentGuide,
  partnerRegister,
  partnerTokenDebug,
  type BusinessStatus,
  type ConsentGuide,
} from "../../lib/api";

type Tab = "consent" | "infra";

export default function SetupPage() {
  const [tab, setTab] = useState<Tab>("consent");
  const [guide, setGuide] = useState<ConsentGuide | null>(null);
  const [status, setStatus] = useState<BusinessStatus | null>(null);
  const [authCode, setAuthCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err" | "info"; text: string } | null>(null);
  const [infraLog, setInfraLog] = useState<string>("");

  const refresh = useCallback(async () => {
    const [g, s] = await Promise.all([getConsentGuide(), getBusinessStatus()]);
    setGuide(g);
    setStatus(s);
  }, []);

  useEffect(() => {
    refresh().catch((e) =>
      setMessage({ type: "err", text: e instanceof Error ? e.message : String(e) }),
    );
  }, [refresh]);

  async function handleExchange() {
    if (!authCode.trim()) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await exchangeBusinessCode(authCode.trim());
      setMessage({
        type: "ok",
        text: `Token business actif (${res.access_token_preview})`,
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
      setMessage({ type: "err", text: "Échec étape infra — voir détails ci-dessous." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="page-header">
        <h1>Configuration</h1>
        <p>Connectez la flotte business Tesla en quelques étapes.</p>
      </header>

      <div className="tabs">
        <button
          type="button"
          className={`tab${tab === "consent" ? " active" : ""}`}
          onClick={() => setTab("consent")}
        >
          Consentement business
        </button>
        <button
          type="button"
          className={`tab${tab === "infra" ? " active" : ""}`}
          onClick={() => setTab("infra")}
        >
          Infra partenaire
        </button>
      </div>

      {message && <div className={`alert alert-${message.type === "ok" ? "success" : message.type === "err" ? "error" : "info"}`}>{message.text}</div>}

      {status && (
        <div className="card" style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
          <span>
            Token business :{" "}
            <span className={`badge ${status.token_active ? "badge-ok" : "badge-warn"}`}>
              {status.token_active ? "Actif" : "Absent"}
            </span>
          </span>
          <span>
            Credentials :{" "}
            {status.client_id_set && status.client_secret_set ? "OK" : "À configurer dans .env"}
          </span>
        </div>
      )}

      {tab === "consent" && guide && (
        <>
          <div className="alert alert-info">{guide.note}</div>
          <div className="card">
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Étape unique : coller le code</h2>
            <p style={{ color: "#5c5e62", fontSize: 14 }}>
              Après approbation sur Tesla for Business, collez l&apos;authorization code ici.
            </p>
            <input
              className="input"
              placeholder="Authorization code depuis Consent Management"
              value={authCode}
              onChange={(e) => setAuthCode(e.target.value)}
              style={{ marginBottom: 12 }}
            />
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={loading || !authCode.trim()}
                onClick={handleExchange}
              >
                {loading ? "Échange…" : "Valider le consentement"}
              </button>
              <a
                className="btn btn-secondary"
                href={guide.steps[0]?.url ?? "https://www.tesla.com/teslaaccount/business"}
                target="_blank"
                rel="noreferrer"
              >
                Ouvrir Tesla for Business
              </a>
            </div>
          </div>
          <ol style={{ paddingLeft: 20, lineHeight: 1.8, fontSize: 14 }}>
            {guide.steps.map((s) => (
              <li key={s.step}>
                <strong>{s.title}</strong>
                {s.description ? ` — ${s.description}` : ""}
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
