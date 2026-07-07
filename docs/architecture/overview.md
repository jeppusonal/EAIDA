# EAIDA MVP — Architecture overview

## Purpose

This document describes the architecture of the **10–14 day MVP**, not the full EAIDA platform. It exists to answer one question honestly: what is the minimum set of moving parts that lets a user ask "why did sales drop in Sydney?" and get a real, data-grounded answer back.

## MVP data flow

```
Synthetic data generation (notebooks)
        ↓
CSV files (data/raw/)
        ↓
PostgreSQL (single database, flat schema — no medallion layers yet)
        ↓
Basic ML (trend / regression to quantify the Sydney drop)
        ↓
Streamlit app
   ├─ shows charts (matplotlib / plotly against Postgres)
   └─ natural language box → local LLM (Ollama) → explanation
```

## What's deliberately missing (and why)

| Full-platform component | MVP replacement | Why it's safe to defer |
|---|---|---|
| Airflow orchestration | Manual notebook / script execution | Only one data load; no recurring schedule needed yet |
| dbt transformations | Direct pandas cleaning in notebooks | Schema is small and stable; dbt's value shows up with more models and more contributors |
| Medallion (raw/staging/mart) warehouse layers | One flat schema | Fewer tables, no need for layered isolation yet — this is the first thing we add back once dbt comes in |
| Multi-agent system | Single LLM call with a fixed prompt template | One question type (sales drop) doesn't need agent handoff logic |
| Vector database / RAG | None | No unstructured documents in the MVP dataset yet |
| Hosted LLM API | Ollama (local model) | No cost, no data leaves the machine, sufficient for a fixed explanation task |

None of these are wrong choices being permanently rejected — they're the same architecture from the full platform diagram, intentionally staged. The MVP schema is designed so that adding dbt later means introducing staging/mart models *on top of* the existing raw tables, not restructuring them.

## MVP database schema (flat, single-layer)

- `customers` — one row per customer
- `stores` — one row per physical store (city, region)
- `products` — one row per SKU
- `orders` — one row per order, links to `customers` and `stores`
- `order_items` — one row per line item, links to `orders` and `products`
- `inventory` — periodic stock-level snapshots per store/product
- `returns` — one row per returned item, links to `orders` and `products`
- `marketing_campaigns` — campaign metadata, optionally city-targeted

This mirrors the fact table / dimension table shape we'll formalize into a proper star schema in the full build (`orders` + `order_items` are the fact tables; `customers`, `stores`, `products` are dimensions).

## Path back to the full architecture

Once this MVP proves the core loop works, the upgrade path is additive:
1. Introduce dbt on top of the existing Postgres tables (raw → staging → marts) — no schema redesign needed.
2. Introduce Airflow to schedule what's currently manual.
3. Split the single LLM call into role-based agents (data engineer agent, BI analyst agent, etc.) once more question types are supported.
4. Add a vector database once unstructured content (reviews, support tickets, PDFs) enters scope.

See `docs/adr/` for the specific decisions made along the way.
