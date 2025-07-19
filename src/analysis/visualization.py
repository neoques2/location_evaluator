"""
Visualization Module for Location Analysis
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis.constants import AnalysisConstants
from src.analysis.grid_analysis import GridAnalysisResult


class MapVisualizer:
    """Creates interactive map visualizations for location analysis."""
    
    def __init__(self):
        self.colorscale = AnalysisConstants.COLORSCALE
        self.target_color = AnalysisConstants.TARGET_COLOR
        self.grid_opacity = AnalysisConstants.GRID_OPACITY
        self.contour_opacity = AnalysisConstants.CONTOUR_OPACITY
    
    def calculate_map_bounds(self, grid_df: pd.DataFrame, targets: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate optimal map center coordinates."""
        all_lats = list(grid_df["lat"]) + [t["lat"] for t in targets]
        all_lons = list(grid_df["lon"]) + [t["lon"] for t in targets]
        
        center_lat = (min(all_lats) + max(all_lats)) / 2
        center_lon = (min(all_lons) + max(all_lons)) / 2
        
        return center_lat, center_lon
    
    def create_main_map(self, analysis_result: GridAnalysisResult) -> go.Figure:
        """Create main interactive map with grid points and targets."""
        grid_df = analysis_result.grid_df
        targets = analysis_result.successful_targets
        config = analysis_result.analysis_config
        
        # Calculate map bounds
        center_lat, center_lon = self.calculate_map_bounds(grid_df, targets)
        
        # Create figure
        fig = go.Figure()
        
        # Add density layer
        fig.add_trace(
            go.Densitymapbox(
                lat=grid_df["lat"],
                lon=grid_df["lon"],
                z=grid_df["total_weekly_travel_time"],
                radius=25 * 1.5,
                zmin=grid_df["total_weekly_travel_time"].min(),
                zmax=grid_df["total_weekly_travel_time"].max() / 2.5,
                colorscale=self.colorscale,
                opacity=0.4,
                showscale=False,
            )
        )
        
        # Add grid points
        fig.add_trace(
            go.Scattermapbox(
                lat=grid_df["lat"],
                lon=grid_df["lon"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=grid_df["total_weekly_travel_time"],
                    colorscale=self.colorscale,
                    colorbar=dict(
                        title="Weekly travel time (min)", 
                        thickness=15, 
                        len=0.7
                    ),
                    opacity=self.grid_opacity,
                ),
                text=[
                    f"<b>Grid {r.point_id}</b><br>"
                    f"📍 ({r.lat:.4f}, {r.lon:.4f})<br>"
                    f"🕐 {r.total_weekly_travel_time:.1f} min<br>"
                    f"📊 Avg trip {r.avg_trip_time:.1f} min<br>"
                    f"🚗 Routes: {r.successful_routes}"
                    for r in grid_df.itertuples()
                ],
                hovertemplate="%{text}<extra></extra>",
                name="Grid points",
            )
        )
        
        # Add target locations
        fig.add_trace(
            go.Scattermapbox(
                lat=[t["lat"] for t in targets],
                lon=[t["lon"] for t in targets],
                mode="markers+text",
                marker=dict(size=28, color=self.target_color, symbol="star"),
                text=[str(i + 1) for i in range(len(targets))],
                textfont=dict(size=12, color="white", family="Arial Black"),
                textposition="middle center",
                name=f"{config.analysis_name} targets",
                hovertemplate="<b>%{hovertext}</b><br>📍 (%{lat:.4f}, %{lon:.4f})<extra></extra>",
                hovertext=[t["name"] for t in targets],
            )
        )
        
        # Configure layout
        target_list = " | ".join([
            f"{i+1}. {t['name'].replace('Movement ', 'Mvmt ')}"
            for i, t in enumerate(targets)
        ])
        
        fig.update_layout(
            title={
                "text": f"{config.analysis_name} - Interactive Map<br>"
                + f"<sub>{config.radius_miles}-Mile Coverage | Targets: {target_list}</sub>",
                "x": 0.5,
                "font": {"size": 20},
            },
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=AnalysisConstants.DEFAULT_ZOOM,
            ),
            height=AnalysisConstants.MAP_HEIGHT,
            width=AnalysisConstants.MAP_WIDTH,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.3)",
                borderwidth=1,
            ),
        )
        
        return fig
    
    def create_target_annotation(self, targets: List[Dict[str, Any]], schedule_info: Dict[str, str]) -> Dict[str, Any]:
        """Create annotation box with target information."""
        target_text = f"<b>{AnalysisConstants.TARGET_EMOJI} Targets:</b><br>" + "<br>".join([
            f"{i+1}. {t['name']}<br>   📍 ({t['lat']:.4f}, {t['lon']:.4f})"
            for i, t in enumerate(targets)
        ])
        
        schedule_text = "<br><br><b>📅 Weekly Schedule:</b><br>" + "<br>".join([
            f"• {name}: {schedule}" for name, schedule in schedule_info.items()
        ])
        
        return dict(
            text=target_text + schedule_text,
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.99,
            y=0.01,
            xanchor="right",
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            font=dict(size=10, family="Arial"),
        )


class SupportingPlotsVisualizer:
    """Creates supporting data visualization plots."""
    
    def create_supporting_plots(self, analysis_result: GridAnalysisResult) -> go.Figure:
        """Create supporting plots figure with histograms and charts."""
        grid_df = analysis_result.grid_df
        config = analysis_result.analysis_config
        
        # Create subplots
        fig = make_subplots(
            rows=1,
            cols=3,
            subplot_titles=[
                "Average Trip Time Distribution",
                "Weekly Schedule Impact by Destination",
                "Distance vs Travel Time Relationship",
            ],
            specs=[
                [{"type": "histogram"}, {"type": "bar"}, {"type": "scatter"}]
            ],
            horizontal_spacing=0.1,
        )
        
        # Plot 1: Histogram of average trip times
        fig.add_trace(
            go.Histogram(
                x=grid_df["avg_trip_time"],
                nbinsx=20,
                marker_color="lightblue",
                name="Trip Time Distribution",
                showlegend=False,
            ),
            row=1, col=1,
        )
        
        # Plot 2: Bar chart showing weekly schedule impact
        location_weekly_times = {}
        for _, point in grid_df.iterrows():
            for route in point["route_details"]:
                dest = route["destination"]
                weekly_time = route["weekly_time"]
                if dest not in location_weekly_times:
                    location_weekly_times[dest] = []
                location_weekly_times[dest].append(weekly_time)
        
        dest_names = [
            name.replace("Movement ", "Mvmt ").replace("Climbing", "Climb")
            for name in location_weekly_times.keys()
        ]
        avg_weekly_times = [np.mean(times) for times in location_weekly_times.values()]
        
        fig.add_trace(
            go.Bar(
                x=dest_names,
                y=avg_weekly_times,
                marker_color="orange",
                name="Avg Weekly Time",
                showlegend=False,
            ),
            row=1, col=2,
        )
        
        # Plot 3: Distance vs Time scatter
        distances = []
        times = []
        destinations_scatter = []
        for _, point in grid_df.iterrows():
            for route in point["route_details"]:
                distances.append(route["distance"])
                times.append(route["travel_time"])
                destinations_scatter.append(
                    route["destination"].replace("Movement ", "Mvmt ")
                )
        
        fig.add_trace(
            go.Scatter(
                x=distances,
                y=times,
                mode="markers",
                marker=dict(
                    color=distances, 
                    colorscale="Viridis", 
                    opacity=0.7, 
                    size=6
                ),
                text=destinations_scatter,
                hovertemplate="<b>%{text}</b><br>Distance: %{x:.1f} mi<br>Time: %{y:.1f} min<extra></extra>",
                name="Routes",
                showlegend=False,
            ),
            row=1, col=3,
        )
        
        # Configure layout
        fig.update_layout(
            title={
                "text": f"{config.analysis_name} - Supporting Data Visualizations",
                "x": 0.5,
                "font": {"size": 16},
            },
            height=AnalysisConstants.SUPPORTING_PLOTS_HEIGHT,
            width=AnalysisConstants.MAP_WIDTH,
            showlegend=False,
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Average Trip Time (min)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_xaxes(title_text="Destination", row=1, col=2)
        fig.update_yaxes(title_text="Avg Weekly Time (min)", row=1, col=2)
        fig.update_xaxes(title_text="Distance (miles)", row=1, col=3)
        fig.update_yaxes(title_text="Travel Time (min)", row=1, col=3)
        
        return fig


class AnalysisVisualizer:
    """Main visualization coordinator for location analysis."""
    
    def __init__(self):
        self.map_visualizer = MapVisualizer()
        self.supporting_visualizer = SupportingPlotsVisualizer()
    
    def create_complete_visualization(
        self, 
        analysis_result: GridAnalysisResult,
        schedule_info: Dict[str, str]
    ) -> Tuple[go.Figure, go.Figure]:
        """Create complete visualization with main map and supporting plots."""
        print(f"{AnalysisConstants.ART_EMOJI} Creating interactive visualization...")
        
        # Create main map
        main_fig = self.map_visualizer.create_main_map(analysis_result)
        
        # Add target annotation
        annotation = self.map_visualizer.create_target_annotation(
            analysis_result.successful_targets, 
            schedule_info
        )
        main_fig.update_layout(annotations=[annotation])
        
        # Create supporting plots
        supporting_fig = self.supporting_visualizer.create_supporting_plots(analysis_result)
        
        return main_fig, supporting_fig