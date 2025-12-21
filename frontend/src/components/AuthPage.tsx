import { useEffect, useState } from "react";
import "./AuthPage.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

interface AuthStatus {
  isAuthenticated: boolean;
  tokenPreview?: string;
}

export default function AuthPage() {
  const [status, setStatus] = useState<AuthStatus>({ isAuthenticated: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  async function checkAuthStatus() {
    try {
      const res = await fetch(`${API_BASE}/auth/debug`);
      if (!res.ok) throw new Error("Failed to check auth status");
      const data = await res.json();
      setStatus({
        isAuthenticated: data.user_token_active ?? false,
        tokenPreview: data.user_token_preview ?? undefined,
      });
    } catch (err) {
      console.error("Auth check failed:", err);
    }
  }

  async function handleLogin() {
    setLoading(true);
    setError(null);
    try {
      // Récupérer l'URL d'autorisation
      const res = await fetch(`${API_BASE}/auth/authorize-url`);
      if (!res.ok) throw new Error("Failed to get authorize URL");
      const data = await res.json();
      
      // Rediriger vers Tesla OAuth
      window.location.href = data.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la connexion");
      setLoading(false);
    }
  }

  // Vérifier si on revient du callback OAuth
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get("success");
    const error = urlParams.get("error");
    
    if (error) {
      setError(`Erreur OAuth: ${decodeURIComponent(error)}`);
      // Nettoyer l'URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (success) {
      // Succès, vérifier le statut après un court délai
      setTimeout(() => {
        checkAuthStatus();
        window.history.replaceState({}, document.title, window.location.pathname);
      }, 1000);
    }
  }, []);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>🔐 Connexion Tesla</h1>
          <p className="auth-subtitle">
            Connectez-vous avec votre compte Tesla pour accéder à votre véhicule
          </p>
        </div>

        {error && (
          <div className="auth-error">
            <strong>Erreur :</strong> {error}
          </div>
        )}

        {status.isAuthenticated ? (
          <div className="auth-success">
            <div className="success-icon">✅</div>
            <h2>Connexion réussie !</h2>
            <p>Votre compte Tesla est maintenant connecté.</p>
            <p className="token-preview">
              Token actif : <code>{status.tokenPreview}</code>
            </p>
            <button onClick={checkAuthStatus} className="btn btn-secondary">
              Actualiser le statut
            </button>
          </div>
        ) : (
          <div className="auth-login">
            <div className="login-instructions">
              <h3>Instructions :</h3>
              <ol>
                <li>Cliquez sur le bouton "Se connecter avec Tesla" ci-dessous</li>
                <li>Vous serez redirigé vers la page de connexion Tesla</li>
                <li>Connectez-vous avec votre compte Tesla</li>
                <li>Accordez les permissions demandées</li>
                <li>Vous serez automatiquement redirigé vers cette page</li>
              </ol>
            </div>
            <button
              onClick={handleLogin}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? "Redirection..." : "Se connecter avec Tesla"}
            </button>
          </div>
        )}

        <div className="auth-info">
          <details>
            <summary>ℹ️ Informations de sécurité</summary>
            <ul>
              <li>Vos identifiants Tesla ne sont jamais stockés sur ce serveur</li>
              <li>Seul un token d'accès temporaire est utilisé</li>
              <li>Le flux OAuth utilise PKCE pour une sécurité renforcée</li>
              <li>Vous pouvez révoquer l'accès à tout moment depuis votre compte Tesla</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
  );
}

