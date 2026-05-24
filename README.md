# Minimal HR Attrition Analytics App

A simple Python web dashboard that shows employee attrition analytics from random sample data.

## Features

- KPI cards: employee count, attrition count, attrition rate, active employees, average age
- Charts for department-wise attrition, age-group attrition, education-wise attrition, and attrition by gender
- Job satisfaction pivot table by role
- Random action failures for resilience testing
- Structured log entries for every action (`success` or `error`) in `logs/app_events.log`

## Project Structure

- `app.py` - minimal web server, API endpoints, and dashboard UI
- `src/data/sample_data.py` - random employee data generator
- `src/analytics/metrics.py` - KPI and chart transformations
- `src/actions/handlers.py` - action wrapper with random failure injection
- `src/core/logger.py` - JSON line event logger
- `src/core/failure.py` - random failure utility
- `tests/test_app_logic.py` - smoke tests for data generation and action logging

## Setup

No third-party packages are required. You only need Python 3.10+.

## Run

```powershell
python app.py
```

Then open `http://127.0.0.1:8000` in your browser.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Notes

- Use the **Random Failure Rate** input to increase or reduce the chance of action failures.
- Click action buttons repeatedly (`Load Dashboard`, `Refresh Data`, `Export CSV`) to observe random failures and logs.
- Log entries are JSON lines and can be parsed later for debugging or auditing.

"# NSP-4-S2-S25App" 
