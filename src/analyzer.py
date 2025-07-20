"""
Core Location Analysis Engine
Orchestrates the complete analysis workflow from grid generation to output.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

from .apis.osrm import OSRMClient

from .core.grid_generator import AnalysisGrid
from .core.scheduler import (
    process_schedules,
    calculate_weekly_frequency,
    calculate_monthly_frequency,
)
from .models.data_structures import (
    AnalysisResults,
    AnalysisMetadata,
    RegionalStatistics,
    CostTotals,
    CostAnalysis,
    TravelAnalysis,
    SafetyAnalysis,
    CompositeScore,
    DestinationAnalysis,
    Route,
    GridPointAnalysis,
    Location,
)
from .apis.osrm import OSRMClient
from .apis.cache import get_cached_route, save_cached_route


class LocationAnalyzer:
    """
    Main analysis engine that coordinates all components.
    """
    
    def __init__(self, config: Dict[str, Any], cache_only: bool = False, force_refresh: bool = False):
        """
        Initialize analyzer with configuration.
        
        Args:
            config: Complete configuration dictionary
            cache_only: Use only cached data, don't make API calls
            force_refresh: Force refresh of all cached data
        """
        self.config = config
        self.cache_only = cache_only
        self.force_refresh = force_refresh
        self.logger = logging.getLogger(__name__)
        
        # Extract key configuration sections
        self.analysis_config = config['analysis']
        self.destinations_config = config['destinations']
        self.transportation_config = config['transportation']
        self.weights_config = config['weights']
        self.output_config = config['output']
        
        # Initialize components
        self.grid = None
        self.schedules = None
        
    def run_analysis(self) -> AnalysisResults:
        """
        Run complete location analysis.
        
        Returns:
            Complete analysis results
        """
        self.logger.info("Starting location analysis")
        
        # Phase 1: Setup and Grid Generation
        self.logger.info("Phase 1: Generating analysis grid")
        self._setup_analysis_grid()
        
        # Phase 2: Schedule Processing
        self.logger.info("Phase 2: Processing destination schedules")
        self._process_schedules()
        
        # Phase 3: Route Calculations (placeholder for now)
        self.logger.info("Phase 3: Calculating routes")
        route_data = self._calculate_routes()
        
        # Phase 4: Analysis and Scoring (placeholder for now)
        self.logger.info("Phase 4: Analyzing locations and calculating scores")
        analysis_results = self._analyze_locations(route_data)
        
        # Phase 5: Regional Statistics
        self.logger.info("Phase 5: Computing regional statistics")
        regional_stats = self._compute_regional_statistics(analysis_results)
        
        # Create final results
        results = AnalysisResults(
            analysis_metadata=self._create_metadata(),
            grid_points=analysis_results,
            regional_statistics=regional_stats
        )
        
        self.logger.info(f"Analysis completed: {len(analysis_results)} grid points analyzed")
        return results
    
    def _setup_analysis_grid(self) -> None:
        """Setup analysis grid based on configuration."""
        center_point = self.analysis_config['center_point']
        
        # Handle center point configuration
        if isinstance(center_point, str):
            # TODO: Geocode address string to coordinates
            # For now, use a default location (NYC)
            center_lat, center_lon = 40.7128, -74.0060
            self.logger.warning(f"Geocoding not implemented, using default coordinates for '{center_point}'")
        else:
            # Assume [lat, lon] coordinates
            center_lat, center_lon = center_point
        
        # Create grid
        self.grid = AnalysisGrid(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_miles=self.analysis_config['max_radius'],
            grid_size_miles=self.analysis_config['grid_size']
        )
        
        grid_info = self.grid.get_grid_info()
        self.logger.info(f"Generated grid: {grid_info['total_points']:,} points")
        self.logger.debug(f"Grid details: {grid_info}")
    
    def _process_schedules(self) -> None:
        """Process destination schedules into departure times."""
        self.schedules = process_schedules(self.config)
        
        # Log schedule summary
        schedule_summary = {}
        for schedule in self.schedules:
            category = schedule['category']
            if category not in schedule_summary:
                schedule_summary[category] = 0
            schedule_summary[category] += 1
        
        total_schedules = len(self.schedules)
        self.logger.info(f"Processed {total_schedules} schedule items")
        for category, count in schedule_summary.items():
            self.logger.debug(f"  {category}: {count} schedules")
    
    def _calculate_routes(self) -> Dict[str, Any]:
        """
        Calculate routes for all grid points using the OSRM service.

        Returns:
            Route calculation results
        """
        osrm_cfg = self.config.get('apis', {}).get('osrm', {})
        client = OSRMClient(
            base_url=osrm_cfg.get('base_url', 'http://localhost:5000'),
            timeout=osrm_cfg.get('timeout', 30),
            requests_per_second=osrm_cfg.get('requests_per_second', 10),
        )
        batch_size = osrm_cfg.get('batch_size', 50)

        grid_df = self.grid.get_grid_dataframe()
        use_cache = osrm_cfg.get('cache', True)

        route_data = {
            'total_api_calls': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'cache_hits': 0,
            'routes': {}
        }

        origins: List[Dict[str, float]] = []
        destinations: List[Dict[str, float]] = []
        meta: List[tuple] = []

        def flush_batch() -> None:
            if not origins:
                return
            results = client.route_batch(origins, destinations)
            route_data['total_api_calls'] += 1
            for (pid, dest_address, o_lat, o_lon, dep, day), res in zip(meta, results):
                route_data['routes'].setdefault(pid, {})[dest_address] = res
                if res['status'] == 'OK':
                    route_data['successful_calculations'] += 1
                else:
                    route_data['failed_calculations'] += 1
                if use_cache:
                    save_cached_route(o_lat, o_lon, dest_address, dep, day, res,
                                     cache_duration_days=self.output_config.get('cache_duration', 7))
            origins.clear()
            destinations.clear()
            meta.clear()

        for row in grid_df.itertuples():
            origin = {'lat': row.lat, 'lon': row.lon}
            for sched in self.schedules:
                dest_addr = sched['destination']
                dep = sched.get('departure_time', '')
                day = sched.get('day', sched.get('pattern', ''))
                dest = {'lat': sched.get('lat', origin['lat']), 'lon': sched.get('lon', origin['lon'])}

                cached = None
                if use_cache and not self.force_refresh:
                    cached = get_cached_route(origin['lat'], origin['lon'], dest_addr, dep, day)

                if cached:
                    route_data['cache_hits'] += 1
                    route_data['routes'].setdefault(row.point_id, {})[dest_addr] = cached
                    continue

                if self.cache_only:
                    route_data['failed_calculations'] += 1
                    continue

                origins.append(origin)
                destinations.append(dest)
                meta.append((row.point_id, dest_addr, origin['lat'], origin['lon'], dep, day))

                if len(origins) >= batch_size:
                    flush_batch()

        flush_batch()

        return route_data

    def _analyze_locations(self, route_data: Dict[str, Any]) -> List[Any]:
        """
        Analyze locations and calculate scores.
        
        Args:
            route_data: Route calculation results
            
        Returns:
            List of grid point analyses
        """
        from .apis.crime_data import get_crime_data

        analysis_results = []
        grid_df = self.grid.get_grid_dataframe()
        schedules = self.schedules or []
        weekly_freq = calculate_weekly_frequency(schedules)
        monthly_freq = calculate_monthly_frequency(schedules)
        dest_meta = {s['destination']: {'name': s['destination_name'], 'category': s['category'], 'departure': s.get('departure_time', '')} for s in schedules}

        route_map = route_data.get('routes', {}) if isinstance(route_data, dict) else {}

        for _, row in grid_df.iterrows():
            lat = float(row['lat'])
            lon = float(row['lon'])

            crime_stats = get_crime_data(lat, lon)

            safety = SafetyAnalysis(
                crime_score=crime_stats['crime_score'],
                nearby_incidents=crime_stats['incident_count'],
                safety_grade=crime_stats['safety_grade'],
                violent_crimes=crime_stats['violent_crimes'],
                property_crimes=crime_stats['property_crimes'],
                other_crimes=crime_stats['other_crimes'],
                crime_types={
                    'violent': crime_stats['violent_crimes'],
                    'property': crime_stats['property_crimes'],
                    'other': crime_stats['other_crimes'],
                },
            )

            dest_map: Dict[str, Dict[str, DestinationAnalysis]] = {}
            total_weekly = 0.0
            total_monthly = 0.0

            point_routes = route_map.get(row.point_id, {})
            for dest_addr, freq in weekly_freq.items():
                route = point_routes.get(dest_addr)
                if not route:
                    continue
                meta = dest_meta[dest_addr]
                w_trips = freq
                m_trips = monthly_freq.get(dest_addr, 0)
                avg_minutes = route['duration_seconds'] / 60
                weekly_time = avg_minutes * w_trips
                total_weekly += weekly_time
                total_monthly += avg_minutes * m_trips

                analysis = DestinationAnalysis(
                    weekly_trips=int(round(w_trips)),
                    monthly_trips=int(round(m_trips)),
                    avg_travel_time=avg_minutes,
                    total_weekly_time=weekly_time,
                    routes=[Route(
                        departure_time=meta['departure'],
                        arrival_time=meta['departure'],
                        mode='driving',
                        duration=int(avg_minutes),
                        distance=route['distance_miles'],
                    )],
                )
                dest_map.setdefault(meta['category'], {})[meta['name']] = analysis

            travel = TravelAnalysis(
                total_weekly_minutes=int(round(total_weekly)),
                total_monthly_minutes=int(round(total_monthly)),
                destinations=dest_map,
            )

            cost = self._calculate_costs(
                point_routes, weekly_freq, monthly_freq
            )

            comp = self._calculate_composite_score(
                travel, cost, safety
            )

            analysis_results.append(
                GridPointAnalysis(
                    location=Location(lat=lat, lon=lon, address=f"{lat},{lon}"),
                    travel_analysis=travel,
                    cost_analysis=cost,
                    safety_analysis=safety,
                    composite_score=comp,
                )
            )

        return analysis_results

    def _calculate_costs(
        self,
        point_routes: Dict[str, Any],
        weekly_freq: Dict[str, int],
        monthly_freq: Dict[str, int],
    ) -> CostAnalysis:
        """Calculate transportation cost analysis for a grid point."""
        cost_per_mile = (
            self.transportation_config.get("driving", {}).get("cost_per_mile", 0.65)
        )
        transit_fare = (
            self.transportation_config.get("transit", {}).get("base_fare", 2.75)
        )
        modes = self.transportation_config.get("modes", ["driving"])

        weekly = CostTotals(0.0, 0.0, 0.0, 0.0)
        monthly = CostTotals(0.0, 0.0, 0.0, 0.0)
        breakdown: Dict[str, CostTotals] = {}

        for dest, w_trips in weekly_freq.items():
            route = point_routes.get(dest)
            if not route:
                continue
            m_trips = monthly_freq.get(dest, 0)
            dist = route.get("distance_miles", 0.0)

            drive_w = dist * w_trips if "driving" in modes else 0.0
            drive_m = dist * m_trips if "driving" in modes else 0.0
            trans_w = transit_fare * w_trips if "transit" in modes else 0.0
            trans_m = transit_fare * m_trips if "transit" in modes else 0.0

            weekly.driving_miles += drive_w
            weekly.transit_cost += trans_w
            monthly.driving_miles += drive_m
            monthly.transit_cost += trans_m

            breakdown[dest] = CostTotals(drive_m, 0.0, 0.0, trans_m)

        return CostAnalysis(weekly_totals=weekly, monthly_totals=monthly, breakdown_by_destination=breakdown)

    def _calculate_composite_score(
        self,
        travel: TravelAnalysis,
        cost: CostAnalysis,
        safety: SafetyAnalysis,
    ) -> CompositeScore:
        """Combine component scores into a single composite score."""
        weights = self.weights_config
        cost_per_mile = (
            self.transportation_config.get("driving", {}).get("cost_per_mile", 0.65)
        )

        monthly_cost = cost.monthly_totals.driving_miles * cost_per_mile + cost.monthly_totals.transit_cost

        travel_score = max(0.0, 1.0 - travel.total_weekly_minutes / 3000.0)
        cost_score = max(0.0, 1.0 - monthly_cost / 1000.0)
        safety_score = max(0.0, 1.0 - safety.crime_score)

        overall = (
            travel_score * weights.get("travel_time", 0.4)
            + cost_score * weights.get("travel_cost", 0.3)
            + safety_score * weights.get("safety", 0.3)
        )

        from .apis.crime_data import score_to_grade

        grade = score_to_grade(1.0 - overall)

        return CompositeScore(
            overall=overall,
            components={
                "travel_time": travel_score,
                "travel_cost": cost_score,
                "safety": safety_score,
            },
            grade=grade,
            rank_percentile=0,
        )
    
    def _compute_regional_statistics(self, analysis_results: List[Any]) -> RegionalStatistics:
        """
        Compute regional statistics from analysis results.
        
        Args:
            analysis_results: List of grid point analyses
            
        Returns:
            Regional statistics summary
        """
        if not analysis_results:
            return RegionalStatistics()

        travel_times = [p.travel_analysis.total_weekly_minutes for p in analysis_results]
        crime_scores = [p.safety_analysis.crime_score for p in analysis_results]
        comp_scores = [p.composite_score.overall for p in analysis_results]

        best = sorted(analysis_results, key=lambda p: p.composite_score.overall, reverse=True)[:5]
        best_locations = [
            {
                'lat': b.location.lat,
                'lon': b.location.lon,
                'score': b.composite_score.overall,
            }
            for b in best
        ]

        return RegionalStatistics(
            travel_time={
                'min': min(travel_times),
                'max': max(travel_times),
                'avg': sum(travel_times) / len(travel_times),
            },
            safety={
                'min': min(crime_scores),
                'max': max(crime_scores),
                'avg': sum(crime_scores) / len(crime_scores),
            },
            composite={
                'min': min(comp_scores),
                'max': max(comp_scores),
                'avg': sum(comp_scores) / len(comp_scores),
            },
            best_locations=best_locations,
        )
    
    def _create_metadata(self) -> AnalysisMetadata:
        """Create analysis metadata."""
        from datetime import datetime
        
        grid_info = self.grid.get_grid_info()
        
        return AnalysisMetadata(
            generated=datetime.now().isoformat(),
            grid_size=self.analysis_config['grid_size'],
            total_points=grid_info['total_points'],
            center_point=grid_info['center_point'],
            bounds=grid_info['bounds']
        )
    
    def generate_output(self, results: AnalysisResults, output_path: str) -> None:
        """
        Generate output visualization.
        
        Args:
            results: Analysis results
            output_path: Path for output file
        """
        output_format = self.output_config.get('output_format', 'html')
        
        if output_format in ('html', 'both'):
            self._generate_html_output(results, output_path)
        
        if output_format in ('json', 'both'):
            self._generate_json_output(results, output_path)
    
    def _generate_html_output(self, results: AnalysisResults, output_path: str) -> None:
        """Generate HTML dashboard output."""
        try:
            # TODO: Implement dashboard generation
            # generate_dashboard(results, self.config, output_path)
            
            # For now, create a simple HTML file
            html_content = self._create_placeholder_html(results)
            
            html_path = output_path if output_path.endswith('.html') else f"{output_path}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML output generated: {html_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating HTML output: {e}")
            raise
    
    def _generate_json_output(self, results: AnalysisResults, output_path: str) -> None:
        """Generate JSON data export."""
        import json
        
        try:
            # TODO: Implement proper JSON serialization of results
            json_data = {
                'metadata': {
                    'generated': results.analysis_metadata.generated,
                    'grid_size': results.analysis_metadata.grid_size,
                    'total_points': results.analysis_metadata.total_points,
                    'center_point': results.analysis_metadata.center_point,
                    'bounds': results.analysis_metadata.bounds
                },
                'grid_points': [],  # TODO: Serialize grid point data
                'regional_statistics': {}  # TODO: Serialize regional stats
            }
            
            json_path = output_path.replace('.html', '.json') if output_path.endswith('.html') else f"{output_path}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            
            self.logger.info(f"JSON output generated: {json_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating JSON output: {e}")
            raise
    
    def _create_placeholder_html(self, results: AnalysisResults) -> str:
        """Create placeholder HTML output for testing."""
        metadata = results.analysis_metadata
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Location Evaluator - Analysis Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f8ff; padding: 20px; border-radius: 8px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ margin: 10px 0; }}
        .placeholder {{ color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Location Evaluator - Analysis Results</h1>
        <p>Generated: {metadata.generated}</p>
    </div>
    
    <div class="section">
        <h2>Analysis Configuration</h2>
        <div class="metric">Grid Size: {metadata.grid_size} miles</div>
        <div class="metric">Total Grid Points: {metadata.total_points:,}</div>
        <div class="metric">Center Point: {metadata.center_point['lat']:.4f}, {metadata.center_point['lon']:.4f}</div>
        <div class="metric">Analysis Bounds:</div>
        <ul>
            <li>North: {metadata.bounds['north']:.4f}</li>
            <li>South: {metadata.bounds['south']:.4f}</li>
            <li>East: {metadata.bounds['east']:.4f}</li>
            <li>West: {metadata.bounds['west']:.4f}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Analysis Results</h2>
        <p class="placeholder">Interactive map and analysis results will be displayed here once route calculations and scoring are implemented.</p>
        <p class="placeholder">This placeholder shows that the core infrastructure is working correctly.</p>
    </div>
    
    <div class="section">
        <h2>Implementation Status</h2>
        <ul>
            <li>✅ Configuration parsing and validation</li>
            <li>✅ Grid generation</li>
            <li>✅ Schedule processing</li>
            <li>⏳ Route calculations (OSRM integration)</li>
            <li>⏳ Travel time and cost analysis</li>
            <li>⏳ Safety scoring (FBI crime data)</li>
            <li>⏳ Interactive visualization</li>
        </ul>
    </div>
</body>
</html>"""