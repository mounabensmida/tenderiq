// App.jsx — toute l'interface de TenderIQ en un seul fichier (3 composants + l'App)
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://localhost:8000";

// Petite fonction utilitaire : appelle l'API avec le token et renvoie le JSON (ou lève une erreur).
async function api(path, token, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`${res.status} : ${await res.text()}`);
  return res.json();
}

// ---------- Composant 1 : la connexion ----------
function Login({ onLogin }) {
  const [username, setUsername] = useState("analyste");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();                          // empêche le rechargement de la page
    // OAuth2 attend un formulaire classique (pas du JSON) : URLSearchParams s'en charge.
    const res = await fetch(`${API}/auth/token`, { method: "POST", body: new URLSearchParams({ username, password }) });
    if (!res.ok) return setError("Identifiants incorrects");
    const data = await res.json();
    onLogin(data.access_token);                      // on remonte le token au composant parent
  }

  return (
    <form className="card login" onSubmit={submit}>
      <h2>Connexion à TenderIQ</h2>
      <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Utilisateur" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe" />
      <button>Se connecter</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

// ---------- Composant 2 : le tableau des opportunités ----------
function Tenders({ token }) {
  const [tenders, setTenders] = useState([]);

  // useEffect : "fais ceci quand le composant apparaît" (et à chaque changement de token).
  useEffect(() => {
    api("/tenders?limit=15", token).then(setTenders).catch(console.error);
  }, [token]);

  return (
    <section className="card">
      <h2>Meilleures opportunités</h2>
      <table>
        <thead>
          <tr><th>Référence</th><th>Objet</th><th>Secteur</th><th>Score</th><th>Pourquoi ?</th></tr>
        </thead>
        <tbody>
          {tenders.map((t) => (
            <tr key={t.reference}>
              <td>{t.reference}</td>
              <td>{t.title}</td>
              <td>{t.sector}</td>
              <td className="score">{t.score != null ? `${Math.round(t.score * 100)} %` : "—"}</td>
              <td>{t.justification || (t.score_reasons || []).map((r) => `${r.label} (${r.direction})`).join(" · ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

// ---------- Composant 3 : le chat avec l'agent ----------
function Chat({ token, role }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(null);      // brouillon d'e-mail en attente de validation
  const [loading, setLoading] = useState(false);

  const add = (msg) => setMessages((old) => [...old, msg]);   // ajoute un message à la liste

  async function ask(event) {
    event.preventDefault();
    if (!question.trim()) return;
    add({ who: "moi", text: question });
    setLoading(true);
    try {
      const r = await api("/ask", token, { method: "POST", body: JSON.stringify({ question }) });
      if (r.status === "pending_approval") {
        setPending(r);
        add({ who: "agent", text: "J'ai préparé un e-mail. Il faut une validation avant l'envoi." });
      } else {
        add({ who: "agent", text: r.answer, route: r.route, sources: r.sources, sql: r.sql });
      }
    } catch (err) {
      add({ who: "agent", text: `Erreur ${err.message}` });
    }
    setQuestion("");
    setLoading(false);
  }

  async function decide(decision) {
    try {
      const r = await api("/approve", token, { method: "POST", body: JSON.stringify({ thread_id: pending.thread_id, decision }) });
      add({ who: "agent", text: r.answer });
    } catch (err) {
      add({ who: "agent", text: `Erreur ${err.message}` });
    }
    setPending(null);
  }

  return (
    <section className="card">
      <h2>Poser une question</h2>
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.who}`}>
            {m.route && <span className="badge">{m.route}</span>}
            <p>{m.text}</p>
            {m.sources?.length > 0 && (
              <small>Sources : {m.sources.map((s) => `[${s.n}] ${s.reference} p.${s.page}`).join(" · ")}</small>
            )}
            {m.sql && <pre>{m.sql}</pre>}
          </div>
        ))}
        {loading && <p className="msg agent">L'agent réfléchit…</p>}
      </div>

      {pending && (
        <div className="approval">
          <b>À : {pending.draft.to}</b> — {pending.draft.subject}
          <pre>{pending.draft.body}</pre>
          {role === "admin" ? (
            <>
              <button onClick={() => decide("approve")}>Valider et envoyer</button>
              <button className="secondary" onClick={() => decide("reject")}>Refuser</button>
            </>
          ) : (
            <p className="error">Seul un administrateur peut valider cet envoi.</p>
          )}
        </div>
      )}

      <form onSubmit={ask} className="ask">
        <input value={question} onChange={(e) => setQuestion(e.target.value)}
               placeholder="Ex. : Quelle caution pour AO-2026-0002 ?  /  Combien d'offres en BTP ?" />
        <button disabled={loading}>Envoyer</button>
      </form>
    </section>
  );
}

// ---------- L'application ----------
export default function App() {
  const [token, setToken] = useState(null);
  if (!token) return <Login onLogin={setToken} />;

  // Le milieu du JWT contient le rôle (encodé en base64url, pas chiffré : il ne faut rien y mettre de secret).
  const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));

  return (
    <main>
      <header>
        <h1>TenderIQ</h1>
        <span>{payload.sub} ({payload.role})</span>
        <button className="secondary" onClick={() => setToken(null)}>Déconnexion</button>
      </header>
      <Tenders token={token} />
      <Chat token={token} role={payload.role} />
    </main>
  );
}