"""
Data Structures and Models
Defines data classes and type definitions for the location evaluator.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Location:
    """Represents a geographic location."""
    lat: float
    lon: float
    address: str
    neighborhood: Optional[str] = None
    nearby_poi: List[str] = field(default_factory=list)


@dataclass
class Route:
    """Represents a single route calculation."""
    departure_time: str
    arrival_time: str
    mode: str  # driving, walking, transit, biking
    duration: int  # minutes
    distance: float  # miles
    cost: float = 0.0  # dollars


@dataclass
class DestinationAnalysis:
    """Analysis for a specific destination."""
    weekly_trips: int
    monthly_trips: int
    avg_travel_time: float  # minutes
    total_weekly_time: int  # minutes
    routes: List[Route] = field(default_factory=list)


@dataclass
class TravelAnalysis:
    """Complete travel analysis for a location."""
    total_weekly_minutes: int
    total_monthly_minutes: int
    destinations: Dict[str, Dict[str, DestinationAnalysis]] = field(default_factory=dict)


@dataclass
class CostTotals:
    """Transportation cost totals."""
    driving_miles: float
    walking_miles: float
    biking_miles: float
    transit_cost: float


@dataclass
class CostAnalysis:
    """Complete cost analysis for a location."""
    weekly_totals: CostTotals
    monthly_totals: CostTotals
    breakdown_by_destination: Dict[str, CostTotals] = field(default_factory=dict)


@dataclass
class SafetyAnalysis:
    """Safety analysis for a location."""
    crime_score: float  # 0-1 scale, lower is safer
    nearby_incidents: int  # within radius
    safety_grade: str  # A+ to F scale
    crime_types: Dict[str, float] = field(default_factory=dict)


@dataclass
class CompositeScore:
    """Composite scoring for a location."""
    overall: float  # 0-1 scale, higher is better
    components: Dict[str, float] = field(default_factory=dict)
    grade: str = "C"
    rank_percentile: int = 50  # percentile rank within region


@dataclass
class GridPointAnalysis:
    """Complete analysis for a single grid point."""
    location: Location
    travel_analysis: TravelAnalysis
    cost_analysis: CostAnalysis
    safety_analysis: SafetyAnalysis
    composite_score: CompositeScore


@dataclass
class CacheInfo:
    """Cache metadata information."""
    created: str  # ISO datetime
    expires: str  # ISO datetime
    grid_point: Dict[str, float]  # lat, lon
    destination: Optional[str] = None
    departure_time: Optional[str] = None
    day: Optional[str] = None


@dataclass
class RouteCache:
    """Cached route data structure."""
    cache_info: CacheInfo
    destinations: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class AnalysisMetadata:
    """Metadata for the complete analysis."""
    generated: str  # ISO datetime
    grid_size: float  # miles
    total_points: int
    center_point: Dict[str, float]  # lat, lon
    bounds: Dict[str, float]  # north, south, east, west


@dataclass
class RegionalStatistics:
    """Regional statistics summary."""
    travel_time: Dict[str, float] = field(default_factory=dict)
    cost: Dict[str, float] = field(default_factory=dict)
    safety: Dict[str, float] = field(default_factory=dict)
    composite: Dict[str, float] = field(default_factory=dict)
    best_locations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AnalysisResults:
    """Complete analysis results."""
    analysis_metadata: AnalysisMetadata
    grid_points: List[GridPointAnalysis]
    regional_statistics: RegionalStatistics


# JSON Schema Documentation as Comments:

"""
Grid Point Analysis Output Schema:
{
  "location": {
    "lat": 40.7128,
    "lon": -74.0060,
    "address": "Manhattan, NY 10001",
    "neighborhood": "Midtown",
    "nearby_poi": [
      "Penn Station (0.3 mi)",
      "Herald Square (0.2 mi)",
      "Bryant Park (0.4 mi)"
    ]
  },
  "travel_analysis": {
    "total_weekly_minutes": 420,
    "total_monthly_minutes": 1680,
    "destinations": {
      "work": {
        "Main Office": {
          "weekly_trips": 10,
          "monthly_trips": 43,
          "avg_travel_time": 25,
          "total_weekly_time": 250,
          "routes": [
            {
              "departure_time": "08:35",
              "arrival_time": "09:00",
              "mode": "transit",
              "duration": 25,
              "distance": 8.2,
              "cost": 2.75
            }
          ]
        }
      }
    }
  },
  "cost_analysis": {
    "weekly_totals": {
      "driving_miles": 45.2,
      "walking_miles": 8.5,
      "biking_miles": 0.0,
      "transit_cost": 27.50
    },
    "monthly_totals": {
      "driving_miles": 196.4,
      "walking_miles": 37.0,
      "biking_miles": 0.0,
      "transit_cost": 119.75
    }
  },
  "safety_analysis": {
    "crime_score": 0.23,
    "crime_types": {
      "violent": 0.15,
      "property": 0.31,
      "other": 0.08
    },
    "nearby_incidents": 12,
    "safety_grade": "B+"
  },
  "composite_score": {
    "overall": 0.78,
    "components": {
      "travel_time": 0.82,
      "travel_cost": 0.71,
      "safety": 0.77
    },
    "grade": "B+",
    "rank_percentile": 78
  }
}
"""

"""
Route Cache Format Schema:
{
  "cache_info": {
    "created": "2024-01-15T10:30:00Z",
    "expires": "2024-01-22T10:30:00Z",
    "grid_point": {
      "lat": 40.7128,
      "lon": -74.0060
    }
  },
  "destinations": {
    "789 Corporate Dr, Business District, ST": {
      "geocoded": {
        "lat": 40.7589,
        "lon": -73.9851
      },
      "routes": {
        "08:35_Mon": {
          "departure_time": "08:35",
          "day_of_week": "Mon",
          "mode": "transit",
          "duration": 25,
          "distance": 8.2,
          "cost": 2.75,
          "steps": []
        }
      }
    }
  }
}
"""

"""
Analysis Results Summary Schema:
{
  "analysis_metadata": {
    "generated": "2024-01-15T15:45:00Z",
    "grid_size": 0.5,
    "total_points": 2401,
    "center_point": {
      "lat": 40.7128,
      "lon": -74.0060
    },
    "bounds": {
      "north": 41.0628,
      "south": 40.3628,
      "east": -73.3560,
      "west": -74.6560
    }
  },
  "regional_statistics": {
    "travel_time": {
      "min": 15,
      "max": 120,
      "avg": 45,
      "median": 42
    },
    "safety": {
      "min": 0.05,
      "max": 0.85,
      "avg": 0.34,
      "median": 0.31
    },
    "best_locations": [
      {
        "lat": 40.7128,
        "lon": -74.0060,
        "score": 0.92,
        "rank": 1
      }
    ]
  }
}
"""