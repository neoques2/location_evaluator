"""
Plotly Map Visualization
Creates interactive Plotly maps with multiple layers for location analysis.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any


def create_travel_time_layer(grid_points: List[Dict[str, Any]]) -> go.Densitymapbox:
    """
    Create travel time heatmap layer.

    Args:
        grid_points: List of grid points with analysis data

    Returns:
        Plotly Densitymapbox trace for travel time
    """
    travel_time_layer = go.Densitymapbox(
        lat=[point["location"]["lat"] for point in grid_points],
        lon=[point["location"]["lon"] for point in grid_points],
        z=[point["travel_analysis"]["total_weekly_minutes"] for point in grid_points],
        opacity=0.6,
        colorscale="Viridis",
        colorbar=dict(title="Weekly Travel Time (minutes)"),
        hovertemplate="<b>%{text}</b><br>"
        + "Travel Time: %{z} min/week<br>"
        + "Location: %{lat}, %{lon}<br>"
        + "<extra></extra>",
        visible=True,
        name="Travel Time",
    )
    return travel_time_layer


def create_transportation_cost_layer(
    grid_points: List[Dict[str, Any]],
) -> go.Densitymapbox:
    """
    Create transportation cost heatmap layer.

    Args:
        grid_points: List of grid points with analysis data

    Returns:
        Plotly Densitymapbox trace for transportation cost
    """
    cost_layer = go.Densitymapbox(
        lat=[point["location"]["lat"] for point in grid_points],
        lon=[point["location"]["lon"] for point in grid_points],
        z=[
            point["cost_analysis"]["monthly_totals"]["driving_miles"] * 0.65
            + point["cost_analysis"]["monthly_totals"]["transit_cost"]
            for point in grid_points
        ],
        opacity=0.6,
        colorscale="Reds",
        colorbar=dict(title="Monthly Transportation Cost ($)"),
        hovertemplate="<b>%{text}</b><br>"
        + "Monthly Cost: $%{z:.2f}<br>"
        + "Driving: %{customdata[0]:.1f} miles<br>"
        + "Transit: $%{customdata[1]:.2f}<br>"
        + "<extra></extra>",
        customdata=[
            [
                point["cost_analysis"]["monthly_totals"]["driving_miles"],
                point["cost_analysis"]["monthly_totals"]["transit_cost"],
            ]
            for point in grid_points
        ],
        visible=False,
        name="Transportation Cost",
    )
    return cost_layer


def create_composite_score_layer(grid_points: List[Dict[str, Any]]) -> go.Densitymapbox:
    """
    Create composite score heatmap layer.

    Args:
        grid_points: List of grid points with analysis data

    Returns:
        Plotly Densitymapbox trace for composite score
    """
    composite_layer = go.Densitymapbox(
        lat=[point["location"]["lat"] for point in grid_points],
        lon=[point["location"]["lon"] for point in grid_points],
        z=[point["composite_score"]["overall"] for point in grid_points],
        opacity=0.6,
        colorscale="Plasma",
        colorbar=dict(title="Overall Desirability Score"),
        hovertemplate="<b>%{text}</b><br>"
        + "Overall Score: %{z:.2f}<br>"
        + "Grade: %{customdata[0]}<br>"
        + "Percentile: %{customdata[1]}<br>"
        + "Travel: %{customdata[2]:.2f}<br>"
        + "Cost: %{customdata[3]:.2f}<br>"
        + "<extra></extra>",
        customdata=[
            [
                point["composite_score"]["grade"],
                point["composite_score"]["rank_percentile"],
                point["composite_score"]["components"]["travel_time"],
                point["composite_score"]["components"]["travel_cost"],
            ]
            for point in grid_points
        ],
        visible=False,
        name="Composite Score",
    )
    return composite_layer


def create_destinations_layer(destinations: List[Dict[str, Any]]) -> go.Scattermapbox:
    """
    Create destination markers layer.

    Args:
        destinations: List of destination locations

    Returns:
        Plotly Scattermapbox trace for destinations
    """
    destinations_trace = go.Scattermapbox(
        lat=[dest["lat"] for dest in destinations],
        lon=[dest["lon"] for dest in destinations],
        mode="markers",
        marker=dict(size=12, color="red", symbol="star"),
        text=[dest["name"] for dest in destinations],
        hovertemplate="<b>%{text}</b><br>" + "Destination<br>" + "<extra></extra>",
        name="Destinations",
    )
    return destinations_trace


def create_main_map(analysis_results: Dict[str, Any]) -> go.Figure:
    """Create main interactive map with all layers using open-street-map tiles.

    The map renders offline and does not require any Mapbox access tokens.

    Args:
        analysis_results: Complete analysis results

    Returns:
        Plotly Figure with interactive map
    """
    grid_points = analysis_results["grid_points"]
    destinations = analysis_results.get("destinations", [])

    # Get map center
    center_lat = analysis_results["analysis_metadata"]["center_point"]["lat"]
    center_lon = analysis_results["analysis_metadata"]["center_point"]["lon"]

    fig = go.Figure()

    # Add all layers
    fig.add_trace(create_travel_time_layer(grid_points))
    fig.add_trace(create_transportation_cost_layer(grid_points))
    fig.add_trace(create_composite_score_layer(grid_points))
    fig.add_trace(create_destinations_layer(destinations))

    mapbox_cfg = dict(
        style="open-street-map", center=dict(lat=center_lat, lon=center_lon), zoom=10
    )

    # Configure layout with layer toggles
    fig.update_layout(
        title="Location Desirability Analysis",
        mapbox=mapbox_cfg,
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list(
                    [
                        dict(
                            args=[{"visible": [True, False, False, True]}],
                            label="Travel Time",
                            method="restyle",
                        ),
                        dict(
                            args=[{"visible": [False, True, False, True]}],
                            label="Transportation Cost",
                            method="restyle",
                        ),
                        dict(
                            args=[{"visible": [False, False, True, True]}],
                            label="Composite Score",
                            method="restyle",
                        ),
                    ]
                ),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top",
            ),
        ],
    )

    return fig
