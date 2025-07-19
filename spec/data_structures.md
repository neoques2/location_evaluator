# Data Structures Specification

## Analysis Data Architecture

### Grid Point Analysis Design

Each grid point in the analysis produces a comprehensive result containing five main components:

#### Location Information
- **Geographic coordinates**: Precise latitude and longitude
- **Address approximation**: Nearest street address or postal code
- **Neighborhood identification**: Local area name for context
- **Points of interest**: Nearby landmarks and facilities within 0.5 miles

#### Travel Analysis Structure
- **Time aggregation**: Weekly and monthly travel time totals
- **Destination breakdown**: Per-destination trip frequencies and times
- **Route details**: Individual route calculations with mode, duration, and distance
- **Schedule integration**: Links to specific departure times and patterns

#### Cost Analysis Components
- **Transportation totals**: Weekly and monthly cost summaries
- **Mode breakdown**: Separate tracking for driving miles, walking miles, biking miles, transit costs
- **Destination attribution**: Cost breakdown by destination category
- **Rate calculations**: Standardized cost per mile for driving ($0.65/mile default)

#### Safety Analysis Data
- **Crime scoring**: Normalized 0-1 scale (lower = safer)
- **Crime categorization**: Violent, property, and other crime type breakdowns
- **Incident proximity**: Count of incidents within configurable radius
- **Letter grading**: A+ to F safety grade for intuitive interpretation

#### Composite Scoring System
- **Overall score**: Weighted combination of all factors (0-1 scale, higher = better)
- **Component scores**: Individual normalized scores for travel time, cost, and safety
- **Ranking**: Letter grade and percentile rank within analyzed region
- **Customizable weights**: Configurable importance of each factor

## Caching System Design

### Geographic Cache Hierarchy
The caching system organizes route data using a geographic hierarchy for efficient lookup and storage:

#### Directory Structure Design
- **Latitude-based folders**: Truncated to 2 decimal places for reasonable grouping
- **Longitude-based subfolders**: Further subdivision for optimal file distribution  
- **Cache file naming**: Hashed keys to avoid filesystem limitations
- **Metadata separation**: Cache timestamps and expiry information stored separately

#### Cache File Format Design
- **Cache metadata**: Creation time, expiration, geographic bounds
- **Route storage**: Organized by destination address and departure time
- **Geocoded coordinates**: Cached destination coordinates to avoid re-geocoding
- **Route details**: Duration, distance, cost, and transportation mode
- **Step-by-step directions**: Optional detailed routing information

### Analysis Results Architecture

#### Metadata Structure
- **Generation timestamp**: When analysis was completed
- **Grid configuration**: Size, total points, center coordinates
- **Geographic bounds**: North, south, east, west boundaries of analysis area
- **Analysis parameters**: Configuration settings used for reproducibility

#### Grid Points Collection
- **Complete dataset**: All analyzed grid points with full analysis results
- **Structured format**: Consistent data structure across all points
- **Spatial indexing**: Geographic coordinates for mapping and lookup
- **Analysis completeness**: Indicators for successful vs. partial analysis

#### Regional Statistics Summary
- **Metric distributions**: Min, max, average, median for all key metrics
- **Comparative analysis**: Regional benchmarks and percentile rankings
- **Top locations**: Best-scoring areas for quick reference
- **Coverage metrics**: Analysis completeness and data quality indicators

### Data Type Definitions

#### Scalar Types
- **Coordinates**: Decimal degrees with 4+ decimal place precision
- **Time values**: Minutes as integers, hours as decimals where appropriate
- **Cost values**: US dollars with 2 decimal place precision
- **Scores**: Normalized 0-1 scale with 2-3 decimal place precision

#### Enumerated Types
- **Transportation modes**: driving, walking, transit, biking
- **Crime categories**: violent, property, other
- **Schedule frequencies**: weekly, monthly
- **Safety grades**: A+, A, A-, B+, B, B-, C+, C, C-, D, F

### Implementation Reference
See data structure implementations in:
- `src/models/data_structures.py` - Python dataclasses and type definitions
- `src/apis/cache.py` - Cache file management and structure
- `src/visualization/statistics.py` - Regional statistics calculations
- JSON schema documentation embedded in source files