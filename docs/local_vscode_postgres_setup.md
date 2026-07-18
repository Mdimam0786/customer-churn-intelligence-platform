# Running This Project Locally in VS Code + Connecting to Real PostgreSQL

Author: Md Imamuddin

*A quick but important note before you start: never paste a real database password into a chat with any AI assistant (including this one) — it should only ever live in your own local `.env` file. This guide shows you exactly where that file goes and how it stays private on your machine.*

---

## Part 1 — Open the Project in VS Code

1. Unzip the project folder somewhere on your computer, e.g. `C:\Projects\customer-churn-intelligence-platform` (Windows) or `~/Projects/customer-churn-intelligence-platform` (Mac/Linux).
2. Open **VS Code**.
3. `File` → `Open Folder...` → select the unzipped project folder.
4. Install these VS Code extensions (Extensions icon in the left sidebar, or `Ctrl+Shift+X`):
   - **Python** (by Microsoft) — required
   - **Pylance** — usually installs automatically with Python
   - **SQLTools** + **SQLTools PostgreSQL Driver** — lets you browse your Postgres database directly inside VS Code
   - **Rainbow CSV** — optional, makes CSV files easier to read in the editor

---

## Part 2 — Set Up Your Python Environment

Open the VS Code integrated terminal: `` Ctrl+` `` (backtick), or `Terminal` → `New Terminal`.

```bash
# Create a virtual environment (keeps this project's packages separate from your system Python)
python3 -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install everything this project needs
pip install -r requirements.txt
```

Then tell VS Code to use this environment: `Ctrl+Shift+P` → type "Python: Select Interpreter" → choose the one inside `./venv/`.

---

## Part 3 — Install PostgreSQL Locally

Pick ONE of these two options.

### Option A: Install PostgreSQL directly (Windows/Mac)
1. Download from https://www.postgresql.org/download/ (version 14 or higher, matching this project's target)
2. During install, you'll be asked to set a password for the default `postgres` superuser — **write this down somewhere safe**, you'll need it in Part 4 (but never paste it into a chat with me).
3. Note the port (default `5432`) — you'll need it too.

### Option B: Use Docker instead (faster, no install clutter)
If you have Docker Desktop installed:
```bash
docker run --name churn-postgres -e POSTGRES_PASSWORD=yourpasswordhere -e POSTGRES_DB=churn_intelligence_platform -p 5432:5432 -d postgres:14
```
This starts a real PostgreSQL 14 server in a container. Replace `yourpasswordhere` with your own password — this command runs entirely on YOUR machine, so it's safe to put a real password directly in your own terminal (just not in this chat).

---

## Part 4 — Create the Database (if you didn't use Docker's `-e POSTGRES_DB` above)

Open a terminal and connect as the superuser:
```bash
psql -U postgres -h localhost
```
It will prompt for the password you set in Part 3. Then run:
```sql
CREATE DATABASE churn_intelligence_platform;
\q
```

---

## Part 5 — Set Your REAL Credentials Locally (Never in Chat)

1. In VS Code's file explorer, find `.env.example` in the project root.
2. Right-click it → duplicate it → rename the copy to `.env` (note: no `.example` at the end).
3. Open `.env` and edit this one line with YOUR real details:
   ```
   DATABASE_URL=postgresql://postgres:YOUR_REAL_PASSWORD@localhost:5432/churn_intelligence_platform
   ```
4. Save the file. **This file is already listed in `.gitignore`**, so it will never be committed to GitHub or seen by anyone but you — verify this yourself:
   ```bash
   git check-ignore -v .env
   ```
   This should print a line confirming `.env` is ignored. If it prints nothing, stop and fix your `.gitignore` before continuing.

---

## Part 6 — Load Real Data Into Your Real PostgreSQL Database

This project ships a brand-new script, `src/data_engineering/load_to_postgres.py`, built specifically for this step. It:
1. Reads your `DATABASE_URL` from `.env`
2. Runs the real schema files in `sql/schema/` against your database (creating the 6 dimension tables + 1 fact table)
3. Re-runs the same real ingestion → cleaning → feature engineering pipeline used everywhere else in this project
4. Loads the real, cleaned data into your actual PostgreSQL tables

Run it from the project root (with your virtual environment activated):
```bash
python3 -m src.data_engineering.load_to_postgres
```

You should see log output ending with something like:
```
VERIFICATION QUERY against your real Postgres database: total_customers=7043, churn_rate_pct=26.54
```

If you see that exact churn rate (26.54%), your real PostgreSQL database now has the real, correct data in it — matching every number in this project's reports exactly.

---

## Part 7 — Verify With SQLTools (Inside VS Code)

1. Click the SQLTools icon in the VS Code sidebar
2. Add a new connection → PostgreSQL → fill in: host `localhost`, port `5432`, database `churn_intelligence_platform`, username `postgres`, password (it can read from your `.env` or you can type it directly into SQLTools's own connection form — either way, it stays local to your VS Code settings, never in chat)
3. Once connected, you can browse `fact_subscription` and all 6 dimension tables directly, and run any of the real queries from `sql/analysis_queries/` right inside VS Code

---

## Part 8 — Run the Stored Procedures & Views (True PostgreSQL Features)

Now that you have a REAL Postgres server, you can run the SQL that SQLite couldn't (materialized views, stored procedures):
```bash
psql -U postgres -h localhost -d churn_intelligence_platform -f sql/views/01_vw_customer_health_score.sql
psql -U postgres -h localhost -d churn_intelligence_platform -f sql/views/02_materialized_views.sql
psql -U postgres -h localhost -d churn_intelligence_platform -f sql/procedures/01_stored_procedures.sql
```

Then test them for real:
```sql
SELECT * FROM vw_customer_health_score ORDER BY customer_health_score ASC LIMIT 10;
SELECT * FROM fn_get_high_risk_customers(80, 'Month-to-month');
CALL sp_refresh_kpi_rollups();
```

This is the first time in this project these specific PostgreSQL-only features (materialized views, stored procedures/functions) will have actually executed — everything before this was verified via the SQLite logic-equivalent stand-in, documented honestly in `docs/sql_verification_log.md`.

---

## Part 9 — Point Power BI at Your Real Database (Optional)

If you have Power BI Desktop:
1. **Get Data** → **PostgreSQL database**
2. Server: `localhost:5432`, Database: `churn_intelligence_platform`
3. Enter your username/password when prompted (stored securely by Power BI itself, not in any project file)
4. Choose **Import** mode (not DirectQuery — this dataset is small enough that Import is faster and simpler)
5. Now every table in `powerbi_data_model.md`'s relationship diagram is a REAL live table instead of a CSV import — build the relationships exactly as described in `docs/powerbi_dashboard_guide.md` and the walkthrough files.

---

## Part 10 — Run the Streamlit App Locally

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

It should open automatically at `http://localhost:8501`. The Streamlit app currently reads from the bundled SQLite file and CSVs (`streamlit_app/data/`), NOT your new Postgres database — that's a deliberate, separate data path so the app stays fully self-contained for easy sharing/deployment. If you'd like, this is a natural next enhancement: pointing `streamlit_app/pages/sql_insights.py` at your real Postgres instance instead of the bundled SQLite file, using the same `.env`-based connection pattern as `load_to_postgres.py`.

---

## Troubleshooting Checklist

| Problem | Likely Fix |
|---|---|
| `DATABASE_URL not found` error | You didn't create `.env` from `.env.example`, or forgot to fill it in |
| `psycopg2.OperationalError: connection refused` | PostgreSQL isn't running — start it (Docker: `docker start churn-postgres`; native install: check your OS's services panel) |
| `relation "fact_subscription" already exists` | Harmless — the DDL uses `CREATE TABLE IF NOT EXISTS`, safe to ignore or re-run |
| Password authentication failed | Double-check the password in `.env` matches what you set when installing/running Postgres |
| VS Code doesn't see your venv packages | Re-run "Python: Select Interpreter" and make sure it points to `./venv/bin/python` (or `venv\Scripts\python.exe` on Windows) |

---

## Quick Reference: What Runs Where

| Component | Data Source |
|---|---|
| `src/data_engineering/etl_pipeline.py` | Builds the SQLite demo database (`data/processed/churn_intelligence.db`) |
| `src/data_engineering/load_to_postgres.py` | **New** — loads the same real data into YOUR real PostgreSQL instance |
| `sql/analysis_queries/*.sql` | Written for PostgreSQL; run via `psql` or SQLTools against your real database |
| Power BI | Can connect to either the CSV exports (`powerbi/data_export/`) or your live Postgres instance |
| Streamlit app | Uses its own bundled SQLite + CSV copies in `streamlit_app/data/` (self-contained for easy deployment) |
