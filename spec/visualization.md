# Visualization Specification

## Interactive Map Design

### Core Visualization Features
- **Regional heatmap**: Dense grid visualization showing analysis results across the study area
- **Multi-layer system**: Toggleable layers for different metrics (travel time, cost, safety, composite)
- **Interactive tooltips**: Detailed hover information with metric breakdowns and local context
- **Dynamic controls**: Layer selection buttons and zoom/pan capabilities
- **Legend system**: Color scale explanations and metric ranges

### Map Layer Architecture

#### Travel Time Layer
- **Data visualization**: Weekly travel time aggregated across all destinations
- **Color scheme**: Viridis colorscale (dark blue = low time, bright yellow = high time)
- **Tooltip content**: Total weekly minutes, destination breakdown, coordinate information
- **Default state**: Visible on initial load

#### Transportation Cost Layer
- **Data visualization**: Combined monthly cost including driving miles and transit fares
- **Color scheme**: Red colorscale (light = low cost, dark red = high cost)
- **Cost calculation**: Driving miles × $0.65/mile + transit costs
- **Tooltip content**: Total monthly cost, driving miles, transit expenses

#### Safety Layer
- **Data visualization**: Inverted crime score (higher values = safer areas)
- **Color scheme**: Red-Yellow-Green scale (red = unsafe, green = safe)
- **Score calculation**: 1 - normalized crime score for intuitive interpretation
- **Tooltip content**: Safety grade, crime score, nearby incident count

#### Composite Score Layer
- **Data visualization**: Weighted combination of travel time, cost, and safety
- **Color scheme**: Plasma colorscale for high dynamic range
- **Score components**: Configurable weights (default: 40% time, 30% cost, 30% safety)
- **Tooltip content**: Overall score, letter grade, percentile rank, component breakdowns

### User Interface Design

#### Layer Toggle System
- **Button layout**: Horizontal button bar at top of map
- **Active state indication**: Highlighted button shows current layer
- **Layer visibility**: Only one analysis layer visible at a time, destinations always visible
- **Responsive design**: Buttons adapt to different screen sizes

#### Destination Markers
- **Visual design**: Red star markers for high visibility
- **Size**: 12px markers, prominent but not overwhelming
- **Hover information**: Destination name and category
- **Persistent visibility**: Always shown regardless of selected layer

### Dashboard Layout

#### Multi-panel Design
- **Main map**: Full-width interactive map in top section
- **Summary statistics**: Regional statistics table in bottom-left
- **Top locations**: Best-scoring locations list in bottom-right
- **Responsive layout**: Adapts to different screen sizes

#### Summary Statistics Panel
- **Content**: Min, max, average, and median values for each metric
- **Format**: Clean table with metric names and formatted values
- **Color coding**: Light blue header for visual separation

#### Top Locations Ranking
- **Content**: Top 10 locations by composite score
- **Columns**: Rank, neighborhood, score, travel time, cost, safety grade
- **Sorting**: Ordered by composite score (highest first)
- **Format**: Green-themed table for positive association

### Output Generation Options

#### Dashboard Mode
- **File format**: Single HTML file with embedded interactive elements
- **Layout**: Multi-panel dashboard with map and supporting tables
- **Size**: Optimized for desktop viewing (1200px height)
- **Features**: Full interactivity with layer toggles and tooltips

#### Map-Only Mode
- **File format**: Standalone HTML map without additional panels
- **Use case**: Focus on geographic analysis without statistical summaries
- **Performance**: Lighter weight for better mobile performance

#### Data Export Mode
- **File format**: JSON export of analysis results
- **Content**: Metadata, regional statistics, top 50 locations, grid summary
- **Use case**: Further analysis in external tools or integration with other systems

### Visual Design Principles

#### Color Accessibility
- **Colorblind-friendly**: Use of color schemes that work for different types of color vision
- **High contrast**: Sufficient contrast between data ranges for clear differentiation
- **Intuitive mapping**: Green = good, red = concerning, following common conventions

#### Performance Optimization
- **Data aggregation**: Optimize grid density for smooth rendering
- **Layer management**: Efficient toggling without reloading data
- **Responsive design**: Maintain performance across different devices

### Implementation Reference
See implementation in:
- `src/visualization/plotly_maps.py` - Map layer creation and configuration
- `src/visualization/statistics.py` - Summary tables and regional statistics
- `src/visualization/dashboard.py` - Dashboard layout and output generation
- `config/output.yaml` - Visualization preferences and styling options