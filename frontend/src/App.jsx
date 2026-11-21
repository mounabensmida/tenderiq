// App.jsx — assemble les écrans : connexion, puis tableau de bord (indicateurs + opportunités + assistant).
import { useCallback, useEffect, useState } from "react";
import "./App.css";
import { api, decodeToken } from "./api";
import Chat from "./components/Chat";
import Icon from "./components/Icon";
import Login from "./components/Login";
import { KpiRow, SectorBreakdown } from "./components/Stats";
import TenderTable from "./components/TenderTable";

function Dashboard({ token, onLogout }) {
  const user = decodeToken(token);
  const [stats, setStats] = useState(null);
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sector, setSector] = useState("");

  // useEffect : "fais ceci quand le composant apparaît". Les 2 appels partent en parallèle.
  useEffect(() => {
    Promise.all([api("/stats", token), api("/tenders?limit=100", token)])
      .then(([s, t]) => { setStats(s); setTenders(t); })
      .catch((err) => {
        if (err.message.includes("Token")) onLogout();   // token expiré : retour à la connexion
        else setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [token, onLogout]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><Icon name="logo" size={20} /></span>
          <span>TenderIQ</span>
          <span className="brand-tag">Veille & analyse d'appels d'offres</span>
        </div>
        <div className="topbar-right">
          <span className={`status ${error ? "status-down" : "status-up"}`}>
            <i /> {error ? "API indisponible" : "Connecté"}
          </span>
          <div className="user-chip">
            <span className="avatar">{user.sub[0].toUpperCase()}</span>
            <div>
              <b>{user.sub}</b>
              <small>{user.role === "admin" ? "Administrateur" : "Analyste"}</small>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onLogout} title="Se déconnecter">
            <Icon name="logout" size={16} /> Déconnexion
          </button>
        </div>
      </header>

      <main className="content">
        <div className="page-title">
          <h1>Tableau de bord</h1>
          <p className="muted">Les appels d'offres publics notés par le modèle, et un assistant pour les interroger.</p>
        </div>

        {error && <p className="alert alert-error">Impossible de charger les données : {error}</p>}

        <KpiRow stats={stats} />

        <div className="grid">
          <div className="col-main">
            <SectorBreakdown stats={stats} active={sector} onSelect={setSector} />
            <TenderTable tenders={tenders} loading={loading} sector={sector} onSectorChange={setSector} />
          </div>
          <aside className="col-side">
            <Chat token={token} role={user.role} />
          </aside>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  // Le token est gardé dans sessionStorage : un rechargement de page ne déconnecte pas,
  // mais fermer l'onglet, si. (try/catch : le stockage peut être bloqué par le navigateur.)
  const [token, setToken] = useState(() => {
    try { return sessionStorage.getItem("tenderiq_token"); } catch { return null; }
  });

  // useCallback garde LA MÊME fonction d'un affichage à l'autre. Sans lui, le useEffect du Dashboard
  // (qui dépend de onLogout) verrait une "nouvelle" fonction à chaque fois et rechargerait en boucle.
  const save = useCallback((t) => {
    try {
      if (t) sessionStorage.setItem("tenderiq_token", t);
      else sessionStorage.removeItem("tenderiq_token");
    } catch { /* stockage bloqué : on reste connecté pour cette page seulement */ }
    setToken(t);
  }, []);
  const logout = useCallback(() => save(null), [save]);

  if (!token) return <Login onLogin={save} />;
  return <Dashboard token={token} onLogout={logout} />;
}
