"""
Constants and Enums for Location Analysis
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class ScheduleFrequency(Enum):
    """Schedule frequency options."""

    WEEKLY = "weekly"
    ONCE_WEEKLY = "1x_weekly"
    TWICE_WEEKLY = "2x_weekly"
    THRICE_WEEKLY = "3x_weekly"


class DayOfWeek(Enum):
    """Days of the week."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"
    WEEKDAY = "Weekday"
    WEEKEND = "Weekend"


class AnalysisConstants:
    """Constants for location analysis."""

    # Grid Parameters
    DEFAULT_GRID_SIZE_MILES = 1.0
    DEFAULT_RADIUS_MILES = 25.0

    # File Paths
    OUTPUT_DIR = "outputs"
    MAIN_MAP_FILE = "dallas_travel_map.html"
    SUPPORTING_PLOTS_FILE = "dallas_supporting_plots.html"
    COMBINED_FILE = "dallas_travel_analysis.html"

    # Visualization
    MAP_HEIGHT = 800
    MAP_WIDTH = 1400
    SUPPORTING_PLOTS_HEIGHT = 500
    DEFAULT_ZOOM = 9

    # Colors
    COLORSCALE = "RdYlGn_r"
    TARGET_COLOR = "red"
    GRID_OPACITY = 0.8
    CONTOUR_OPACITY = 0.3

    # Time Format
    TIME_FORMAT = "%H:%M"

    # Console Messages
    SUCCESS_EMOJI = "✅"
    ERROR_EMOJI = "❌"
    INFO_EMOJI = "📍"
    TARGET_EMOJI = "🎯"
    ANALYSIS_EMOJI = "📊"
    MAP_EMOJI = "🗺️"
    TIME_EMOJI = "⏰"
    CAR_EMOJI = "🚗"
    ART_EMOJI = "🎨"


@dataclass
class ScheduleRequirement:
    """Represents a schedule requirement for a target location."""

    def __init__(self):
        pass

    location: str
    day: DayOfWeek
    time: str
    end_time: str
    frequency: ScheduleFrequency
    description: str

    def get_frequency_multiplier(self) -> int:
        """Get the weekly frequency multiplier."""
        multipliers = {
            ScheduleFrequency.WEEKLY: 1,
            ScheduleFrequency.ONCE_WEEKLY: 1,
            ScheduleFrequency.TWICE_WEEKLY: 2,
            ScheduleFrequency.THRICE_WEEKLY: 3,
        }
        return multipliers.get(self.frequency, 1)

    def get_schedule_summary(self) -> str:
        """Get a human-readable schedule summary."""
        freq_map = {
            ScheduleFrequency.WEEKLY: "1x/week",
            ScheduleFrequency.ONCE_WEEKLY: "1x/week",
            ScheduleFrequency.TWICE_WEEKLY: "2x/week",
            ScheduleFrequency.THRICE_WEEKLY: "3x/week",
        }

        if self.day == DayOfWeek.SATURDAY:
            return f"Sat {self.time}-{self.end_time}"
        elif self.day == DayOfWeek.WEDNESDAY:
            return f"Wed {self.time}-{self.end_time}"
        elif self.day == DayOfWeek.SUNDAY:
            return f"Sun {self.time}"
        else:
            return (
                f"{freq_map.get(self.frequency, '1x/week')} {self.time}-{self.end_time}"
            )


@dataclass
class TargetLocation:
    """Represents a target location with schedule requirements."""

    name: str
    address: str
    schedule_requirements: list[ScheduleRequirement]

    def get_total_weekly_frequency(self) -> int:
        """Get total weekly frequency for this location."""
        return sum(req.get_frequency_multiplier() for req in self.schedule_requirements)

    def get_schedule_summary(self) -> str:
        """Get combined schedule summary."""
        if len(self.schedule_requirements) == 1:
            return self.schedule_requirements[0].get_schedule_summary()

        # Handle multiple requirements (like Design District)
        total_freq = self.get_total_weekly_frequency()
        return f"{total_freq}x/week"


@dataclass
class AnalysisConfig:
    """Configuration for location analysis."""

    center_lat: float
    center_lon: float
    radius_miles: float = AnalysisConstants.DEFAULT_RADIUS_MILES
    grid_size_miles: float = AnalysisConstants.DEFAULT_GRID_SIZE_MILES
    analysis_name: str = "Location Analysis"
    coverage_description: str = "Metro Area Coverage"
