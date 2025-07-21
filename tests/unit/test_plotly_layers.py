import plotly.graph_objects as go
from src.visualization.plotly_maps import create_main_map


def make_dummy_results():
    return {
        "analysis_metadata": {"center_point": {"lat": 0, "lon": 0}},
        "grid_points": [
            {
                "location": {"lat": 1.0, "lon": 1.0},
                "travel_analysis": {
                    "total_weekly_minutes": 10,
                    "total_monthly_minutes": 40,
                    "destinations": {},
                },
                "cost_analysis": {
                    "weekly_totals": {
                        "driving_miles": 0,
                        "walking_miles": 0,
                        "biking_miles": 0,
                        "transit_cost": 0,
                    },
                    "monthly_totals": {
                        "driving_miles": 0,
                        "walking_miles": 0,
                        "biking_miles": 0,
                        "transit_cost": 0,
                    },
                },
                "safety_analysis": {},
                "composite_score": {
                    "overall": 0.9,
                    "components": {
                        "travel_time": 0.9,
                        "travel_cost": 0.9,
                        "safety": 0.9,
                    },
                    "grade": "A",
                    "rank_percentile": 100,
                },
            }
        ],
    }


def test_main_map_layers():
    fig = create_main_map(make_dummy_results())
    layer_names = [trace.name for trace in fig.data]
    expected = [
        "Travel Time",
        "Transportation Cost",
        "Composite Score",
        "Destinations",
    ]
    assert layer_names == expected
    assert len(fig.data) == 4
    # when no token is provided the map should use open street map tiles
    assert fig.layout.mapbox.style == "open-street-map"
    assert fig.layout.mapbox.accesstoken is None
