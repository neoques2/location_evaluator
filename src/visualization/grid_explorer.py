"""
Grid Visualization and Exploration
Interactive visualization of analysis grid points and destinations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..core.grid_generator import AnalysisGrid
from ..core.scheduler import process_schedules


class GridExplorer:
    """
    Interactive visualization and exploration of analysis grids.
    """
    
    def __init__(self, grid: AnalysisGrid, config: Optional[Dict[str, Any]] = None):
        """
        Initialize grid explorer.
        
        Args:
            grid: AnalysisGrid instance
            config: Optional configuration for destinations
        """
        self.grid = grid
        self.config = config
        self.destinations_df = self._process_destinations() if config else None
    
    def _process_destinations(self) -> pd.DataFrame:
        """Process destinations from config into DataFrame."""
        destinations = []
        
        for category, dest_list in self.config['destinations'].items():
            for dest in dest_list:
                destinations.append({
                    'name': dest['name'],
                    'address': dest['address'],
                    'category': category,
                    'lat': None,  # Will be geocoded later
                    'lon': None   # Will be geocoded later
                })
        
        return pd.DataFrame(destinations)
    
    def create_grid_overview_map(self, title: str = "Analysis Grid Overview") -> go.Figure:
        """
        Create an overview map showing all grid points and destinations.
        
        Args:
            title: Map title
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Add grid points
        grid_df = self.grid.get_grid_dataframe()
        
        # Color points by distance from center for visual effect
        fig.add_trace(go.Scattermapbox(
            lat=grid_df['lat'],
            lon=grid_df['lon'],
            mode='markers',
            marker=dict(
                size=4,
                color=grid_df['distance_from_center'],
                colorscale='Viridis',
                colorbar=dict(
                    title="Distance from Center (miles)",
                    thickness=15,
                    len=0.7
                ),
                opacity=0.7
            ),
            text=[
                f"Point {row['point_id']}<br>"
                f"Lat: {row['lat']:.4f}<br>"
                f"Lon: {row['lon']:.4f}<br>"
                f"Distance: {row['distance_from_center']:.1f} mi"
                for _, row in grid_df.iterrows()
            ],
            hovertemplate='%{text}<extra></extra>',
            name='Grid Points'
        ))
        
        # Add center point
        fig.add_trace(go.Scattermapbox(
            lat=[self.grid.center_lat],
            lon=[self.grid.center_lon],
            mode='markers',
            marker=dict(
                size=12,
                color='red',
                symbol='circle'
            ),
            text=[f"Analysis Center<br>Lat: {self.grid.center_lat:.4f}<br>Lon: {self.grid.center_lon:.4f}"],
            hovertemplate='%{text}<extra></extra>',
            name='Center Point'
        ))
        
        # Add destinations if available
        if self.destinations_df is not None:
            # For now, add placeholder destinations near center
            # In real implementation, these would be geocoded
            sample_destinations = [
                {"name": "Work", "lat": self.grid.center_lat + 0.1, "lon": self.grid.center_lon + 0.1, "category": "work"},
                {"name": "Gym", "lat": self.grid.center_lat - 0.05, "lon": self.grid.center_lon + 0.05, "category": "personal"},
                {"name": "Doctor", "lat": self.grid.center_lat + 0.05, "lon": self.grid.center_lon - 0.1, "category": "monthly"}
            ]
            
            dest_df = pd.DataFrame(sample_destinations)
            
            # Color by category
            category_colors = {'work': 'blue', 'personal': 'green', 'monthly': 'orange'}
            
            for category in dest_df['category'].unique():
                cat_data = dest_df[dest_df['category'] == category]
                
                fig.add_trace(go.Scattermapbox(
                    lat=cat_data['lat'],
                    lon=cat_data['lon'],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=category_colors.get(category, 'purple'),
                        symbol='star'
                    ),
                    text=[f"{row['name']}<br>Category: {row['category']}" for _, row in cat_data.iterrows()],
                    hovertemplate='%{text}<extra></extra>',
                    name=f'{category.title()} Destinations'
                ))
        
        # Update layout
        fig.update_layout(
            title=title,
            mapbox=dict(
                style='open-street-map',
                center=dict(
                    lat=self.grid.center_lat,
                    lon=self.grid.center_lon
                ),
                zoom=9
            ),
            height=700,
            showlegend=True
        )
        
        return fig
    
    def create_grid_density_map(self) -> go.Figure:
        """
        Create a density heatmap of grid points.
        
        Returns:
            Plotly figure
        """
        grid_df = self.grid.get_grid_dataframe()
        
        # Create hexagonal binning for density
        fig = go.Figure()
        
        # Add density heatmap
        fig.add_trace(go.Densitymapbox(
            lat=grid_df['lat'],
            lon=grid_df['lon'],
            z=[1] * len(grid_df),  # Each point has equal weight
            radius=10,
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Point Density")
        ))
        
        # Update layout
        fig.update_layout(
            title="Grid Point Density Map",
            mapbox=dict(
                style='open-street-map',
                center=dict(
                    lat=self.grid.center_lat,
                    lon=self.grid.center_lon
                ),
                zoom=9
            ),
            height=600
        )
        
        return fig
    
    def create_grid_statistics_dashboard(self) -> go.Figure:
        """
        Create a dashboard with grid statistics.
        
        Returns:
            Plotly figure with subplots
        """
        grid_df = self.grid.get_grid_dataframe()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Distance Distribution',
                'Latitude Distribution', 
                'Longitude Distribution',
                'Grid Summary'
            ],
            specs=[
                [{"type": "xy"}, {"type": "xy"}],
                [{"type": "xy"}, {"type": "table"}]
            ]
        )
        
        # Distance distribution histogram
        fig.add_trace(
            go.Histogram(
                x=grid_df['distance_from_center'],
                nbinsx=20,
                name='Distance',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        # Latitude distribution
        fig.add_trace(
            go.Histogram(
                x=grid_df['lat'],
                nbinsx=20,
                name='Latitude',
                marker_color='lightgreen'
            ),
            row=1, col=2
        )
        
        # Longitude distribution
        fig.add_trace(
            go.Histogram(
                x=grid_df['lon'],
                nbinsx=20,
                name='Longitude',
                marker_color='lightcoral'
            ),
            row=2, col=1
        )
        
        # Summary table
        grid_info = self.grid.get_grid_info()
        
        summary_data = [
            ['Total Points', f"{grid_info['total_points']:,}"],
            ['Grid Size', f"{grid_info['grid_size_miles']} miles"],
            ['Radius', f"{grid_info['radius_miles']} miles"],
            ['Theoretical Area', f"{grid_info['coverage_area_sq_miles']:,.0f} sq mi"],
            ['Actual Coverage', f"{grid_info['actual_coverage_sq_miles']:,.0f} sq mi"],
            ['Center Lat', f"{grid_info['center_point']['lat']:.4f}"],
            ['Center Lon', f"{grid_info['center_point']['lon']:.4f}"],
            ['North Bound', f"{grid_info['bounds']['north']:.4f}"],
            ['South Bound', f"{grid_info['bounds']['south']:.4f}"],
            ['East Bound', f"{grid_info['bounds']['east']:.4f}"],
            ['West Bound', f"{grid_info['bounds']['west']:.4f}"]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=['Metric', 'Value'], fill_color='lightblue'),
                cells=dict(
                    values=[[row[0] for row in summary_data], [row[1] for row in summary_data]],
                    fill_color='white'
                )
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title="Grid Analysis Dashboard",
            height=800,
            showlegend=False
        )
        
        # Update x-axis labels
        fig.update_xaxes(title_text="Distance from Center (miles)", row=1, col=1)
        fig.update_xaxes(title_text="Latitude", row=1, col=2)
        fig.update_xaxes(title_text="Longitude", row=2, col=1)
        
        return fig
    
    def save_grid_to_html(self, filename: str = "grid_visualization.html") -> None:
        """
        Save interactive grid visualization to HTML file.
        
        Args:
            filename: Output filename
        """
        # Create overview map
        overview_fig = self.create_grid_overview_map()
        
        # Save to HTML
        overview_fig.write_html(filename, include_plotlyjs='cdn')
        print(f"Grid visualization saved to {filename}")
    
    def save_dashboard_to_html(self, filename: str = "grid_dashboard.html") -> None:
        """
        Save grid statistics dashboard to HTML file.
        
        Args:
            filename: Output filename
        """
        dashboard_fig = self.create_grid_statistics_dashboard()
        dashboard_fig.write_html(filename, include_plotlyjs='cdn')
        print(f"Grid dashboard saved to {filename}")


def visualize_grid_from_config(config_path: str = "config", 
                              output_file: str = "outputs/grid_visualization.html") -> None:
    """
    Convenient function to visualize grid from configuration.
    
    Args:
        config_path: Path to configuration
        output_file: Output HTML file
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from src.config_parser import ConfigParser
    
    # Load configuration
    parser = ConfigParser()
    config = parser.load_config(config_path)
    
    # Extract center point
    center_point = config['analysis']['center_point']
    if isinstance(center_point, str):
        # Use NYC default for now
        center_lat, center_lon = 40.7128, -74.0060
    else:
        center_lat, center_lon = center_point
    
    # Create grid
    grid = AnalysisGrid(
        center_lat=center_lat,
        center_lon=center_lon,
        radius_miles=config['analysis']['max_radius'],
        grid_size_miles=config['analysis']['grid_size']
    )
    
    # Create explorer and save visualization
    explorer = GridExplorer(grid, config)
    explorer.save_grid_to_html(output_file)
    
    print(f"Grid visualization created with {len(grid.grid_df)} points")
    print(f"Saved to: {output_file}")