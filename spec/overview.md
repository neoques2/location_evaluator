# Location Evaluator - Overview

The Location Evaluator analyzes residential areas by combining travel time, transportation cost and crime metrics. It builds a grid around a center point, processes destination schedules and (in future) scores each location. Results will be displayed on interactive Plotly maps.

## Directory Layout
```text
location_evaluator/
├── config/               # YAML configuration files
├── main.py               # CLI entry point
├── src/
│   ├── config_parser.py  # Config loading and validation
│   ├── analyzer.py       # Core analysis engine
│   ├── core/             # grid_generator.py, scheduler.py
│   ├── apis/             # google_maps.py, cache.py, crime_data.py, rate_limiter.py
│   ├── visualization/    # plotly_maps.py, dashboard.py, statistics.py
│   ├── analysis/         # experimental analysis scripts
│   └── models/           # dataclasses and schemas
├── tests/                # test suite
└── spec/                 # design documentation
```

## Data Flow
1. **Configuration** – merge YAML files and validate values
2. **Grid Generation** – produce evenly spaced points across the region
3. **Schedule Processing** – expand weekly and monthly patterns
4. **Route Calculation** – (placeholder) call Google Maps and cache results
5. **Scoring** – (placeholder) compute travel time, cost, and safety scores
6. **Visualization** – build Plotly dashboards or JSON exports

Only configuration, grid generation and schedule processing are fully implemented today.
