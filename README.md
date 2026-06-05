# Oil Desk — Commodity Analytics Dashboard

A data pipeline and analytics dashboard for daily commodity settlement prices. Covers all seven assessment questions: data manipulation, SQLite CRUD, a transformation pipeline with a logging decorator, a FastAPI backend, a JavaScript dashboard, backtesting, and an async pipeline.

---

## Requirements

- Python 3.11
- [uv](https://docs.astral.sh/uv/)

```bash
uv sync
```

To activate the ruff pre-commit hook (linting and formatting on every commit):

```bash
uv run pre-commit install
```

---

## Quick Start

Run these steps in order.

**1. Initialise the database**

Creates the SQLite tables. Only needed once.

```bash
uv run python scripts/init_db.py
```

**2. Run the data pipeline**

Loads `data/MarketData.csv`, filters Copper, Zinc, and Crude Oil for 2020–2021, computes all indicators, and inserts the results into `data/oildesk.db`.

```bash
uv run python scripts/run_pipeline.py
```

**3. Start the API**

```bash
uv run uvicorn app.main:app --reload
```

Available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**4. Open the dashboard**

```bash
cd frontend && python -m http.server 5500
```

Open `http://localhost:5500`. The dashboard connects to the API at `localhost:8000` automatically.

**5. Open the notebooks**

```bash
uv run jupyter notebook
```

Notebooks are in `solutions/`. Q3 and Q7 require the pipeline to have been run first (step 2).

---

## Tests

```bash
uv run pytest tests/ -v
```

With coverage (99% on the core `app/` modules):

```bash
uv run pytest tests/ --cov
```

37 tests across four files.

**`test_calculations.py` — unit tests for indicator correctness**

- RSI is always in [0, 100] by definition
- MACD histogram satisfies the identity `hist = macd − signal` to floating-point precision
- MA20, MA50, and MA200 produce NaN for exactly the right number of warmup rows, then a valid value at the exact boundary row
- MACD produces NaN until 26 bars of data are available
- `macd_signal` at the first valid MACD row equals `macd` at that row — verifies the signal EWM starts fresh with no pre-warmup contamination
- In a monotonically rising series, `ma_fast > ma_medium > ma_slow` holds at the last row
- Indicators for one commodity do not bleed into another — groupby isolation is verified by putting a rising and a flat series in the same dataframe and checking that the flat commodity's MAs stay exactly at its price
- The pipeline produces no duplicate `(date, commodity)` pairs against the real CSV
- RSI on a flat price series (no gains or losses) produces NaN, not a spurious value

**`test_api.py` — integration tests for all endpoints**

`conftest.py` builds a temporary SQLite database from the real CSV and overrides the FastAPI `get_db` dependency to point at it. Every API test runs against real pipeline data without depending on the `data/oildesk.db` file on disk.

- `/health` returns 200 and `{"status": "ok"}`
- `/health` returns 500 when the database raises an error
- `/commodities` returns all three expected commodities
- `/prices` returns rows; `/prices/{commodity}` is parametrized over all three commodities and verifies each returns only its own rows
- `/indicators/{commodity}` is parametrized and checks all indicator columns are present
- `/summary/{commodity}` is parametrized and checks all required statistics are present
- `/backtest/{commodity}` is parametrized and checks both the metrics block and the daily series are returned with the expected fields
- Every commodity endpoint (`/prices`, `/indicators`, `/summary`, `/backtest`) returns 404 for an unknown commodity with an error message naming the invalid input

**`test_database.py` — unit tests for database helpers**

- `get_connection` creates the parent directory if it does not exist
- `get_summary` returns an empty dict for a commodity not in the table

**`test_pipeline.py` — integration tests for the data pipeline**

- `insert_indicators` opens and closes its own connection when none is provided
- `run_pipeline` completes end-to-end and populates the indicators table

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | API and database status |
| `GET /commodities` | Available commodity names |
| `GET /prices` | All price and indicator rows |
| `GET /prices/{commodity}` | Price and indicator rows for one commodity |
| `GET /indicators/{commodity}` | Indicator columns only (MA, MACD, RSI) |
| `GET /summary/{commodity}` | Price statistics and latest indicator values |
| `GET /backtest/{commodity}` | Backtest metrics and daily PnL series |

Commodity names in the URL are normalised to lowercase — `/prices/Copper` and `/prices/copper` both work.

---

## Project Structure

```
.
├── app/
│   ├── config.py               Centralised constants and paths
│   ├── database.py             SQLite connection and query helpers
│   ├── models.py               Pydantic response schemas
│   ├── calculations.py         Moving averages, MACD, RSI
│   ├── pipeline.py             CSV load, transform, and database insert
│   ├── backtest.py             Signal generation and performance metrics
│   ├── async_pipeline.py       Async insert and concurrent reads
│   └── main.py                 FastAPI endpoints
├── frontend/
│   ├── index.html              Dashboard layout
│   ├── styles.css              Styles and theme
│   └── app.js                  API calls, charts, table rendering
├── solutions/
│   ├── q1_data_manipulation.ipynb    CSV loading, filtering, monthly averages, charts
│   ├── q2_sqlite_crud.ipynb          Schema design and CRUD operations
│   ├── q3_pipeline.ipynb             Pipeline walkthrough and logging decorator
│   ├── q6_backtest.ipynb             Strategy design, metrics, return distribution, transaction cost sensitivity
│   └── q7_async.ipynb                Async insert and concurrent reads
├── scripts/
│   ├── init_db.py              Create database tables
│   └── run_pipeline.py         Run the full data pipeline
├── tests/
│   ├── conftest.py             Test database fixture and TestClient setup
│   ├── test_calculations.py    Unit tests for indicator correctness
│   ├── test_database.py        Unit tests for database helpers
│   ├── test_pipeline.py        Integration tests for the data pipeline
│   └── test_api.py             Integration tests for all API endpoints
├── data/
│   └── MarketData.csv
├── pyproject.toml
└── uv.lock
```

Q4 (FastAPI backend) and Q5 (JavaScript dashboard) are implemented as the live application rather than notebooks.

---

## Design Decisions

**Single indicators table**
Prices and computed indicators are stored in one `indicators` table rather than separate tables. This avoids joins on every API request. A separate `prices` table is used for the Q2 CRUD demonstration.

**Composite index on `(commodity, date)`**
Every API query filters by commodity and orders by date. The composite index ensures these queries scan only the relevant rows rather than the full table.

**Wilder RSI**
RSI uses Wilder's smoothing (`alpha = 1/period`, `adjust=False`) rather than a standard EMA. This matches the calculation on Bloomberg and most trading platforms. The 14-day period is the daily standard.

**Composite signal strategy**
The backtest combines three signals: price vs MA200 (trend filter), RSI momentum, and MA20/MA50 cross. Each signal returns −1, 0, or +1. A position is entered when the average of all three exceeds 0.5, meaning at least two signals must agree. The strategy is long/flat only — no short positions — which reflects how a physical commodity desk would operate.

**Log returns**
The backtest uses log returns rather than simple percentage returns. Log returns are additive, which makes time-series cumulation mathematically consistent. WTI crude oil went negative in April 2020; those rows produce NaN log returns that are excluded from all metrics.

**Idempotent pipeline**
`INSERT OR IGNORE` with a `UNIQUE(date, commodity)` constraint means the pipeline can be run multiple times safely without creating duplicates.

**No look-ahead bias**
The backtest applies `position.shift(1)` before multiplying by the daily return. The signal is generated at the close of day T and the return is realised on day T+1. Without the shift, today's RSI would determine today's return — a look-ahead bias that would overstate strategy performance.

**Backtest computed on-demand**
The `/backtest/{commodity}` endpoint runs the full calculation at request time rather than pre-storing results in the database. This avoids serving stale metrics if the pipeline is rerun, and the dataset is small enough that the computation is negligible.

---

## Known Limitations

- **Short dataset.** Two years (2020–2021) is not enough for robust strategy evaluation. A proper backtest would span multiple market regimes and ideally more of data.
- **MA200 warmup.** The 200-day MA requires 200 bars before it produces a value. Combined with MACD and RSI warmup, the strategy is only active for around 320 of 523 trading days, which limits statistical significance.
- **No transaction costs.** The backtest assumes zero costs and no slippage. The Q6 notebook includes a sensitivity analysis at 0.1%, 0.5%, and 1.0% round-trip cost to show the break-even point, but the primary results are reported without costs.
- **SQLite concurrency.** The database we're using (SQLite) can only handle one person saving data at a time. If two people try to save at the same moment, one has to wait. For a real app with many users, we would switch to a more powerful database.

---

## Dependencies

**Python**

| Package | Purpose |
|---------|---------|
| `fastapi` | API framework — request validation, Pydantic integration, automatic OpenAPI docs |
| `uvicorn` | ASGI server for FastAPI |
| `pandas` | CSV loading, time-series filtering, groupby/transform for indicator calculations |
| `numpy` | Log returns, EWM smoothing, sign function for signals |
| `aiosqlite` | Async-compatible SQLite driver for the Q7 async pipeline |
| `matplotlib` | Charts in the Jupyter notebooks |
| `jupyter` / `ipykernel` | Notebook environment |
| `pytest` | Unit and integration tests |
| `pytest-cov` | Test coverage measurement and reporting |
| `httpx2` | HTTP client required by FastAPI's `TestClient` for API integration tests |
| `ruff` | Linter and formatter, run automatically on every commit via pre-commit |
| `pre-commit` | Git hook runner |

**JavaScript** (loaded from CDN, no install required)

| Library | Purpose |
|---------|---------|
| Chart.js 4.4.1 | Price, RSI, MACD, PnL, and drawdown charts |
| chartjs-plugin-zoom | Scroll-to-zoom and drag-to-pan on all charts |

---

## Use of AI

I used Claude (claude.ai and Claude Code CLI) throughout the assessment.

**Workflow**

My approach was to use AI as a tool for execution, not a substitute for thinking. Before writing any code I worked out the architecture — what the pipeline stages would be, what the database schema should look like, how the backtest needed to handle position timing to avoid look-ahead bias. Once the design was clear, I used AI to generate initial implementations and catch errors quickly, which let me test ideas and iterate faster than writing everything from scratch.

I built the project piece by piece rather than generating the full codebase at once. Each module was written, reviewed, and tested before moving to the next. This kept me in control of what was happening and meant I could catch inconsistencies before they propagated across files.

For the Jupyter notebooks I asked for structural templates; cell layout, section headings, code skeletons and then read through every cell carefully before running it, modifying the logic and explanations where I disagreed or wanted to add my own interpretation.

Once the code was functionally complete, I used Claude Code to do a final review pass across the full project: identifying bugs, inefficient patterns, and cross file inconsistencies that are easy to miss. Every suggestion is reviewed carefully before accepting it.

**How I generated prompts**

Each prompt included a role, context, and explicit requirements. Open-ended questions were avoided — prompts described exactly what was needed and why. For complex tasks, ChatGPT was sometimes used to rephrase and sharpen the prompt before sending it to Claude.

Examples:

- *"You are a senior database engineer. I am building a FastAPI application serving commodity indicator data for three commodities. Every API query filters by commodity and orders by date. Design a SQLite schema with appropriate types, a UNIQUE constraint to make inserts idempotent, and indexes that directly benefit those query patterns. Explain the tradeoff between one combined table versus separate prices and indicators tables."*

- *"You are a quantitative developer. Implement a composite signal backtest in pandas. Three signals each return −1, 0, or +1: price vs MA200, RSI momentum, and MA20/MA50 cross. Position is long when the average of the three exceeds 0.5, flat otherwise — no short positions. Use log returns. Before returning the code, trace through the position timing to confirm the signal from day T is applied to day T+1's return and there is no look-ahead bias."*

- *"I have a function compute_all_indicators(df) that calculates moving averages, MACD, and RSI per commodity group using groupby. What properties should I test to be confident the function is correct? Consider: mathematical identities, exact warmup boundary rows, isolation between commodity groups, and edge cases in the input. For each property, write a pytest test that would catch a failure."*

- *"Review the following files for: correctness (logic errors, off-by-one mistakes), consistency (naming and patterns across modules), and inefficiency (pandas operations that could be vectorised). Ignore formatting — that is handled by ruff. Be specific with file names and line numbers."*

**How I reviewed AI output**
Nothing was accepted without being read, understood, and tested. For any calculation or logic, the output was verified against the specification or expected behaviour before being committed — not just run to see if it didn't crash. When AI suggested a change, the reasoning behind it was checked independently before applying it. Anything that could not be explained or justified was not kept.

**My contributions**

*Strategy design.* The composite signal approach — trend filter, RSI momentum, and MA cross was a choice over the simpler RSI or MACD crossover the brief described. A single indicator on a two-year dataset is easy to overfit; requiring at least two signals to agree (threshold of 0.5) and restricting positions to long/flat (reflecting how a physical commodity desk operates) are decisions made before any code was written.

*Test design.* The test cases were specified before any code was generated: groupby isolation between commodities, exact warmup boundary rows, RSI behaviour on flat prices, no duplicate date/commodity pairs from the real CSV. AI generated the implementations from those specifications and was asked to flag anything missing.

*Analysis and interpretation.* The commentary throughout the notebooks — what the indicators signal in context, what the backtest results mean given 2020–2021 market conditions, the caveats around warmup period and statistical significance — reflects the analysis. AI helped tighten the language, not produce the judgements.

*Dashboard layout.* The information architecture — what to surface, how to organise the stat cards, which charts sit side by side — was designed before implementation. AI wrote the Chart.js code from that specification.
