# EAIDA — Enterprise AI Intelligent Data Assistant (MVP)

> Ask a business question in natural language. Get SQL, data, a chart, and an explanation back.

This is the fast-MVP track of EAIDA: a scoped-down, 10–14 day build that proves the core loop before we invest in the full data platform (Airflow, dbt, multi-agent orchestration, Azure). Everything here is designed to be replaced or extended, not thrown away — the data model and folder layout match the long-term architecture, we're just deferring the heavy infrastructure.

## The one question this MVP answers

**"Why did sales drop in Sydney?"**

The synthetic dataset is generated with a deliberate, realistic revenue dip in the Sydney store in the most recent period. The point of the MVP is to be able to ask that question in plain English and get a grounded, data-backed answer — not to boil the ocean on every possible business question.

## MVP scope

**In scope:**
- Python, PostgreSQL, Streamlit
- Synthetic retail dataset (customers, stores, products, orders, order items, inventory, returns, marketing campaigns)
- Basic ML (a simple regression/trend model to quantify the drop)
- A local LLM via Ollama for natural-language explanation (added once the data layer is solid)

**Explicitly out of scope for MVP** (deferred to the full build):
- Airflow orchestration
- dbt transformations
- Multi-agent system
- Azure deployment
- Vector database / RAG

## Status

- **Day 1–2**: dataset design and generation (this README, architecture overview, and notebooks under `notebooks/`).
- **Day 3**: raw data loaded into PostgreSQL (`src/loading/load_raw_data.py`), six analytical views defined (`sql/02_analytical_views.sql`), and the Sydney revenue drop proven with plain SQL — no ML yet (`sql/03_sydney_drop_analysis.sql`). The drop is real: Sydney revenue fell ~41% month-over-month in May 2026 versus a trailing-3-month expectation, and the decline is broad-based across product categories rather than concentrated in one — see `docs/data/day3_findings.md`.

### Running Day 3 locally (macOS)

```bash
# 1. Postgres running locally (either works)
brew install postgresql@16 && brew services start postgresql@16
# or: docker run --name eaida-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16

createdb eaida

# 2. Python env
pip install -r requirements.txt
cp .env.example .env   # adjust credentials if yours differ

# 3. Load the data (creates schema + loads all 8 tables)
python -m src.loading.load_raw_data

# 4. Create the analytical views
psql eaida -f sql/02_analytical_views.sql

# 5. Run the drop analysis
psql eaida -f sql/03_sydney_drop_analysis.sql
```

## Project structure

```
eaida/
├── README.md
├── docs/
│   ├── architecture/overview.md      # MVP architecture (this stage)
│   ├── data/dataset_generation_plan.md
│   └── adr/                          # architecture decision records
├── notebooks/                        # exploratory, educational data generation
│   ├── 01_generate_customers.ipynb
│   ├── 02_generate_products.ipynb
│   ├── 03_generate_stores.ipynb
│   ├── 04_generate_orders.ipynb
│   ├── 05_generate_inventory.ipynb
│   ├── 06_generate_returns.ipynb
│   ├── 07_generate_marketing_campaigns.ipynb
│   └── 08_data_validation.ipynb
├── data/raw/                         # generated CSVs land here
└── src/                              # reusable modules (populated after MVP notebooks are validated)
```

## Why notebooks first

For the MVP data-generation stage, notebooks are the right tool: they make each generation decision visible and inspectable (sample rows, distributions, validation) while we're still shaping the dataset. Once the schema and generation logic are validated, the reusable logic moves into `src/` as proper modules — notebooks stay as documentation and exploration, not production code.

## Getting started

```bash
cd eaida
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # added once dependencies are finalized
jupyter lab notebooks/
```

## Roadmap after the MVP

Once the natural-language → SQL → chart → explanation loop works end to end on this synthetic dataset, later milestones re-introduce the full architecture: dbt for transformation, Airflow for orchestration, a vector database for document/RAG search, and a proper multi-agent system. See `docs/architecture/overview.md` for how this MVP maps onto that longer-term design.
