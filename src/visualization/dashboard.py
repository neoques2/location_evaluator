"""
Dashboard Generation
Combines multiple visualizations into a comprehensive dashboard.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any
from .plotly_maps import create_main_map
from .statistics import create_summary_stats, create_top_locations_table


def generate_interactive_map(analysis_results: Dict[str, Any], output_path: str) -> None:
    """
    Generate final HTML output with all visualizations.
    
    Args:
        analysis_results: Complete analysis results
        output_path: Path to save HTML output
    """
    # Create main map
    main_fig = create_main_map(analysis_results)
    
    # Create summary statistics
    stats_fig = create_summary_stats(analysis_results)
    
    # Create top locations table
    locations_fig = create_top_locations_table(analysis_results)
    
    # Combine into dashboard
    dashboard = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "mapbox", "colspan": 2}, None],
               [{"type": "table"}, {"type": "table"}]],
        subplot_titles=('Location Analysis', 'Regional Statistics', 'Top Locations')
    )
    
    # Add traces to dashboard
    for trace in main_fig.data:
        dashboard.add_trace(trace, row=1, col=1)
    
    dashboard.add_trace(stats_fig.data[0], row=2, col=1)
    dashboard.add_trace(locations_fig.data[0], row=2, col=2)
    
    # Update layout
    dashboard.update_layout(
        title='Location Desirability Analysis Dashboard',
        height=1200,
        showlegend=False
    )
    
    # Copy mapbox configuration from main map
    dashboard.update_layout(mapbox=main_fig.layout.mapbox)
    
    # Copy update menus (layer toggles) from main map
    dashboard.update_layout(updatemenus=main_fig.layout.updatemenus)
    
    # Save to HTML
    dashboard.write_html(output_path)
    
    print(f"Interactive map saved to: {output_path}")


def create_simple_map_output(analysis_results: Dict[str, Any], output_path: str) -> None:
    """
    Create a simpler map-only output without dashboard layout.
    
    Args:
        analysis_results: Complete analysis results
        output_path: Path to save HTML output
    """
    # Create main map
    main_fig = create_main_map(analysis_results)
    
    # Save to HTML
    main_fig.write_html(output_path)
    
    print(f"Interactive map saved to: {output_path}")


def create_data_export(analysis_results: Dict[str, Any], output_path: str) -> None:
    """
    Export analysis results as JSON for further processing.
    
    Args:
        analysis_results: Complete analysis results
        output_path: Path to save JSON output
    """
    import json
    
    # Create a simplified export format
    export_data = {
        'metadata': analysis_results['analysis_metadata'],
        'regional_stats': analysis_results['regional_statistics'],
        'top_locations': analysis_results['regional_statistics']['best_locations'][:50],
        'grid_summary': [
            {
                'lat': point['location']['lat'],
                'lon': point['location']['lon'],
                'neighborhood': point['location'].get('neighborhood', 'Unknown'),
                'overall_score': point['composite_score']['overall'],
                'travel_time': point['travel_analysis']['total_weekly_minutes'],
                'monthly_cost': (
                    point['cost_analysis']['monthly_totals']['driving_miles'] * 0.65 + 
                    point['cost_analysis']['monthly_totals']['transit_cost']
                ),
                'safety_grade': point['safety_analysis']['safety_grade']
            }
            for point in analysis_results['grid_points']
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Data export saved to: {output_path}")