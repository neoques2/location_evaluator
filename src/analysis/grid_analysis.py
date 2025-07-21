"""
Grid Analysis Module for Location Evaluation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.core.grid_generator import AnalysisGrid
from src.analysis.constants import (
    AnalysisConfig,
    TargetLocation,
    ScheduleRequirement,
    AnalysisConstants,
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
            "target_count": len(self.successful_targets),
        }
