"""
Dallas Target Definitions and Configuration
"""

from typing import List, Dict

from src.analysis.constants import (
    AnalysisConfig,
    TargetLocation,
    ScheduleRequirement,
    ScheduleFrequency,
    DayOfWeek,
    AnalysisConstants,
)


class DallasTargetDefinitions:
    """Predefined target locations and schedules for Dallas analysis."""

    # Dallas center coordinates
    DALLAS_CENTER_LAT = 32.7767
    DALLAS_CENTER_LON = -96.7970

    # Target addresses
    SAMMONS_CENTER_ADDRESS = "Sammons Center for the Arts, Dallas, TX"
    SONS_HERMANN_ADDRESS = "Sons of Hermann Hall, Dallas, TX"
    MOVEMENT_PLANO_ADDRESS = "525 Talbert Dr, Plano, TX 75093"
    HILL_CLIMBING_ADDRESS = "The Hill Climbing Gym, Dallas, TX"
    MOVEMENT_DESIGN_ADDRESS = "Movement Climbing Gym Design District, Dallas, TX"

    # Schedule times
    EVENING_START = "19:30"  # 7:30 PM
    EVENING_END = "22:00"  # 10:00 PM
    LATE_START = "21:00"  # 9:00 PM
    LATE_END = "23:30"  # 11:30 PM
    NOON_START = "12:00"  # 12:00 PM
    NOON_END = "14:00"  # 2:00 PM (estimated)

    @classmethod
    def get_dallas_config(cls) -> AnalysisConfig:
        """Get Dallas analysis configuration."""
        return AnalysisConfig(
            center_lat=cls.DALLAS_CENTER_LAT,
            center_lon=cls.DALLAS_CENTER_LON,
            radius_miles=25.0,
            grid_size_miles=1.0,
            analysis_name="Dallas Metro Travel Time Analysis",
            coverage_description="Dallas metro area",
        )

    @classmethod
    def get_sammons_center_schedule(cls) -> List[ScheduleRequirement]:
        """Get Sammons Center schedule requirements."""
        return [
            ScheduleRequirement(
                location="Sammons Center for the Arts",
                day=DayOfWeek.SATURDAY,
                time=cls.LATE_START,
                end_time=cls.LATE_END,
                frequency=ScheduleFrequency.WEEKLY,
                description="Saturday night arts events",
            )
        ]

    @classmethod
    def get_sons_hermann_schedule(cls) -> List[ScheduleRequirement]:
        """Get Sons of Hermann Hall schedule requirements."""
        return [
            ScheduleRequirement(
                location="Sons of Hermann Hall",
                day=DayOfWeek.WEDNESDAY,
                time=cls.LATE_START,
                end_time=cls.LATE_END,
                frequency=ScheduleFrequency.WEEKLY,
                description="Wednesday night events",
            )
        ]

    @classmethod
    def get_movement_plano_schedule(cls) -> List[ScheduleRequirement]:
        """Get Movement Plano schedule requirements."""
        return [
            ScheduleRequirement(
                location="Movement Plano",
                day=DayOfWeek.WEEKDAY,
                time=cls.EVENING_START,
                end_time=cls.EVENING_END,
                frequency=ScheduleFrequency.ONCE_WEEKLY,
                description="Climbing session (1x per week)",
            )
        ]

    @classmethod
    def get_hill_climbing_schedule(cls) -> List[ScheduleRequirement]:
        """Get The Hill Climbing schedule requirements."""
        return [
            ScheduleRequirement(
                location="The Hill Climbing",
                day=DayOfWeek.WEEKDAY,
                time=cls.EVENING_START,
                end_time=cls.EVENING_END,
                frequency=ScheduleFrequency.ONCE_WEEKLY,
                description="Climbing session (1x per week)",
            )
        ]

    @classmethod
    def get_movement_design_schedule(cls) -> List[ScheduleRequirement]:
        """Get Movement Design District schedule requirements."""
        return [
            ScheduleRequirement(
                location="Movement Design District",
                day=DayOfWeek.WEEKEND,
                time=cls.EVENING_START,
                end_time=cls.EVENING_END,
                frequency=ScheduleFrequency.TWICE_WEEKLY,
                description="Climbing sessions (2x per week - weekend)",
            ),
            ScheduleRequirement(
                location="Movement Design District",
                day=DayOfWeek.SUNDAY,
                time=cls.NOON_START,
                end_time=cls.NOON_END,
                frequency=ScheduleFrequency.WEEKLY,
                description="Sunday noon session",
            ),
        ]

    @classmethod
    def get_dallas_target_locations(cls) -> List[TargetLocation]:
        """Get all Dallas target locations with complete schedules."""
        return [
            TargetLocation(
                name="Sammons Center for the Arts",
                address=cls.SAMMONS_CENTER_ADDRESS,
                schedule_requirements=cls.get_sammons_center_schedule(),
            ),
            TargetLocation(
                name="Sons of Hermann Hall",
                address=cls.SONS_HERMANN_ADDRESS,
                schedule_requirements=cls.get_sons_hermann_schedule(),
            ),
            TargetLocation(
                name="Movement Plano",
                address=cls.MOVEMENT_PLANO_ADDRESS,
                schedule_requirements=cls.get_movement_plano_schedule(),
            ),
            TargetLocation(
                name="The Hill Climbing",
                address=cls.HILL_CLIMBING_ADDRESS,
                schedule_requirements=cls.get_hill_climbing_schedule(),
            ),
            TargetLocation(
                name="Movement Design District",
                address=cls.MOVEMENT_DESIGN_ADDRESS,
                schedule_requirements=cls.get_movement_design_schedule(),
            ),
        ]

    @classmethod
    def get_schedule_info_dict(cls) -> Dict[str, str]:
        """Get schedule information as dictionary for HTML generation."""
        return {
            "Sammons Center for the Arts": "Saturday 9:00-11:30 PM",
            "Sons of Hermann Hall": "Wednesday 9:00-11:30 PM",
            "Movement Plano": "1x/week, 7:30-10:00 PM",
            "The Hill Climbing": "1x/week, 7:30-10:00 PM",
            "Movement Design District": "3x/week (2x weekend + Sunday noon)",
        }

    @classmethod
    def print_schedule_summary(cls) -> None:
        """Print schedule summary to console."""
        print(f"{AnalysisConstants.TIME_EMOJI} Dallas Weekly Schedule Summary:")
        print("=" * 40)

        target_locations = cls.get_dallas_target_locations()
        for target in target_locations:
            print(f"   • {target.name}")
            for req in target.schedule_requirements:
                print(
                    f"     {req.day.value} {req.time}-{req.end_time} ({req.frequency.value})"
                )
                print(f"     {req.description}")
            print()


class DallasAnalysisRunner:
    """Convenience class for running Dallas analysis with predefined targets."""

    @classmethod
    def get_complete_dallas_setup(cls) -> tuple:
        """Get complete Dallas analysis setup (config, targets, schedule_info)."""
        config = DallasTargetDefinitions.get_dallas_config()
        targets = DallasTargetDefinitions.get_dallas_target_locations()
        schedule_info = DallasTargetDefinitions.get_schedule_info_dict()

        return config, targets, schedule_info

    @classmethod
    def print_analysis_header(cls) -> None:
        """Print analysis header with Dallas-specific information."""
        print(f"{AnalysisConstants.MAP_EMOJI} Dallas Area Travel Time Analysis")
        print("=" * 70)

        config = DallasTargetDefinitions.get_dallas_config()
        print(
            f"   Grid center: ({config.center_lat:.4f}, {config.center_lon:.4f}) - Downtown Dallas"
        )
        print(f"   Coverage: Expanded Dallas metro area")
        print(f"   Radius: {config.radius_miles} miles")
        print(f"   Grid spacing: {config.grid_size_miles} mile(s)")
        print()
