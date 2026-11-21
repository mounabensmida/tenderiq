// Chat.jsx — l'assistant : l'agent LangGraph choisit seul entre documents (RAG), chiffres (SQL) et e-mail.
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import Icon from "./Icon";

const ROUTES = {
  documents: { label: "Documents", icon: "doc" },
  chiffres: { label: "Chiffres", icon: "chart" },
  email: { label: "E-mail", icon: "mail" },
};

const SUGGESTIONS = [
  { route: "documents", text: "Quelle certification est exigée pour l'appel d'offres AO-2026-0001 ?" },
  { route: "chiffres", text: "Combien d'appels d'offres y a-t-il par secteur ?" },
  { route: "email", text: "Envoie un résumé de l'appel d'offres AO-2026-0001 à ali@exemple.tn" },
];

function RouteTag({ route }) {
  const r = ROUTES[route];
  if (!r) return null;
  return <span className={`route route-${route}`}><Icon name={r.icon} size={13} /> {r.label}</span>;
}

// Les lignes EXACTES renvoyées par la base : la réponse du LLM peut se vérifier d'un coup d'œil.
function ResultTable({ rows }) {
  const columns = Object.keys(rows[0]);
  return (
    <div className="result-wrap">
      <table className="result">
        <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.slice(0, 10).map((row, i) => (
            <tr key={i}>{columns.map((c) => <td key={c}>{String(row[c] ?? "—")}</td>)}</tr>
          ))}
        </tbody>
      </table>
      {rows.length > 10 && <p className="muted small">… et {rows.length - 10} autres lignes</p>}
    </div>
  );
}

function Message({ m }) {
  if (m.who === "user") return <div className="msg msg-user">{m.text}</div>;
  return (
    <div className={`msg msg-agent ${m.error ? "msg-error" : ""}`}>
      {m.route && <RouteTag route={m.route} />}
      <p>{m.text}</p>
      {m.sources?.length > 0 && (
        <div className="sources">
          {m.sources.map((s) => (
            <span key={s.n} className="source" title={s.extrait}>
              <b>[{s.n}]</b> {s.reference} · p.{s.page}
            </span>
          ))}
        </div>
      )}
      {m.rows?.length > 0 && <ResultTable rows={m.rows} />}
      {m.sql && (
        <details className="sql">
          <summary>Voir la requête SQL exécutée</summary>
          <pre>{m.sql}</pre>
        </details>
      )}
    </div>
  );
}

export default function Chat({ token, role }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(null);      // brouillon d'e-mail en attente de validation
  const [loading, setLoading] = useState(false);
  const bottom = useRef(null);

  const add = (msg) => setMessages((old) => [...old, msg]);

  // Fait défiler jusqu'au dernier message à chaque nouveau message.
  // ⚠ Les accolades sont indispensables : sans elles, la flèche RENVOIE le résultat de scrollIntoView
  // (une Promise dans les navigateurs récents), et React plante car un useEffect ne doit renvoyer
  // qu'une fonction de nettoyage, ou rien.
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, loading, pending]);

  async function ask(text) {
    const q = text.trim();
    if (q.length < 3 || loading) return;
    add({ who: "user", text: q });
    setQuestion("");
    setLoading(true);
    try {
      const r = await api("/ask", token, { method: "POST", body: JSON.stringify({ question: q }) });
      if (r.status === "pending_approval") {
        setPending(r);
        add({ who: "agent", route: "email", text: "J'ai rédigé l'e-mail ci-dessous. Il ne partira qu'après validation." });
      } else {
        add({ who: "agent", text: r.answer, route: r.route, sources: r.sources, sql: r.sql, rows: r.rows });
      }
    } catch (err) {
      add({ who: "agent", error: true, text: `Une erreur est survenue : ${err.message}` });
    }
    setLoading(false);
  }

  async function decide(decision) {
    try {
      const r = await api("/approve", token, {
        method: "POST", body: JSON.stringify({ thread_id: pending.thread_id, decision }),
      });
      add({ who: "agent", route: "email", text: `${r.answer} (décision de ${r.validated_by})` });
    } catch (err) {
      add({ who: "agent", error: true, text: err.message });
    }
    setPending(null);
  }

  // Entrée = envoyer ; Maj + Entrée = nouvelle ligne.
  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask(question);
    }
  }

  return (
    <section className="card chat">
      <header className="card-head chat-head">
        <div className="chat-title">
          <span className="bot-avatar"><Icon name="spark" /></span>
          <div>
            <h2>Assistant TenderIQ</h2>
            <p className="muted small">Agent LangGraph · réponses sourcées</p>
          </div>
        </div>
      </header>

      <div className="messages">
        {!messages.length && (
          <div className="chat-empty">
            <p className="muted">Posez une question en français, en anglais ou en arabe. Par exemple :</p>
            {SUGGESTIONS.map((s) => (
              <button key={s.text} className="suggestion" onClick={() => ask(s.text)}>
                <RouteTag route={s.route} />
                <span>{s.text}</span>
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => <Message key={i} m={m} />)}

        {loading && (
          <div className="msg msg-agent typing" aria-label="L'agent réfléchit">
            <span /><span /><span />
          </div>
        )}

        {pending && (
          <div className="approval">
            <p className="approval-title"><Icon name="shield" size={16} /> Validation humaine requise</p>
            <dl>
              <dt>À</dt><dd>{pending.draft.to}</dd>
              <dt>Objet</dt><dd>{pending.draft.subject}</dd>
            </dl>
            <pre>{pending.draft.body}</pre>
            {role === "admin" ? (
              <div className="approval-actions">
                <button className="btn btn-primary btn-sm" onClick={() => decide("approve")}>
                  <Icon name="check" size={16} /> Valider et envoyer
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => decide("reject")}>Refuser</button>
              </div>
            ) : (
              <p className="alert alert-warn"><Icon name="lock" size={15} /> Seul un administrateur peut valider cet envoi.</p>
            )}
          </div>
        )}
        <div ref={bottom} />
      </div>

      <form className="composer" onSubmit={(e) => { e.preventDefault(); ask(question); }}>
        <textarea rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={onKeyDown}
                  placeholder="Votre question…  (Entrée pour envoyer)" />
        <button className="btn btn-primary btn-icon" disabled={loading || question.trim().length < 3} aria-label="Envoyer">
          <Icon name="send" />
        </button>
      </form>
    </section>
  );
}
