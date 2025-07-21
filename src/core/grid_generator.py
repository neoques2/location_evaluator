"""
Grid Generation for Location Analysis
Creates regular grids of analysis points using numpy for efficiency.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class GridConfig:
    """Configuration for grid generation."""

    center_lat: float
    center_lon: float
    radius_miles: float
    grid_size_miles: float


class AnalysisGrid:
    """
    Generates and manages analysis grid points using numpy.
    """

    def __init__(
        self,
        center_lat: float,
        center_lon: float,
        radius_miles: float,
        grid_size_miles: float,
    ):
        """
        Initialize grid generator.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_miles: Radius of analysis area in miles
            grid_size_miles: Distance between grid points in miles
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_miles = radius_miles
        self.grid_size_miles = grid_size_miles

        # Generate grid as DataFrame
        self.grid_df = self._generate_grid()

    def _generate_grid(self) -> pd.DataFrame:
        """
        Generate evenly spaced lat/lon points within circular radius using numpy.

        Returns:
            DataFrame with columns: lat, lon, distance_from_center
        """
        # Convert miles to degrees (approximate)
        lat_per_mile = 1.0 / 69.0
        lon_per_mile = 1.0 / (69.0 * np.cos(np.radians(self.center_lat)))

        # Grid spacing in degrees
        lat_spacing = self.grid_size_miles * lat_per_mile
        lon_spacing = self.grid_size_miles * lon_per_mile

        # Create bounding square for efficiency
        radius_lat = self.radius_miles * lat_per_mile
        radius_lon = self.radius_miles * lon_per_mile

        # Generate lat/lon arrays
        lat_range = np.arange(
            self.center_lat - radius_lat,
            self.center_lat + radius_lat + lat_spacing,
            lat_spacing,
        )

        lon_range = np.arange(
            self.center_lon - radius_lon,
            self.center_lon + radius_lon + lon_spacing,
            lon_spacing,
        )

        # Create meshgrid
        lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

        # Flatten to get all combinations
        lats = lat_grid.flatten()
        lons = lon_grid.flatten()

        # Calculate distances from center using Haversine formula (vectorized)
        distances = self._haversine_vectorized(
            lats, lons, self.center_lat, self.center_lon
        )

        # Filter points within radius
        within_radius = distances <= self.radius_miles

        # Create DataFrame
        grid_df = pd.DataFrame(
            {
                "lat": lats[within_radius],
                "lon": lons[within_radius],
                "distance_from_center": distances[within_radius],
            }
        )

        # Add point IDs
        grid_df["point_id"] = range(len(grid_df))

        # Round coordinates for cleaner display
        grid_df["lat"] = grid_df["lat"].round(6)
        grid_df["lon"] = grid_df["lon"].round(6)
        grid_df["distance_from_center"] = grid_df["distance_from_center"].round(2)

        return grid_df

    def _haversine_vectorized(
        self, lat1: np.ndarray, lon1: np.ndarray, lat2: float, lon2: float
    ) -> np.ndarray:
        """
        Vectorized Haversine distance calculation.

        Args:
            lat1, lon1: Arrays of coordinates
            lat2, lon2: Single reference point

        Returns:
            Array of distances in miles
        """
        # Convert to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        )
        c = 2 * np.arcsin(np.sqrt(a))

        # Earth's radius in miles
        earth_radius_miles = 3959

        return earth_radius_miles * c

    @property
    def grid_points(self):
        """Legacy property for backward compatibility."""
        return list(zip(self.grid_df["lat"], self.grid_df["lon"]))

    def get_grid_bounds(self) -> Dict[str, float]:
        """
        Get bounding box of the grid.

        Returns:
            Dictionary with north, south, east, west bounds
        """
        if len(self.grid_df) == 0:
            return {"north": 0, "south": 0, "east": 0, "west": 0}

        return {
            "north": float(self.grid_df["lat"].max()),
            "south": float(self.grid_df["lat"].min()),
            "east": float(self.grid_df["lon"].max()),
            "west": float(self.grid_df["lon"].min()),
        }

    def get_grid_info(self) -> Dict[str, Any]:
        """
        Get information about the generated grid.

        Returns:
            Dictionary with grid statistics
        """
        bounds = self.get_grid_bounds()

        return {
            "total_points": len(self.grid_df),
            "grid_size_miles": self.grid_size_miles,
            "radius_miles": self.radius_miles,
            "center_point": {"lat": self.center_lat, "lon": self.center_lon},
            "bounds": bounds,
            "coverage_area_sq_miles": np.pi * (self.radius_miles**2),
            "actual_coverage_sq_miles": self._calculate_actual_coverage(),
        }

    def _calculate_actual_coverage(self) -> float:
        """
        Calculate actual coverage area based on grid density.

        Returns:
            Actual coverage area in square miles
        """
        if len(self.grid_df) == 0:
            return 0.0

        # Each grid point represents approximately grid_size^2 area
        return len(self.grid_df) * (self.grid_size_miles**2)

    def get_nearest_grid_point(
        self, target_lat: float, target_lon: float
    ) -> Tuple[float, float]:
        """
        Find the nearest grid point to a target location.

        Args:
            target_lat: Target latitude
            target_lon: Target longitude

        Returns:
            Nearest grid point as (lat, lon) tuple
        """
        if len(self.grid_df) == 0:
            return (0.0, 0.0)

        # Calculate distances to all points
        distances = self._haversine_vectorized(
            self.grid_df["lat"].values,
            self.grid_df["lon"].values,
            target_lat,
            target_lon,
        )

        # Find nearest
        nearest_idx = np.argmin(distances)
        row = self.grid_df.iloc[nearest_idx]

        return (float(row["lat"]), float(row["lon"]))

    def get_grid_dataframe(self) -> pd.DataFrame:
        """
        Get the grid as a pandas DataFrame.

        Returns:
            DataFrame with grid points and metadata
        """
        return self.grid_df.copy()

    def add_column(self, name: str, values: np.ndarray) -> None:
        """
        Add a column to the grid DataFrame.

        Args:
            name: Column name
            values: Array of values (must match grid length)
        """
        if len(values) != len(self.grid_df):
            raise ValueError(
                f"Values length {len(values)} doesn't match grid length {len(self.grid_df)}"
            )

        self.grid_df[name] = values
