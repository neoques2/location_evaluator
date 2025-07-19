"""
Grid Analysis Module for Location Evaluation
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.apis.google_maps import GoogleMapsClient, Destination
from src.core.grid_generator import AnalysisGrid
from src.analysis.constants import (
    AnalysisConfig, 
    TargetLocation, 
    ScheduleRequirement,
    AnalysisConstants
)


@dataclass
class GridAnalysisResult:
    """Result of grid analysis with travel time calculations."""
    grid_df: pd.DataFrame
    successful_targets: List[Dict[str, Any]]
    total_routes: int
    analysis_config: AnalysisConfig
    
    def get_best_location(self) -> pd.Series:
        """Get the location with lowest total weekly travel time."""
        return self.grid_df.loc[self.grid_df["total_weekly_travel_time"].idxmin()]
    
    def get_worst_location(self) -> pd.Series:
        """Get the location with highest total weekly travel time."""
        return self.grid_df.loc[self.grid_df["total_weekly_travel_time"].idxmax()]
    
    def get_summary_stats(self) -> Dict[str, float]:
        """Get summary statistics for the analysis."""
        return {
            "mean_travel_time": self.grid_df["total_weekly_travel_time"].mean(),
            "std_travel_time": self.grid_df["total_weekly_travel_time"].std(),
            "min_travel_time": self.grid_df["total_weekly_travel_time"].min(),
            "max_travel_time": self.grid_df["total_weekly_travel_time"].max(),
            "grid_points": len(self.grid_df),
            "target_count": len(self.successful_targets)
        }


class GridAnalyzer:
    """Handles grid generation and travel time analysis."""
    
    def __init__(self, api_key: str, rate_limit: int = 5):
        self.client = GoogleMapsClient(api_key, rate_limit=rate_limit)
    
    def create_analysis_grid(self, config: AnalysisConfig) -> AnalysisGrid:
        """Create analysis grid from configuration."""
        print(f"{AnalysisConstants.INFO_EMOJI} Creating analysis grid...")
        print(f"   Grid center: ({config.center_lat:.4f}, {config.center_lon:.4f})")
        print(f"   Coverage: {config.coverage_description}")
        
        grid = AnalysisGrid(
            center_lat=config.center_lat,
            center_lon=config.center_lon,
            radius_miles=config.radius_miles,
            grid_size_miles=config.grid_size_miles,
        )
        
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Generated {len(grid.grid_df)} grid points")
        return grid
    
    def geocode_targets(self, target_locations: List[TargetLocation]) -> List[Dict[str, Any]]:
        """Geocode target locations and return successful ones."""
        print(f"{AnalysisConstants.MAP_EMOJI} Geocoding target locations...")
        
        # Convert to Destination objects
        destinations = [
            Destination(target.address, target.name) 
            for target in target_locations
        ]
        
        geocoded_targets = self.client.geocode_batch(destinations)
        successful_targets = [
            t for t in geocoded_targets if not t.get("geocoding_failed", False)
        ]
        
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Successfully geocoded {len(successful_targets)}/{len(target_locations)} targets")
        
        # Print target summary
        print(f"{AnalysisConstants.INFO_EMOJI} Target Locations Summary:")
        print("=" * 60)
        for i, target in enumerate(successful_targets, 1):
            print(f"   {i}. {target['name']}")
            print(f"      Coordinates: ({target['lat']:.4f}, {target['lon']:.4f})")
            print(f"      Address: {target.get('formatted_address', target.get('address', 'N/A'))}")
            print()
        
        return successful_targets
    
    def calculate_travel_times(
        self, 
        grid: AnalysisGrid, 
        successful_targets: List[Dict[str, Any]], 
        departure_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate travel times from grid points to targets."""
        print(f"{AnalysisConstants.CAR_EMOJI} Calculating travel times...")
        
        if departure_time is None:
            departure_time = datetime.now().replace(hour=19, minute=30, second=0) + timedelta(days=1)
        
        test_grid = grid.grid_df.copy()
        
        print(f"   Analyzing {len(test_grid)} grid points × {len(successful_targets)} targets")
        
        result = self.client.batch_distance_calculations(
            grid_df=test_grid,
            destinations=successful_targets,
            mode="driving",
            departure_time=departure_time,
        )
        
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Calculated {result['total_routes']} travel routes")
        return result
    
    def process_schedule_weighted_analysis(
        self, 
        grid: AnalysisGrid, 
        successful_targets: List[Dict[str, Any]], 
        target_locations: List[TargetLocation],
        result: Dict[str, Any]
    ) -> pd.DataFrame:
        """Process travel time data with schedule weighting."""
        print(f"{AnalysisConstants.ANALYSIS_EMOJI} Processing travel times with schedule weighting...")
        
        # Create target name to location mapping
        target_to_location = {loc.name: loc for loc in target_locations}
        
        test_grid = grid.grid_df.copy()
        grid_point_data = []
        
        for i, (_, grid_point) in enumerate(test_grid.iterrows()):
            point_id = grid_point["point_id"]
            lat, lon = grid_point["lat"], grid_point["lon"]
            
            # Find routes for this grid point
            point_routes = {}
            for batch in result["batches"]:
                for route in batch["routes"]:
                    if (
                        abs(route["origin"]["lat"] - lat) < 0.0001
                        and abs(route["origin"]["lon"] - lon) < 0.0001
                    ):
                        dest_name = route["destination"].get("name", "Unknown")
                        if route["status"] in ["OK", "ESTIMATED"]:
                            point_routes[dest_name] = {
                                "duration_minutes": route.get("duration_seconds", 0) / 60,
                                "distance_miles": route.get("distance_miles", 0),
                                "status": route["status"],
                            }
            
            # Calculate weighted score based on schedule frequency
            total_weekly_travel_time = 0
            route_details = []
            
            for target in successful_targets:
                target_name = target["name"]
                if target_name in point_routes and target_name in target_to_location:
                    travel_time = point_routes[target_name]["duration_minutes"]
                    distance = point_routes[target_name]["distance_miles"]
                    
                    # Get frequency from target location
                    target_loc = target_to_location[target_name]
                    weekly_frequency = target_loc.get_total_weekly_frequency()
                    weekly_time = travel_time * weekly_frequency
                    
                    total_weekly_travel_time += weekly_time
                    route_details.append({
                        "destination": target_name,
                        "travel_time": travel_time,
                        "weekly_time": weekly_time,
                        "distance": distance,
                        "frequency": target_loc.get_schedule_summary(),
                        "status": point_routes[target_name]["status"],
                    })
            
            grid_point_data.append({
                "point_id": point_id,
                "lat": lat,
                "lon": lon,
                "total_weekly_travel_time": total_weekly_travel_time,
                "avg_trip_time": total_weekly_travel_time / max(len(route_details), 1),
                "route_details": route_details,
                "successful_routes": len(route_details),
            })
        
        grid_df = pd.DataFrame(grid_point_data)
        
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Processed travel times for {len(grid_df)} grid points")
        stats = {
            "mean": grid_df["total_weekly_travel_time"].mean(),
            "min": grid_df["total_weekly_travel_time"].min(),
            "max": grid_df["total_weekly_travel_time"].max()
        }
        print(f"   Average weekly travel time: {stats['mean']:.1f} minutes")
        print(f"   Best location weekly time: {stats['min']:.1f} minutes")
        print(f"   Worst location weekly time: {stats['max']:.1f} minutes")
        
        return grid_df
    
    def run_full_analysis(
        self, 
        config: AnalysisConfig, 
        target_locations: List[TargetLocation]
    ) -> GridAnalysisResult:
        """Run complete grid analysis from configuration."""
        print(f"{AnalysisConstants.ANALYSIS_EMOJI} Starting {config.analysis_name}")
        print("=" * 70)
        
        # Step 1: Create grid
        grid = self.create_analysis_grid(config)
        
        # Step 2: Geocode targets
        successful_targets = self.geocode_targets(target_locations)
        if not successful_targets:
            raise ValueError("No successful geocoding, cannot proceed")
        
        # Step 3: Calculate travel times
        result = self.calculate_travel_times(grid, successful_targets)
        
        # Step 4: Process with schedule weighting
        grid_df = self.process_schedule_weighted_analysis(
            grid, successful_targets, target_locations, result
        )
        
        return GridAnalysisResult(
            grid_df=grid_df,
            successful_targets=successful_targets,
            total_routes=result["total_routes"],
            analysis_config=config
        )