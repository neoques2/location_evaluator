# Location Evaluator

Location Evaluator is a prototype CLI for exploring residential desirability. It generates a grid of points around a center location, expands destination schedules and calculates routes using a local OSRM server. Crime scoring and cost analysis are included in a simplified form. Output can be an interactive HTML dashboard or raw JSON.

## Features
- Modular YAML configuration files
- Grid generation and schedule processing
- OSRM routing client with request batching and caching
- Placeholder FBI crime data integration
- HTML and JSON output modes
- Dry‑run and cache-only options for testing

## Repository Layout
- `config/` – analysis, destination, transportation, API, weight and output settings
- `src/` – implementation modules (`core/`, `apis/`, `visualization/`, `models/`)
- `tests/` – pytest suite
- `data/` – local cache storage
- `outputs/` – generated analysis results

Run `python main.py --dry-run` to validate the configuration.

## Configuration Overview
Configuration is split into several YAML files:
- **analysis.yaml** – center point, radius and grid spacing
- **destinations.yaml** – addresses with weekly or monthly schedules
- **transportation.yaml** – travel mode preferences
- **api.yaml** – OSRM server settings and rate limits
- **weights.yaml** – scoring weights for time, cost and safety
- **output.yaml** – cache duration and visualization options

See the files in the `config/` directory for examples.

## Data Flow
1. Parse and validate the YAML configuration
2. Build an analysis grid around the center location
3. Expand schedules into individual trips
4. Batch route requests to OSRM (using cache when available)
5. Calculate safety and cost metrics
6. Produce an HTML dashboard or JSON export

## Data Model Summary
Analysis results include location info, travel time and distance, cost, safety statistics and a composite score for each grid point. Data classes for these structures live in `src/models/data_structures.py`.

## Visualization Notes
`src/visualization` contains helpers for Plotly maps and simple dashboards. Layers for travel time, cost, safety and composite score can be toggled. Destinations are always visible for context.

## Roadmap
### Completed
- Core infrastructure (CLI, config parser, grid generator, schedule processor)
- API integration with OSRM and basic crime data
- Caching for geocoding and OSRM route requests
- Basic Plotly visualization

### Planned
- Expand unit and integration tests
- Improve performance (parallel API calls, cache formats)
- Add configuration validation and troubleshooting docs
- Enhance error handling and retry logic
- Explore additional data sources (real estate, weather, public transit)

## Quick Start
1. Install dependencies with `pip install -r requirements.txt`
2. Adjust the YAML files in `config/` for your region
3. Run `python main.py --dry-run` to check the setup
4. Run `python main.py --config config --output outputs/result.html` to generate a report




## Installation

1. Install Python 3.11 or later.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

```bash
# validate configuration
python main.py --dry-run

# run analysis with default config
python main.py --cache-only --output outputs/example.html
```
