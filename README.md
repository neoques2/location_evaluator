# Location Evaluator

Prototype CLI tool for exploring residential desirability. It builds a grid of potential locations, processes schedules, and (eventually) scores each point based on travel time, cost, and safety.

## Features
- Modular YAML configuration
- CLI with dry‑run and cache options
- Grid generation and schedule processing implemented
- OSRM routing (local server) and crime data integrations are placeholders
- Generates simple HTML/JSON output for now

## Repository Layout
- `config/` – analysis, destinations, transportation, API, weight, and output settings
- `src/` – implementation modules
  - `config_parser.py` and `analyzer.py`
  - `core/` – grid generator and scheduler
  - `apis/` – OSRM routing, caching, crime data
  - `visualization/` – plotly map and dashboard helpers
  - `analysis/` – experimental analysis scripts
  - `models/` – dataclasses
- `tests/` – basic tests
- `spec/` – design documents

Run `python main.py --dry-run` to validate configuration and see the planned analysis.
