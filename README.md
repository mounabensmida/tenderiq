# TenderIQ — copilote multi-agents de veille et d'analyse d'appels d'offres

> Plateforme qui **détecte** les appels d'offres publics (Tunisie & Afrique), les **qualifie** avec un score explicable,
> permet de les **interroger en langage naturel** (documents *et* chiffres) et **se surveille elle-même** (qualité, dérive, coût).

![status](https://img.shields.io/badge/status-MVP%20en%20cours-orange)
![python](https://img.shields.io/badge/python-3.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Ce qui rend le projet différent

| Fonction | Comment |
|---|---|
| **Score explicable** | XGBoost + valeurs SHAP + justification rédigée par le LLM — pas de boîte noire |
| **Deux modes de question** | Documents → RAG avec citation de la page · Chiffres → Text-to-SQL en lecture seule. Un agent choisit automatiquement |
| **Garde-fou qualité en CI** | Si le score RAG ou la précision Text-to-SQL passe sous un seuil, GitHub Actions **bloque** le déploiement |
| **Détection de dérive** | Evidently compare les nouveaux appels d'offres à ceux d'entraînement → réentraînement déclenché |
| **Sécurité** | Validation humaine avant tout e-mail, utilisateur SQL read-only, tests d'injection de prompt, JWT/RBAC |
| **Multilingue** | FR / EN (AR en option) |

---

## 🏗️ Architecture

```
 Sources publiques (TUNEPS, sites ministères, AfDB…)
        │
        ▼
 ┌───────────────┐   Scrapy (pages statiques) / Playwright (pages JavaScript)
 │   SCRAPER     │
 └──────┬────────┘
        ▼
 ┌───────────────┐   pandas : nettoyage · embeddings : dédoublonnage (similarité cosinus)
 │   PIPELINE    │   LLM → JSON validé par Pydantic (titre, acheteur, budget, deadline, secteur…)
 └──────┬────────┘
        ▼
 ┌──────────────────────────┐      ┌──────────────────────────┐
 │ PostgreSQL (étoile)      │      │ Qdrant                   │
 │ fact_tender + dim_*      │      │ chunks des TDR (PDF)     │
 └──────┬───────────────────┘      └──────────┬───────────────┘
        ▼                                     │
 ┌───────────────┐   XGBoost + SHAP           │
 │   SCORING     │   suivi dans MLflow        │
 │               │   dérive : Evidently       │
 └──────┬────────┘                            │
        ▼                                     ▼
 ┌─────────────────────────────────────────────────────┐
 │  AGENT LangGraph  (routeur)                         │
 │   ├─ outil RAG          → Qdrant (hybride)          │
 │   ├─ outil Text-to-SQL  → Postgres (read-only)      │
 │   └─ outil e-mail       → ⏸ validation humaine      │
 │  outils exposés aussi via un serveur MCP            │
 └──────┬──────────────────────────────────────────────┘
        ▼
 ┌───────────────┐        ┌───────────────┐
 │ API FastAPI   │ ─────▶ │ Front React   │      + Dashboard Superset sur Postgres
 │ JWT / RBAC    │        └───────────────┘
 └──────┬────────┘
        ▼
 Docker Compose → GitHub Actions (tests + évals + Trivy) → kind (Kubernetes) / cloud via Terraform
 Observabilité : Prometheus + Grafana (API) · Langfuse (traces LLM, coût) · OpenTelemetry
```

---

## 📁 Arborescence

```
tenderiq/
├── backend/
│   ├── scraper/        # Spiders Scrapy + scripts Playwright
│   ├── pipeline/       # nettoyage, dédoublonnage, extraction LLM → Pydantic
│   ├── ml/             # entraînement XGBoost, SHAP, MLflow, détection de dérive
│   ├── rag/            # découpage des PDF, embeddings, indexation et recherche Qdrant
│   ├── agent/          # graphe LangGraph : routeur + outils (RAG, SQL, e-mail)
│   ├── mcp_server/     # serveur MCP qui expose les mêmes outils
│   ├── app/
│   │   ├── api/        # routes FastAPI (/tenders, /ask, /auth…)
│   │   ├── core/       # config (.env), sécurité JWT, logs
│   │   ├── models/     # schémas Pydantic
│   │   └── db/         # connexion SQLAlchemy
│   ├── tests/          # pytest
│   └── requirements.txt
├── evals/
│   ├── rag/            # questions + réponses attendues pour noter le RAG
│   ├── sql/            # questions + SQL attendu pour noter le Text-to-SQL
│   └── security/       # prompts d'injection qui doivent échouer
├── db/
│   ├── migrations/     # schéma en étoile (DDL)
│   └── seeds/          # données de démo
├── data/               # raw/ (scrapé), processed/ (nettoyé), samples/ (versionné)
├── notebooks/          # exploration
├── frontend/           # React (Vite)
├── infra/
│   ├── docker/         # Dockerfiles
│   ├── k8s/            # manifests kind
│   ├── terraform/      # IaC cloud
│   └── monitoring/     # config Prometheus + dashboards Grafana
├── .github/workflows/  # CI : lint, tests, évals LLM, scan Trivy, build images
├── docs/               # schémas, captures, notes d'apprentissage
├── .env.example
└── README.md
```

### Schéma en étoile (PostgreSQL)

```
            dim_buyer ─┐
          dim_sector ──┼── fact_tender ──┬── dim_date
         dim_country ──┘   (budget,      └── dim_source
                            score, …)
```

---

## 🧰 Technologies

| Domaine | Technologies | Ce que tu apprends |
|---|---|---|
| Data | Scrapy, Playwright, pandas, PostgreSQL, Superset | Collecter, nettoyer, modéliser en étoile, visualiser |
| IA | Ollama, embeddings, extraction JSON, XGBoost, SHAP, MLflow | LLM structuré, ML tabulaire, explicabilité, suivi d'expériences |
| RAG & agents | Qdrant, recherche hybride, LangGraph, Text-to-SQL, MCP | Récupération augmentée, orchestration d'agents, protocole d'outils |
| Génie logiciel | FastAPI, React, pytest, JWT/RBAC | API propre, auth, tests |
| DevOps | Docker Compose, GitHub Actions, Terraform, kind | Conteneurs, CI/CD, IaC, Kubernetes |
| Observabilité & sécu | Prometheus, Grafana, Langfuse, OpenTelemetry, Trivy | Métriques, traces LLM, scan de vulnérabilités |

---

## 🗓️ Plan sur 2 jours (une brique simple par techno)

**Jour 1 — la donnée et l'IA**

| Créneau | Brique | Résultat attendu |
|---|---|---|
| 1 | Docker Compose : Postgres, Qdrant, Ollama, MLflow | `docker compose up` démarre tout |
| 2 | Scraper (1 seule source) → `data/raw` | ~50 appels d'offres en JSON |
| 3 | Pipeline : nettoyage pandas + extraction LLM → Pydantic | JSON validé en base (schéma en étoile) |
| 4 | Scoring XGBoost + SHAP, loggé dans MLflow | Un score + 3 raisons par appel d'offres |
| 5 | RAG : PDF → chunks → Qdrant | Réponse avec citation de la page |

**Jour 2 — l'agent, le produit et l'ops**

| Créneau | Brique | Résultat attendu |
|---|---|---|
| 6 | Text-to-SQL read-only + agent LangGraph (routeur) | La bonne question va au bon outil |
| 7 | API FastAPI + JWT, outil e-mail avec validation humaine | `/ask`, `/tenders`, `/approve` |
| 8 | Front React minimal (liste + chat) | Démo utilisable |
| 9 | Évals + tests d'injection + CI GitHub Actions (seuil bloquant) + Trivy | Pipeline rouge si la qualité baisse |
| 10 | Prometheus/Grafana + Langfuse | Un dashboard de latence et de coût |

**Bonus si le temps le permet :** serveur MCP, détection de dérive (Evidently), Superset, kind/Terraform, arabe.

---

## 🚀 Démarrage

### Prérequis
Python 3.12 · Node 20 · Docker Desktop · Git · (optionnel) Ollama

### Installation

```bash
git clone https://github.com/<ton-user>/tenderiq.git
cd tenderiq
cp .env.example .env            # puis remplir les valeurs
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
pip install -r backend/requirements.txt
playwright install chromium
```

### Lancer (une fois le code écrit)

```bash
docker compose up -d                       # Postgres, Qdrant, MLflow, Grafana…
uvicorn backend.app.main:app --reload      # API → http://localhost:8000/docs
cd frontend && npm install && npm run dev  # Front → http://localhost:5173
```

| Service | URL |
|---|---|
| API (Swagger) | http://localhost:8000/docs |
| Front | http://localhost:5173 |
| Qdrant | http://localhost:6333/dashboard |
| MLflow | http://localhost:5000 |
| Grafana | http://localhost:3001 |
| Langfuse | http://localhost:3000 |

---

## 🔒 Sécurité

- Le Text-to-SQL utilise un **utilisateur PostgreSQL en lecture seule** et seules les requêtes `SELECT` sont acceptées.
- Toute action externe (e-mail) passe par une **étape de validation humaine** dans le graphe LangGraph.
- `evals/security/` contient des **prompts d'injection** joués en CI.
- Les images Docker sont scannées par **Trivy** avant le déploiement.
- Les secrets restent dans `.env`, qui n'est jamais commité.

---

## 📈 Qualité (LLMOps)

| Métrique | Seuil | Bloquant en CI |
|---|---|---|
| Score RAG (fidélité + pertinence) | ≥ 0.70 | ✅ |
| Précision Text-to-SQL (résultat identique) | ≥ 0.80 | ✅ |
| Tests d'injection réussis | 100 % | ✅ |

---

## 🎯 Lien avec les candidatures

- **MC13** : data, ML explicable, MLOps (MLflow, dérive, CI).
- **MC06** : LLM, RAG, agents, MCP, LLMOps.
- Réutilise mon projet MLOps existant pour la détection de dérive.

## 📄 Licence
MIT
