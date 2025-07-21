"""
Core Location Analysis Engine
Orchestrates the complete analysis workflow from grid generation to output.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path

from .apis.osrm import OSRMClient
from tqdm import tqdm

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

    def __init__(
        self,
        config: Dict[str, Any],
        cache_only: bool = False,
        force_refresh: bool = False,
    ):
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
        self.analysis_config = config["analysis"]
        self.destinations_config = config["destinations"]
        self.transportation_config = config["transportation"]
        self.weights_config = config["weights"]
        self.output_config = config["output"]

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

        # Validate required inputs
        self._validate_inputs()

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
            regional_statistics=regional_stats,
        )

        self.logger.info(
            f"Analysis completed: {len(analysis_results)} grid points analyzed"
        )
        return results

    def _setup_analysis_grid(self) -> None:
        """Setup analysis grid based on configuration."""
        center_point = self.analysis_config["center_point"]

        # Handle center point configuration
        if isinstance(center_point, str):
            # TODO: Geocode address string to coordinates
            # For now, use a default location (NYC)
            center_lat, center_lon = 40.7128, -74.0060
            self.logger.warning(
                f"Geocoding not implemented, using default coordinates for '{center_point}'"
            )
        else:
            # Assume [lat, lon] coordinates
            center_lat, center_lon = center_point

        # Create grid
        self.grid = AnalysisGrid(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_miles=self.analysis_config["max_radius"],
            grid_size_miles=self.analysis_config["grid_size"],
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
            category = schedule["category"]
            if category not in schedule_summary:
                schedule_summary[category] = 0
            schedule_summary[category] += 1

        total_schedules = len(self.schedules)
        self.logger.info(f"Processed {total_schedules} schedule items")
        for category, count in schedule_summary.items():
            self.logger.debug(f"  {category}: {count} schedules")

    def _validate_inputs(self) -> None:
        """Validate that grid and schedules are available."""
        if self.grid is None or self.grid.get_grid_dataframe().empty:
            raise ValueError("Analysis grid is empty")
        if not self.schedules:
            raise ValueError("No schedules provided")

    def _calculate_routes(self) -> Dict[str, Any]:
        """
        Calculate routes for all grid points using the OSRM service.

        Returns:
            Route calculation results
        """
        osrm_cfg = self.config.get("apis", {}).get("osrm", {})
        client = OSRMClient(
            base_url=osrm_cfg.get("base_url", "http://localhost:5000"),
            timeout=osrm_cfg.get("timeout", 30),
            requests_per_second=osrm_cfg.get("requests_per_second", 10),
            use_cache=osrm_cfg.get("cache", True),
            cache_duration_days=self.output_config.get("cache_duration", 7),
            force_refresh=self.force_refresh,
        )
        batch_size = osrm_cfg.get("batch_size", 50)

        grid_df = self.grid.get_grid_dataframe()
        use_cache = osrm_cfg.get("cache", True)

        route_data = {
            "total_api_calls": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "cache_hits": 0,
            "routes": {},
        }

        origins: List[Dict[str, float]] = []
        destinations: List[Dict[str, float]] = []
        meta: List[tuple] = []

        def flush_batch() -> None:
            if not origins:
                return
            results = client.route_batch(origins, destinations)
            route_data["total_api_calls"] += 1
            for (pid, dest_address, o_lat, o_lon, dep, day), res in zip(meta, results):
                route_data["routes"].setdefault(pid, {})[dest_address] = res
                if res["status"] == "OK":
                    route_data["successful_calculations"] += 1
                else:
                    route_data["failed_calculations"] += 1
                if use_cache:
                    save_cached_route(
                        o_lat,
                        o_lon,
                        dest_address,
                        dep,
                        day,
                        res,
                        cache_duration_days=self.output_config.get("cache_duration", 7),
                    )
            origins.clear()
            destinations.clear()
            meta.clear()

        for row in tqdm(grid_df.itertuples(), total=len(grid_df), desc="Routes"):
            origin = {"lat": row.lat, "lon": row.lon}
            for sched in self.schedules:
                dest_addr = sched["destination"]
                dep = sched.get("departure_time", "")
                day = sched.get("day", sched.get("pattern", ""))
                dest = {
                    "lat": sched.get("lat", origin["lat"]),
                    "lon": sched.get("lon", origin["lon"]),
                }

                cached = None
                if use_cache and not self.force_refresh:
                    cached = get_cached_route(
                        origin["lat"], origin["lon"], dest_addr, dep, day
                    )

                if cached:
                    route_data["cache_hits"] += 1
                    route_data["routes"].setdefault(row.point_id, {})[
                        dest_addr
                    ] = cached
                    continue

                if self.cache_only:
                    route_data["failed_calculations"] += 1
                    continue

                origins.append(origin)
                destinations.append(dest)
                meta.append(
                    (row.point_id, dest_addr, origin["lat"], origin["lon"], dep, day)
                )

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

        if not isinstance(route_data, dict):
            raise ValueError("route_data must be a dict")

        grid_df = self.grid.get_grid_dataframe()
        schedules_df = pd.DataFrame(self.schedules or [])
        safety_params = self.weights_config.get("safety_parameters", {})

        if schedules_df.empty:
            weekly_map = pd.Series(dtype=float)
            monthly_map = pd.Series(dtype=float)
            dest_meta = pd.DataFrame()
        else:
            weekly_map = (
                schedules_df.assign(
                    weight=schedules_df["frequency"].map(
                        {"weekly": 1.0, "monthly": 12 / 52}
                    )
                )
                .groupby("destination")["weight"]
                .sum()
            )
            monthly_map = (
                schedules_df.assign(
                    weight=schedules_df["frequency"].map(
                        {"weekly": 52 / 12, "monthly": 1.0}
                    )
                )
                .groupby("destination")["weight"]
                .sum()
            )
            dest_meta = (
                schedules_df[
                    ["destination", "destination_name", "category", "departure_time"]
                ]
                .drop_duplicates(subset=["destination"])
                .set_index("destination")
            )

        route_records = []
        for pid, dests in route_data.get("routes", {}).items():
            for dest, r in dests.items():
                route_records.append(
                    {
                        "point_id": pid,
                        "destination": dest,
                        "duration_min": r.get("duration_seconds", 0) / 60,
                        "distance_miles": r.get("distance_miles", 0),
                    }
                )

        routes_df = pd.DataFrame(route_records)
        if routes_df.empty:
            df = grid_df.copy()
            df["weekly_minutes"] = 0.0
            df["monthly_minutes"] = 0.0
            df["drive_monthly_miles"] = 0.0
            df["transit_monthly_cost"] = 0.0
        else:
            freq_df = pd.DataFrame(
                {
                    "destination": weekly_map.index,
                    "weekly_trips": weekly_map.values,
                    "monthly_trips": monthly_map.reindex(weekly_map.index)
                    .fillna(0)
                    .values,
                }
            )

            merged = routes_df.merge(freq_df, on="destination", how="left")

            merged["weekly_minutes"] = merged["duration_min"] * merged["weekly_trips"]
            merged["monthly_minutes"] = merged["duration_min"] * merged["monthly_trips"]

            transit_fare = self.transportation_config.get("transit", {}).get(
                "base_fare", 2.75
            )
            merged["drive_monthly_miles"] = (
                merged["distance_miles"] * merged["monthly_trips"]
            )
            merged["transit_monthly_cost"] = merged["monthly_trips"] * transit_fare

            agg = (
                merged.groupby("point_id")
                .agg(
                    weekly_minutes=("weekly_minutes", "sum"),
                    monthly_minutes=("monthly_minutes", "sum"),
                    drive_monthly_miles=("drive_monthly_miles", "sum"),
                    transit_monthly_cost=("transit_monthly_cost", "sum"),
                )
                .reset_index()
            )

            df = grid_df.merge(agg, on="point_id", how="left").fillna(0)

        weights = {
            "violent": safety_params.get("violent_weight", 2.0),
            "property": safety_params.get("property_weight", 1.0),
            "other": safety_params.get("other_weight", 0.5),
        }

        tqdm.pandas(desc="Crime")
        crime_stats = df.progress_apply(
            lambda r: get_crime_data(
                r.lat,
                r.lon,
                weights=weights,
                density_scale=safety_params.get("density_scale", 1000.0),
                score_scale=safety_params.get("score_scale", 10.0),
            ),
            axis=1,
        )

        crime_df = pd.DataFrame(crime_stats.tolist())
        df = pd.concat([df, crime_df], axis=1)

        cost_per_mile = self.transportation_config.get("driving", {}).get(
            "cost_per_mile", 0.65
        )
        weights_cfg = self.weights_config

        travel_score = (1.0 - df["weekly_minutes"] / 3000.0).clip(lower=0.0)
        monthly_cost = (
            df["drive_monthly_miles"] * cost_per_mile + df["transit_monthly_cost"]
        )
        cost_score = (1.0 - monthly_cost / 1000.0).clip(lower=0.0)
        safety_score_comp = (1.0 - df["crime_score"]).clip(lower=0.0)

        overall = (
            travel_score * weights_cfg.get("travel_time", 0.4)
            + cost_score * weights_cfg.get("travel_cost", 0.3)
            + safety_score_comp * weights_cfg.get("safety", 0.3)
        )

        from .apis.crime_data import score_to_grade

        df["overall"] = overall
        df["grade"] = df["overall"].apply(lambda x: score_to_grade(1.0 - x))
        df["rank_percentile"] = df["overall"].rank(pct=True) * 100

        analysis_results = []
        for _, row in df.iterrows():
            point_routes = route_data.get("routes", {}).get(row.point_id, {})
            dest_map: Dict[str, Dict[str, DestinationAnalysis]] = {}
            if not dest_meta.empty:
                for dest_addr, w_trips in weekly_map.items():
                    route = point_routes.get(dest_addr)
                    if not route:
                        continue
                    if dest_addr not in dest_meta.index:
                        continue
                    meta = dest_meta.loc[dest_addr]
                    m_trips = monthly_map.get(dest_addr, 0)
                    avg_minutes = route["duration_seconds"] / 60
                    analysis = DestinationAnalysis(
                        weekly_trips=int(round(w_trips)),
                        monthly_trips=int(round(m_trips)),
                        avg_travel_time=avg_minutes,
                        total_weekly_time=avg_minutes * w_trips,
                        routes=[
                            Route(
                                departure_time=meta["departure_time"],
                                arrival_time=meta["departure_time"],
                                mode="driving",
                                duration=int(avg_minutes),
                                distance=route["distance_miles"],
                            )
                        ],
                    )
                    dest_map.setdefault(meta["category"], {})[
                        meta["destination_name"]
                    ] = analysis

            travel = TravelAnalysis(
                total_weekly_minutes=int(round(row.weekly_minutes)),
                total_monthly_minutes=int(round(row.monthly_minutes)),
                destinations=dest_map,
            )

            cost = CostAnalysis(
                weekly_totals=CostTotals(0.0, 0.0, 0.0, 0.0),
                monthly_totals=CostTotals(
                    row.drive_monthly_miles, 0.0, 0.0, row.transit_monthly_cost
                ),
                breakdown_by_destination={},
            )

            safety = SafetyAnalysis(
                crime_score=row.crime_score,
                nearby_incidents=row.incident_count,
                safety_grade=row.safety_grade,
                violent_crimes=row.violent_crimes,
                property_crimes=row.property_crimes,
                other_crimes=row.other_crimes,
                crime_types={
                    "violent": row.violent_crimes,
                    "property": row.property_crimes,
                    "other": row.other_crimes,
                },
            )

            comp = CompositeScore(
                overall=row.overall,
                components={
                    "travel_time": travel_score.loc[_],
                    "travel_cost": cost_score.loc[_],
                    "safety": safety_score_comp.loc[_],
                },
                grade=row.grade,
                rank_percentile=int(row.rank_percentile),
            )

            analysis_results.append(
                GridPointAnalysis(
                    location=Location(
                        lat=row.lat, lon=row.lon, address=f"{row.lat},{row.lon}"
                    ),
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
        cost_per_mile = self.transportation_config.get("driving", {}).get(
            "cost_per_mile", 0.65
        )
        transit_fare = self.transportation_config.get("transit", {}).get(
            "base_fare", 2.75
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

        return CostAnalysis(
            weekly_totals=weekly,
            monthly_totals=monthly,
            breakdown_by_destination=breakdown,
        )

    def _calculate_composite_score(
        self,
        travel: TravelAnalysis,
        cost: CostAnalysis,
        safety: SafetyAnalysis,
    ) -> CompositeScore:
        """Combine component scores into a single composite score."""
        weights = self.weights_config
        cost_per_mile = self.transportation_config.get("driving", {}).get(
            "cost_per_mile", 0.65
        )

        monthly_cost = (
            cost.monthly_totals.driving_miles * cost_per_mile
            + cost.monthly_totals.transit_cost
        )

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

    def _compute_regional_statistics(
        self, analysis_results: List[Any]
    ) -> RegionalStatistics:
        """
        Compute regional statistics from analysis results.

        Args:
            analysis_results: List of grid point analyses

        Returns:
            Regional statistics summary
        """
        if not analysis_results:
            return RegionalStatistics()

        travel_times = [
            p.travel_analysis.total_weekly_minutes for p in analysis_results
        ]
        crime_scores = [p.safety_analysis.crime_score for p in analysis_results]
        comp_scores = [p.composite_score.overall for p in analysis_results]

        best = sorted(
            analysis_results, key=lambda p: p.composite_score.overall, reverse=True
        )[:5]
        best_locations = [
            {
                "lat": b.location.lat,
                "lon": b.location.lon,
                "score": b.composite_score.overall,
            }
            for b in best
        ]

        return RegionalStatistics(
            travel_time={
                "min": min(travel_times),
                "max": max(travel_times),
                "avg": sum(travel_times) / len(travel_times),
            },
            safety={
                "min": min(crime_scores),
                "max": max(crime_scores),
                "avg": sum(crime_scores) / len(crime_scores),
            },
            composite={
                "min": min(comp_scores),
                "max": max(comp_scores),
                "avg": sum(comp_scores) / len(comp_scores),
            },
            best_locations=best_locations,
        )

    def _create_metadata(self) -> AnalysisMetadata:
        """Create analysis metadata."""
        from datetime import datetime

        grid_info = self.grid.get_grid_info()

        return AnalysisMetadata(
            generated=datetime.now().isoformat(),
            grid_size=self.analysis_config["grid_size"],
            total_points=grid_info["total_points"],
            center_point=grid_info["center_point"],
            bounds=grid_info["bounds"],
        )

    def generate_output(self, results: AnalysisResults, output_path: str) -> None:
        """
        Generate output visualization.

        Args:
            results: Analysis results
            output_path: Path for output file
        """
        output_format = self.output_config.get("output_format", "html")

        if output_format in ("html", "both"):
            self._generate_html_output(results, output_path)

        if output_format in ("json", "both"):
            self._generate_json_output(results, output_path)

    def _generate_html_output(self, results: AnalysisResults, output_path: str) -> None:
        """Generate HTML dashboard output."""
        from dataclasses import asdict
        from .visualization.dashboard import generate_interactive_map

        try:
            html_path = (
                output_path if output_path.endswith(".html") else f"{output_path}.html"
            )
            generate_interactive_map(asdict(results), html_path)
            self.logger.info(f"HTML output generated: {html_path}")

        except Exception as e:
            self.logger.error(f"Error generating HTML output: {e}")
            raise

    def _generate_json_output(self, results: AnalysisResults, output_path: str) -> None:
        """Generate JSON data export."""
        from dataclasses import asdict
        from .visualization.dashboard import create_data_export

        try:
            json_path = (
                output_path.replace(".html", ".json")
                if output_path.endswith(".html")
                else f"{output_path}.json"
            )
            create_data_export(asdict(results), json_path)
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
