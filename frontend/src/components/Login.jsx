// Login.jsx — écran de connexion en deux panneaux : la promesse du produit à gauche, le formulaire à droite.
import { useState } from "react";
import { login } from "../api";
import Icon from "./Icon";

// Comptes de démonstration définis dans backend/app/core/security.py
const DEMO_ACCOUNTS = [
  { username: "analyste", password: "analyste123", label: "Analyste", hint: "Consulter et questionner" },
  { username: "admin", password: "admin123", label: "Administrateur", hint: "Valide aussi les e-mails" },
];

const FEATURES = [
  { icon: "gauge", title: "Score explicable", text: "Chaque opportunité est notée par XGBoost, avec ses raisons (SHAP)." },
  { icon: "doc", title: "Questions sur les documents", text: "Réponses issues des cahiers des charges, page citée." },
  { icon: "chart", title: "Questions chiffrées", text: "Le langage naturel est traduit en SQL sécurisé, en lecture seule." },
  { icon: "shield", title: "Humain dans la boucle", text: "Aucun e-mail ne part sans validation d'un administrateur." },
];

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("analyste");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();                       // empêche le rechargement de la page
    setLoading(true);
    setError("");
    try {
      onLogin(await login(username, password));   // on remonte le token au composant parent
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }

  return (
    <div className="login-page">
      <aside className="login-hero">
        <div className="brand brand-light">
          <span className="brand-mark"><Icon name="logo" size={22} /></span>
          <span>TenderIQ</span>
        </div>
        <h1>Repérez les appels d'offres qui valent votre temps.</h1>
        <p className="hero-sub">
          Un copilote multi-agents qui détecte, note et explique les appels d'offres publics en Tunisie et en Afrique.
        </p>
        <ul className="feature-list">
          {FEATURES.map((f) => (
            <li key={f.title}>
              <span className="feature-icon"><Icon name={f.icon} /></span>
              <div><b>{f.title}</b><span>{f.text}</span></div>
            </li>
          ))}
        </ul>
        <p className="hero-foot">FastAPI · LangGraph · Qdrant · XGBoost · PostgreSQL</p>
      </aside>

      <main className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <h2>Connexion</h2>
          <p className="muted">Accédez à votre espace de veille.</p>

          <label>
            Identifiant
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </label>
          <label>
            Mot de passe
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                   autoComplete="current-password" placeholder="••••••••" />
          </label>

          {error && <p className="alert alert-error">{error}</p>}
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Connexion…" : "Se connecter"}
          </button>

          <div className="demo-accounts">
            <span className="muted small">Comptes de démonstration</span>
            {DEMO_ACCOUNTS.map((a) => (
              <button type="button" key={a.username} className="demo-account"
                      onClick={() => { setUsername(a.username); setPassword(a.password); }}>
                <span className="avatar small">{a.label[0]}</span>
                <span><b>{a.label}</b><small>{a.hint}</small></span>
              </button>
            ))}
          </div>
        </form>
      </main>
    </div>
  );
}
