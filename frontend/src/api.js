// api.js — tout ce qui parle à l'API FastAPI est rangé ici (un seul endroit à modifier si l'URL change).

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Appelle l'API avec le token JWT et renvoie le JSON (ou lève une erreur lisible).
export async function api(path, token, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

// OAuth2 attend un formulaire classique (pas du JSON) : URLSearchParams s'en charge.
export async function login(username, password) {
  const res = await fetch(`${API_URL}/auth/token`, {
    method: "POST",
    body: new URLSearchParams({ username, password }),
  });
  if (res.status === 401) throw new Error("Identifiant ou mot de passe incorrect.");
  if (!res.ok) throw new Error("L'API ne répond pas. Est-elle bien démarrée ?");
  return (await res.json()).access_token;
}

// Le milieu du JWT contient le nom et le rôle (encodé en base64url, PAS chiffré : rien de secret dedans).
export function decodeToken(token) {
  const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(part));
}

// ---------- Petits formateurs réutilisés partout ----------
const nf = new Intl.NumberFormat("fr-FR");
const compact = new Intl.NumberFormat("fr-FR", { notation: "compact", maximumFractionDigits: 1 });

export const formatNumber = (n) => (n == null ? "—" : nf.format(Math.round(n)));
export const formatBudget = (n) => (n == null ? "—" : `${compact.format(n)} TND`);
export const formatPercent = (x) => (x == null ? "—" : `${Math.round(x * 100)} %`);

export function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
}

// Nombre de jours avant la date limite (négatif = déjà clôturé).
export function daysLeft(iso) {
  if (!iso) return null;
  const ms = new Date(iso).setHours(23, 59, 59) - Date.now();
  return Math.ceil(ms / 86_400_000);
}

// Nom affiché de chaque secteur (la base stocke des noms courts en minuscules).
const SECTOR_LABELS = {
  informatique: "Informatique", telecom: "Télécoms", etudes: "Études & conseil",
  btp: "BTP", sante: "Santé", energie: "Énergie", autre: "Autre",
};
export const sectorLabel = (s) => SECTOR_LABELS[s] ?? s;

// Couleur d'un score : vert = à saisir, ambre = à étudier, gris = peu pertinent.
export function scoreLevel(score) {
  if (score == null) return "none";
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "mid";
  return "low";
}
