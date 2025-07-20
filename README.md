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
- **api_secrets.yaml** – API keys (ignored by git, create locally)

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
`src/visualization` contains helpers for Plotly maps and simple dashboards. Layers for travel time, cost, safety, individual crime types and composite score can be toggled. Destinations are always visible for context.

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

# TODO List
## Core Implementation Tasks

### Phase 1: Core Infrastructure ✅
- [x] Create main.py CLI entry point
- [x] Create configuration parser and validator
- [x] Set up grid generation logic
- [x] Set up schedule processing
- [x] Create basic data structures

### Phase 2: API Integration
- [x] Implement OSRM routing client
- [x] Add rate limiting and error handling
- [x] Implement local caching system
- [x] Add FBI crime data integration
- [x] Implement crime data caching

### Phase 3: Analysis Engine
- [x] Implement travel time calculations
- [x] Add transportation cost analysis
- [x] Implement safety scoring algorithm
- [x] Calibrate safety scoring parameters
- [x] Create composite scoring system
- [x] Add data validation and error handling

### Phase 4: Visualization
- [x] Implement Plotly map generation
- [x] Add interactive layer toggles
- [x] Create summary statistics tables
- [x] Add top locations ranking
- [x] Generate HTML dashboard output
- [x] Add crime type heatmap layers

### Phase 5: Testing & Polish
- [x] Add comprehensive unit tests
   - [x] Test scheduler utilities (`parse_days`, monthly pattern helpers)
   - [x] Test cache utilities (`clear_expired_cache`, `get_cache_stats`)
   - [ ] Test analyzer cost calculation logic
- [x] Implement integration tests
   - [x] CLI dry run invocation
   - [x] Full analysis run producing HTML output
- [x] Add performance optimization
   - [x] Add progress indicator in route calculations
- [x] Create user documentation
   - [x] Expand README with install and quick start
- [x] Add example configurations
   - [x] Provide sample YAML files in `config/examples`

## System Requirements

### Python Dependencies
The following packages need to be installed (see `requirements.txt`):
- [ ] Verify all dependencies are correctly specified
- [ ] Test installation on clean environment
- [ ] Add version pinning for stability

### File Structure Setup
- [x] Create `data/` directory for caching
- [x] Create `outputs/` directory for results
- [ ] Set up proper directory permissions
- [x] Add `.gitignore` for cache and output files

## Configuration Tasks

### Required Configuration Updates
- [x] Replace center_point with actual location
- [ ] Customize destination addresses for real use case
- [ ] Adjust transportation preferences
- [ ] Fine-tune scoring weights
- [ ] Set appropriate cache duration

### Validation Improvements
- [x] Add geocoding validation for addresses
- [x] Implement network connectivity checks
- [ ] Add disk space validation
- [ ] Create configuration migration tools

## Performance and Scalability

### Optimization Tasks
- [ ] Implement parallel API processing
- [ ] Add memory usage monitoring
 - [x] Optimize cache file formats
- [x] Add OSRM client caching for route requests
 - [x] Add progress indicators
- [x] Vectorize analysis calculations with pandas
- [ ] Implement graceful interruption handling

### Error Recovery
- [ ] Add comprehensive error handling
- [ ] Implement retry mechanisms
- [ ] Create backup data sources
- [ ] Add graceful degradation modes

## Documentation

### User Documentation
- [ ] Create comprehensive README.md
- [ ] Add configuration examples
- [x] Document API key setup process
- [ ] Create troubleshooting guide

### Technical Documentation
- [ ] Document data flow architecture
- [ ] Add API integration details
- [ ] Document caching strategy
- [ ] Create performance tuning guide

## Security and Privacy

### Security Tasks
- [x] Secure API key storage
- [ ] Validate all user inputs
- [ ] Sanitize file paths
- [ ] Add rate limiting protection

### Privacy Considerations
- [ ] Review data retention policies
- [ ] Implement data anonymization
- [ ] Add opt-out mechanisms
- [ ] Document data usage

## Future Enhancements

### Advanced Features
- [ ] Add multiple transportation cost models
- [ ] Implement custom scoring algorithms
- [ ] Add export to external mapping tools
- [ ] Create mobile-responsive visualizations

### Integration Opportunities
- [ ] Real estate data integration
- [ ] Weather data integration
- [ ] Traffic pattern analysis
- [ ] Public transportation integration

---

## Quick Start Checklist

To get the Location Evaluator running:

1. **Setup API Access**
   - [ ] Update `config/api.yaml`
   - [ ] Create `config/api_secrets.yaml` with your FBI API key

2. **Configure Analysis**
   - [ ] Set center_point in `config/analysis.yaml`
   - [ ] Update destinations in `config/destinations.yaml`

3. **Test Installation**
   - [ ] Run `python test_core_components.py`
   - [ ] Run `python main.py --dry-run`

4. **First Analysis**
   - [ ] Run `python main.py --config config --output outputs/test.html`
   - [ ] Verify HTML output is generated

