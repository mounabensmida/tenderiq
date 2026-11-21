// Stats.jsx — les 4 indicateurs clés + la répartition par secteur (données de la route /stats).
import { formatBudget, formatNumber, formatPercent, sectorLabel } from "../api";
import Icon from "./Icon";

export function KpiRow({ stats }) {
  const cards = [
    { icon: "doc", label: "Appels d'offres analysés", value: formatNumber(stats?.total),
      sub: stats ? `${formatNumber(stats.open)} encore ouverts` : "" },
    { icon: "trophy", label: "Opportunités chaudes", value: formatNumber(stats?.hot),
      sub: "score ≥ 70 %", accent: true },
    { icon: "gauge", label: "Score moyen", value: formatPercent(stats?.avg_score),
      sub: stats ? `${formatNumber(stats.scored)} avis notés` : "" },
    { icon: "wallet", label: "Budget des opportunités chaudes", value: formatBudget(stats?.hot_budget),
      sub: "montant cumulé estimé" },
  ];
  return (
    <section className="kpi-row">
      {cards.map((c) => (
        <article key={c.label} className={`kpi ${c.accent ? "kpi-accent" : ""}`}>
          <span className="kpi-icon"><Icon name={c.icon} /></span>
          <div>
            <p className="kpi-label">{c.label}</p>
            <p className="kpi-value">{stats ? c.value : <span className="skeleton" />}</p>
            <p className="kpi-sub">{c.sub}</p>
          </div>
        </article>
      ))}
    </section>
  );
}

export function SectorBreakdown({ stats, active, onSelect }) {
  const sectors = stats?.sectors ?? [];
  const max = Math.max(1, ...sectors.map((s) => s.count));
  return (
    <section className="card">
      <header className="card-head">
        <div>
          <h2>Répartition par secteur</h2>
          <p className="muted small">Cliquez sur un secteur pour filtrer la liste.</p>
        </div>
        {active && <button className="btn btn-ghost btn-sm" onClick={() => onSelect("")}>Tout afficher</button>}
      </header>
      <ul className="sector-bars">
        {sectors.map((s) => (
          <li key={s.sector}>
            <button className={`sector-bar ${active === s.sector ? "is-active" : ""}`}
                    onClick={() => onSelect(active === s.sector ? "" : s.sector)}>
              <span className="sector-name">{sectorLabel(s.sector)}</span>
              <span className="bar-track"><span className="bar-fill" style={{ width: `${(s.count / max) * 100}%` }} /></span>
              <span className="sector-count">{s.count}</span>
              <span className="sector-score muted">{formatPercent(s.avg_score)}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
