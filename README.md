# Take-Home Assessment for Intern — Oil Desk
 
## Introduction
 
This take-home assessment is designed to evaluate your proficiency in Python, JavaScript, data analysis, backend development, and practical programming judgment. The goal is to build a small but complete data dashboard application for analysing oil/commodity market data.
 
The assessment should demonstrate that you can:
 
* Write clean and maintainable Python code
* Build a simple API using FastAPI
* Store and query data using SQLite
* Write JavaScript, HTML, and CSS to build a usable dashboard
* Analyse time-series data
* Present data clearly using tables, charts, and written explanations
* Structure a small project in a way that is easy to run and review
* Use third-party libraries appropriately and explain why they were chosen
 
## Technical Requirements
 
You must use:
 
* Python 3.11.x
* UV
* FastAPI
* SQLite
* JavaScript, HTML, and CSS
* Jupyter Notebook for exploratory analysis
 
You may use relevant third-party packages, including but not limited to:
 
* pandas
* numpy
* matplotlib
* plotly
* ECharts
* FastAPI-related packages
* SQLite-related packages
* Other clearly justified dependencies
 
Any package you use must be added to `pyproject.toml`.
 
You should use packages sensibly. We are not looking for unnecessary complexity, but we do expect you to choose tools that help you solve the problem clearly and efficiently.
 
For example, you may use pandas and numpy for:
 
* Reading and parsing CSV data
* Filtering and aggregating time-series data
* Calculating moving averages
* Calculating RSI
* Calculating MACD
* Computing backtest metrics
 
You may use charting libraries such as ECharts, Plotly, or matplotlib for:
 
* Price charts
* RSI charts
* MACD charts
* PnL charts
* Drawdown charts
* Dashboard visualisations
 
Your code must be runnable after:
 
```bash
uv sync
```
 
## Use of AI
 
Use of AI tools is permitted for this assessment.
 
However, we expect you to understand, own, and be able to explain everything you submit. Any AI-assisted code should be properly reviewed, adapted, and commented by you.
 
Your submission should include a short section in the README explaining:
 
1. Which AI tools you used, if any.
2. What you used them for.
3. Examples of prompts or instructions you gave to the AI tool.
4. The logic and reasoning you applied when reviewing, changing, and integrating the AI-generated output.
5. Any parts of the solution that were written entirely by you without AI assistance.
 
You should not submit AI-generated code that you do not understand. During review, you may be asked to explain your prompting, implementation choices, calculations, and code structure.
 
We are not assessing whether you avoided AI. We are assessing whether you can use it responsibly, understand the output, and turn it into a working, well-reasoned solution.
 
## Goal
 
Build a dashboard application that loads, stores, analyses, and displays commodity price data.
 
The dashboard should include:
 
* A table view of the data
* Charts showing price history and indicators
* Clear explanations of the calculations and results
* API endpoints serving data from SQLite
* A frontend written in JavaScript
 
The final result should feel like a small internal analytics tool for an Oil Desk.
 
## Repository Instructions
 
1. Fork the provided repository to your GitHub account.
2. Clone your fork locally.
3. Create a `solutions/` directory.
4. Build your application and notebooks inside the repository.
5. Do not commit generated SQLite database files.
6. Commit your work with a clear and sensible Git history.
7. Push your completed solution to your GitHub repository.
8. Share the GitHub link by the deadline provided.
 
Suggested Project Structure
.
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # SQLite connection and query helpers
│   ├── models.py            # Data models or response schemas
│   ├── calculations.py      # Moving averages, RSI, MACD, returns
│   ├── pipeline.py          # CSV load, transform, and database insert
│   ├── backtest.py          # Strategy and performance calculations
│   └── async_pipeline.py    # Async database demonstration
├── frontend/
│   ├── index.html           # Dashboard page
│   ├── styles.css           # Dashboard styling
│   └── app.js               # API calls, table rendering, charts
├── data/
│   └── sample_prices.csv    # Source data file
├── scripts/
│   ├── init_db.py           # Optional database initialisation script
│   └── run_pipeline.py      # Optional script to rebuild database
├── tests/
│   └── test_calculations.py # Optional tests for calculations
├── pyproject.toml
├── README.md
└── .gitignore
 
You may choose a different structure, but it should be easy to understand, run, and review. The important point is that the tasks should connect into one working application rather than separate notebook-style answers
 
---
 
# Questions
 
## Question 1: Python Basics and Data Manipulation
 
### Objective
 
Demonstrate Python skills, CSV handling, and time-series data manipulation.
 
### Task
 
Using the provided CSV file containing commodity price data:
 
1. Load the CSV file using Python.
 
2. Parse dates and numeric price fields correctly.
 
3. Filter the data to include only selected commodities, for example:
 
   * Copper
   * Zinc
   * Crude Oil
 
4. Filter the data for the year 2021.
 
5. Calculate the average price per month for each commodity.
 
6. Plot the monthly average price for each commodity.
 
7. Explain your approach in a Jupyter Notebook.
 
You may use packages such as pandas, numpy, and matplotlib or plotly for this question.
 
### Expected Output
 
Your notebook should show:
 
* How the file is loaded
* How the data is filtered
* How monthly averages are calculated
* A table-like view of the final result
* A chart of monthly average prices
* A clear explanation of your method
 
---
 
## Question 2: SQLite Database and CRUD Operations
 
### Objective
 
Demonstrate basic database design and CRUD operations using SQLite.
 
### Task
 
Create a SQLite database schema to store time-series commodity prices.
 
The schema should include fields such as:
 
* `id`
* `date`
* `commodity`
* `price`
* `source`
* `created_at`
 
You should then demonstrate basic CRUD operations:
 
1. Create the table.
2. Insert records.
3. Read records.
4. Update records.
5. Delete records.
 
### Expected Output
 
Your notebook should include:
 
* The SQL table schema
* Python code that executes the SQL
* Examples of each CRUD operation
* Explanations of what each operation does
 
Do not commit the generated SQLite database file to GitHub.
 
---
 
## Question 3: Data Pipeline and Transformations
 
### Objective
 
Show that you can build a reusable data pipeline and calculate technical indicators.
 
### Task
 
Using the CSV file from Question 1:
 
1. Load and validate the data.
 
2. Filter the data for selected commodities for the years 2020 and 2021.
 
3. Calculate the following indicators for each commodity:
 
   * Fast moving average
   * Medium moving average
   * Slow moving average
   * MACD
   * MACD signal line
   * RSI
 
4. Insert the transformed data into SQLite.
 
5. Use a decorator to log execution details for the database insert step.
 
The decorator should log information such as:
 
* Function name
* Start time
* End time
* Execution duration
* Number of rows inserted
 
You may use pandas and numpy for data transformation, but your solution should still be clear and well explained.
 
### Expected Output
 
Your solution should include:
 
* Reusable Python functions
* Indicator calculations
* SQL insert logic
* A logging decorator
* A short explanation of your data pipeline design
 
---
 
## Question 4: FastAPI Backend
 
### Objective
 
Build an API layer that serves the stored and transformed data.
 
### Task
 
Create a FastAPI application that exposes endpoints for the dashboard.
 
At minimum, include endpoints such as:
 
```text
GET /health
GET /commodities
GET /prices
GET /prices/{commodity}
GET /indicators/{commodity}
GET /summary/{commodity}
```
 
The API should read from SQLite and return JSON responses.
 
### Expected Output
 
Your backend should:
 
* Start successfully with `uv`
* Connect to SQLite
* Return clean JSON responses
* Handle missing or invalid commodities gracefully
* Include basic error handling
* Include clear instructions in the README
 
Example command:
 
```bash
uv run fastapi dev app/main.py
```
 
or:
 
```bash
uv run uvicorn app.main:app --reload
```
 
---
 
## Question 5: JavaScript Dashboard
 
### Objective
 
Build a simple frontend dashboard.
 
### Task
 
Create a dashboard using:
 
* HTML
* CSS
* JavaScript
 
The dashboard should fetch data from your FastAPI backend and display:
 
1. A commodity selector.
 
2. A table of price and indicator data.
 
3. At least two charts, for example:
 
   * Price over time
   * RSI over time
   * MACD and signal line over time
   * Monthly average price
 
4. Short written explanations of the selected commodity’s data and indicators.
 
You may use a JavaScript charting library such as ECharts or Plotly. You may also choose to build your own charts using SVG or Canvas.
 
### Expected Output
 
Your dashboard should:
 
* Load data from the FastAPI API
* Update when the selected commodity changes
* Display data in a readable table
* Render clear charts
* Include labels, axes, legends, and titles
* Provide written explanations of what the user is seeing
 
---
 
## Question 6: Backtesting
 
### Objective
 
Demonstrate understanding of a simple trading strategy and backtesting logic.
 
### Task
 
Backtest either an RSI-based strategy or a MACD-based strategy.
 
Examples:
 
### RSI Strategy
 
* Buy when RSI falls below 30
* Sell or exit when RSI rises above 70
 
### MACD Strategy
 
* Buy when MACD crosses above the signal line
* Sell or exit when MACD crosses below the signal line
 
You should calculate and display:
 
* Daily strategy returns
* Cumulative PnL
* Annualised Sharpe ratio
* Drawdown over time
* Maximum drawdown
 
Your code should be efficient, clear, and well explained. You may use pandas, numpy, matplotlib, plotly, or other appropriate packages.
 
### Expected Output
 
Your notebook and/or dashboard should include:
 
* Strategy explanation
* Backtest assumptions
* PnL over time
* Sharpe ratio
* Drawdown chart or table
* Commentary on the strategy’s performance
 
---
 
## Question 7: Async Data Pipeline
 
### Objective
 
Show understanding of asynchronous programming in Python.
 
### Task
 
Modify part of your data pipeline to use asynchronous code.
 
You should:
 
1. Write transformed data to the database asynchronously.
2. Read from the database five times concurrently using `asyncio.gather()`.
3. Explain when async programming is useful and when it is not.
 
You may use an async-compatible SQLite package if you add it to `pyproject.toml`, or you may demonstrate async orchestration around database work clearly.
 
### Expected Output
 
Your solution should include:
 
* An async insert or write process
* Five concurrent reads using `asyncio.gather()`
* Explanation of the async design
* Notes on any limitations of SQLite for concurrent workloads
 
---
 
# README Requirements
 
Your repository must include a `README.md` explaining:
 
1. How to install dependencies.
2. How to run the data pipeline.
3. How to create or initialise the SQLite database.
4. How to start the FastAPI server.
5. How to open the frontend dashboard.
6. How to run the notebooks.
7. Any design decisions or assumptions.
8. Any known limitations.
9. Which packages were used and why.
10. Whether AI tools were used, including prompts, reasoning, and how AI-generated output was reviewed or modified.
 
Example commands:
 
```bash
uv sync
uv run python -m app.pipeline
uv run uvicorn app.main:app --reload
```
 
---
 
# Submission Guidelines
 
Before submitting, ensure that:
 
* Your code runs after `uv sync`.
* Your notebooks are committed under `solutions/`.
* Your frontend is included in the repository.
* Your database file is not committed.
* Your `pyproject.toml` includes all dependencies.
* Your Git commit history is clean and meaningful.
* Your README is clear enough for someone else to run your project.
* Your README explains your package choices.
* Your README includes the required AI-use explanation.
 
Submit your GitHub repository URL by email to the address provided, by the deadline provided.
 
---
 
# Assessment Criteria
 
We will evaluate your submission based on:
 
* Correctness of the data processing
* Code clarity and organisation
* Quality of Python implementation
* Quality of JavaScript implementation
* API design and error handling
* SQLite schema design
* Quality of the dashboard
* Correctness of RSI, MACD, PnL, Sharpe, and drawdown calculations
* Explanation of reasoning and assumptions
* Explanation of package choices
* Explanation of AI prompting and AI-assisted implementation, if applicable
* Sensible Git usage
 
Good luck.
