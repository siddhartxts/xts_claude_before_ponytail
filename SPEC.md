# SPEC.md — Damodaran Reference Data Backend

## 1. What this project is

A small FastAPI + PostgreSQL backend for storing **Damodaran-style industry reference data** — the public, industry-level numbers from Aswath Damodaran's data pages (betas, tax rates, margins, risk premiums, PE ratios, and so on).

This is a **learning project**. The goal right now is to understand models, schemas, routers, and migrations by doing one small thing well — not to build a production valuation system.

What this is **not** (yet): we are not valuing companies, importing every spreadsheet, or building a frontend. Those come later.

---

## 2. The one job for now

> Take **one** Damodaran dataset, store it cleanly in the database, and read it back through the API.

Start with: **Levered and Unlevered Betas by Industry (US)**.

Once that works end to end, every other Damodaran dataset (tax rates, margins, implied ERP, PE ratios…) drops into the *same two tables* — you just add another dataset row and its metric rows. That is the whole point of the design below.

---

## 3. How the data actually gets into the database (read this first)

This is the part that feels confusing, so let's be clear about it.

Damodaran's data is **reference data that ships as Excel files** — one file per region, updated once a year in early January. Nobody types hundreds of beta rows into a POST endpoint by hand. So there are two different "write" paths, and they do different jobs:

- **POST endpoints** — build them, but mainly for *learning CRUD* and for the occasional manual fix (create a dataset record, correct one wrong row). They are **not** how the bulk data gets loaded.
- **A tiny seed script** — this is how the real data gets in. A short script (e.g. `scripts/seed_betas.py`) reads **one known Excel/CSV file**, maps its columns onto metric rows, and inserts them. It can insert directly via SQLAlchemy, or call your own POST endpoint — either is fine.

**Important distinction:** a small one-file seed script is **not** the same as the "full Excel importer" we're deferring. The deferred thing is a *general* importer that handles any file, validates everything, and runs on a schedule. We are not building that. We are building a ~30–50 line script for one specific file, just so we have real data to read.

So the priority order is:

1. **GET endpoints are the real point** — the whole reason to store this is to *read* it later (for valuations / an agent / a frontend).
2. **POST endpoints** — for learning and manual edits.
3. **The seed script** — loads the betas file once.

If you want the first version to be truly minimal, you can even skip the script at first and insert 3–4 beta rows by hand (in Adminer or via a couple of POST calls) just to prove the schema works — then write the script next.

---

## 4. Tables

Two tables hold everything for now.

### `datasets`

One row = one Damodaran dataset (one file, one region, one year).

| Column | Type | Notes |
|---|---|---|
| id | PK | |
| name | text, required | e.g. "Levered and Unlevered Betas by Industry" |
| category | text | groups datasets, e.g. `discount_rate`, `cash_flows`, `multiples` |
| region | text | `US`, `Europe`, `Japan`, `Emerging`, `Global` |
| source_url | text | link to the Damodaran page/file |
| data_year | int | e.g. 2026 (Damodaran updates once a year, in early January) |
| created_at | timestamp | |
| updated_at | timestamp | |

*Optional later:* a unique constraint on `(name, region, data_year)` so re-running the seed script doesn't create duplicate datasets.

### `dataset_metrics`

One row = one number, for one industry, for one metric. (Damodaran's wide spreadsheet gets "unfolded" into one row per value.)

| Column | Type | Notes |
|---|---|---|
| id | PK | |
| dataset_id | FK → datasets.id, required | |
| industry_name | text, **nullable** | e.g. "Software (System & Application)". Nullable because some datasets are market-wide, not by industry (e.g. implied ERP). |
| metric_name | text, required | e.g. `unlevered_beta`, `beta`, `d_e_ratio`, `effective_tax_rate` |
| metric_value | numeric, **nullable** | the number. Nullable because Damodaran sometimes shows `NA`. |
| unit | text | `ratio`, `percent`, `usd_millions`, `count` |
| period | text | usually the year; useful for time-series datasets |
| notes | text | optional |
| created_at | timestamp | |

*Optional later:* a unique constraint on `(dataset_id, industry_name, metric_name, period)` so re-importing updates instead of duplicating.

**Why this "one row per value" shape?** Different Damodaran datasets have completely different columns. Instead of building a new table for each one, this flexible shape lets all of them live in the same two tables. It's a normal, beginner-friendly choice for heterogeneous reference data. The trade-off is that it's less type-safe and you sometimes have to "pivot" rows back into columns when reading — fine at this stage.

---

## 5. Example — the betas dataset

**Dataset row:**

- name: `Levered and Unlevered Betas by Industry`
- category: `discount_rate`
- region: `US`
- source_url: `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html` (the exact `.xls` file link is on that page under *Risk / Discount Rate* — copy it from there)
- data_year: `2026`

**A few metric rows for one industry (`Software (System & Application)`):**

| industry_name | metric_name | metric_value | unit |
|---|---|---|---|
| Software (System & Application) | number_of_firms | 280 | count |
| Software (System & Application) | beta | 1.28 | ratio |
| Software (System & Application) | d_e_ratio | 0.12 | ratio |
| Software (System & Application) | effective_tax_rate | 0.05 | percent |
| Software (System & Application) | unlevered_beta | 1.16 | ratio |

(Values are illustrative — the real numbers come from the file.)

---

## 6. API endpoints for now

**Datasets**

- `POST /datasets` — create a dataset record
- `GET /datasets` — list datasets
- `GET /datasets/{dataset_id}` — one dataset

**Metrics**

- `POST /datasets/{dataset_id}/metrics` — add a metric row (also usable by the seed script)
- `GET /datasets/{dataset_id}/metrics` — list a dataset's metrics

**Useful filters (add when needed):**

- `GET /datasets/{dataset_id}/metrics?industry=Software`
- `GET /datasets/{dataset_id}/metrics?metric_name=unlevered_beta`

**Not an endpoint:** `scripts/seed_betas.py` — loads the one betas file into the tables.

---

## 7. Out of scope for now

Deliberately **not** building yet:

- company valuation cases (companies / inputs / outputs)
- a general Excel/CSV importer (the one-file seed script is fine; a reusable importer is not)
- frontend, authentication, user accounts
- AI / agent ingestion, scraping other sites
- formulas / valuation math, PDF exports
- full-text search, pgvector semantic search

These are real next steps — just not now.

---

## 8. Done means

This version is done when:

- the `datasets` and `dataset_metrics` tables exist **and were created by an Alembic migration** (not by hand in Adminer)
- a dataset can be created and listed through the API
- metric rows can be added to a dataset and listed back
- the betas dataset has real rows in it (loaded by the seed script, or a handful inserted by hand to start)
- basic tests pass (create + read a dataset, add + read metrics)
- you can see it working in `/docs` and Adminer

---

## 9. Later (one line each, so the ideas aren't lost)

- **Next:** load a second and third dataset (tax rates, margins) — this proves the design scales without schema changes.
- **Then:** add `companies` + valuation cases that *reference* this stored data.
- **Later:** a general importer, scraping, search / pgvector, a frontend, agent ingestion.
