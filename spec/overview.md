# Location Evaluator - Technical Specification

## Overview
The Location Evaluator is a Python CLI tool that analyzes residential location desirability based on commute patterns, travel costs, and safety metrics. It generates interactive Plotly maps showing regional analysis across a configurable grid of potential locations.

## Core Concept
Instead of evaluating specific home candidates, the tool analyzes **every location** on a regional grid to determine optimal residential areas based on:
- Travel time to scheduled destinations
- Transportation costs (miles driven/walked/biked, transit fares)
- Crime/safety metrics
- Composite desirability scores

## Architecture
```
location_evaluator/
├── config.yaml              # User configuration
├── main.py                  # CLI entry point
├── src/
│   ├── grid_generator.py    # Generate analysis grid
│   ├── maps_client.py       # Google Maps API integration
│   ├── crime_data.py        # FBI UCR data integration
│   ├── analyzer.py          # Core analysis logic
│   └── visualizer.py        # Plotly map generation
├── data/
│   ├── grid_cache/          # Cached route data by lat/lon
│   ├── crime_data/          # Downloaded crime statistics
│   └── analysis_results.json # Final analysis output
├── outputs/
│   └── location_analysis.html # Interactive Plotly map
└── spec/
    └── overview.md          # This file
```

## Data Flow
1. **Configuration**: Read YAML config with destinations and schedules
2. **Grid Generation**: Create regular grid of lat/lon points across region
3. **Route Calculation**: For each grid point, calculate routes to all destinations
4. **Schedule Processing**: Apply exact departure times and frequencies
5. **Cost Calculation**: Sum travel distances and transit costs
6. **Crime Integration**: Overlay FBI UCR crime data
7. **Visualization**: Generate interactive Plotly map with toggle layers

## Key Design Decisions
- **Grid-based analysis**: Evaluate all locations, not specific candidates
- **Exact scheduling**: Support precise departure times and monthly recurrence
- **Local processing**: All data cached locally for offline analysis
- **Batch API calls**: Pre-calculate all routes to minimize API usage
- **Layered visualization**: Toggle between time, cost, safety, and composite metrics

## Next Steps
- Define detailed YAML configuration format
- Specify grid-based caching structure
- Design output data format for location metrics
- Plan Google Maps API batch processing strategy