// TenderTable.jsx — la liste des opportunités : recherche, filtres, et détail du score (SHAP) au clic.
import { Fragment, useMemo, useState } from "react";
import { daysLeft, formatBudget, formatDate, formatPercent, scoreLevel, sectorLabel } from "../api";
import Icon from "./Icon";

const SCORE_FILTERS = [
  { value: 0, label: "Tous" },
  { value: 0.4, label: "≥ 40 %" },
  { value: 0.7, label: "≥ 70 %" },
];

function ScoreBadge({ score }) {
  const level = scoreLevel(score);
  return (
    <div className={`score score-${level}`}>
      <span className="score-value">{formatPercent(score)}</span>
      <span className="score-track"><span style={{ width: `${(score ?? 0) * 100}%` }} /></span>
    </div>
  );
}

function Deadline({ date }) {
  const days = daysLeft(date);
  let status = { cls: "closed", text: "Clôturé" };
  if (days == null) status = { cls: "closed", text: "—" };
  else if (days >= 0 && days <= 7) status = { cls: "urgent", text: `J-${days}` };
  else if (days > 7) status = { cls: "open", text: `${days} j restants` };
  return (
    <div className="deadline">
      <span>{formatDate(date)}</span>
      <span className={`pill pill-${status.cls}`}>{status.text}</span>
    </div>
  );
}

// Le détail qui s'ouvre sous une ligne : les raisons SHAP en barres + la justification du LLM.
function Explanation({ tender }) {
  const reasons = tender.score_reasons ?? [];
  const maxImpact = Math.max(0.01, ...reasons.map((r) => Math.abs(r.impact)));
  return (
    <div className="explain">
      <div>
        <h4>Pourquoi ce score ?</h4>
        <p className="muted small">Contribution de chaque facteur au score (valeurs SHAP du modèle XGBoost).</p>
        <ul className="reasons">
          {reasons.map((r) => (
            <li key={r.feature}>
              <span className="reason-label">{r.label}</span>
              <span className="reason-bar">
                <span className={r.impact > 0 ? "up" : "down"}
                      style={{ width: `${(Math.abs(r.impact) / maxImpact) * 100}%` }} />
              </span>
              <span className={`reason-dir ${r.impact > 0 ? "up" : "down"}`}>
                {r.impact > 0 ? "▲" : "▼"} {r.direction}
              </span>
            </li>
          ))}
          {!reasons.length && <li className="muted">Score pas encore calculé.</li>}
        </ul>
      </div>
      <div className="ai-note">
        <h4><Icon name="spark" size={16} /> Analyse de l'IA</h4>
        <p>{tender.justification || "Pas encore de justification rédigée pour cet avis. Les barres ci-contre suffisent à expliquer le score."}</p>
        <dl className="meta">
          <dt>Pays</dt><dd>{tender.country || "—"}</dd>
          <dt>Budget</dt><dd>{formatBudget(tender.budget_tnd)}</dd>
          <dt>Référence</dt><dd>{tender.reference}</dd>
        </dl>
      </div>
    </div>
  );
}

export default function TenderTable({ tenders, loading, sector, onSectorChange }) {
  const [query, setQuery] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [openRef, setOpenRef] = useState(null);

  // useMemo : ne recalcule la liste filtrée que si les données ou les filtres changent.
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return tenders.filter((t) =>
      (!sector || t.sector === sector) &&
      (t.score ?? 0) >= minScore &&
      (!q || `${t.reference} ${t.title} ${t.country}`.toLowerCase().includes(q)));
  }, [tenders, query, minScore, sector]);

  return (
    <section className="card card-table">
      <header className="card-head">
        <div>
          <h2>Opportunités</h2>
          <p className="muted small">{visible.length} sur {tenders.length} affichées, triées par score.</p>
        </div>
        <div className="toolbar">
          <label className="search">
            <Icon name="search" size={16} />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Référence, objet, pays…" />
          </label>
          <div className="segmented" role="group" aria-label="Score minimum">
            {SCORE_FILTERS.map((f) => (
              <button key={f.value} className={minScore === f.value ? "is-active" : ""}
                      onClick={() => setMinScore(f.value)}>{f.label}</button>
            ))}
          </div>
          {sector && (
            <button className="chip chip-filter" onClick={() => onSectorChange("")}>
              {sectorLabel(sector)} <Icon name="close" size={14} />
            </button>
          )}
        </div>
      </header>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Score</th><th>Appel d'offres</th><th>Secteur</th><th>Budget</th><th>Date limite</th><th /></tr>
          </thead>
          <tbody>
            {loading && [...Array(6)].map((_, i) => (
              <tr key={i}><td colSpan={6}><span className="skeleton wide" /></td></tr>
            ))}
            {!loading && visible.map((t) => {
              const open = openRef === t.reference;
              return (
                <Fragment key={t.reference}>
                  <tr className={`row ${open ? "is-open" : ""}`} onClick={() => setOpenRef(open ? null : t.reference)}>
                    <td><ScoreBadge score={t.score} /></td>
                    <td>
                      <p className="title">{t.title}</p>
                      <p className="muted small">{t.reference} · {t.country}</p>
                    </td>
                    <td><span className={`chip chip-${t.sector}`}>{sectorLabel(t.sector)}</span></td>
                    <td className="num">{formatBudget(t.budget_tnd)}</td>
                    <td><Deadline date={t.deadline} /></td>
                    <td><Icon name="chevron" className={`chevron ${open ? "rot" : ""}`} /></td>
                  </tr>
                  {open && (
                    <tr className="detail-row"><td colSpan={6}><Explanation tender={t} /></td></tr>
                  )}
                </Fragment>
              );
            })}
            {!loading && !visible.length && (
              <tr><td colSpan={6} className="empty">Aucun appel d'offres ne correspond à ces filtres.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
