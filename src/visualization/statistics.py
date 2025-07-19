"""
Summary Statistics and Tables
Creates summary statistics tables and top locations rankings.
"""

import plotly.graph_objects as go
from typing import Dict, Any, List


def create_summary_stats(analysis_results: Dict[str, Any]) -> go.Figure:
    """
    Create summary statistics table.
    
    Args:
        analysis_results: Complete analysis results
        
    Returns:
        Plotly Figure with summary statistics table
    """
    stats = analysis_results['regional_statistics']
    
    summary_table = go.Figure(data=[go.Table(
        header=dict(
            values=['Metric', 'Min', 'Max', 'Average', 'Median'],
            fill_color='lightblue',
            align='left'
        ),
        cells=dict(
            values=[
                ['Travel Time (min)', 'Monthly Cost ($)', 'Safety Score'],
                [stats['travel_time']['min'], f"${stats['cost']['min']:.2f}", f"{stats['safety']['min']:.2f}"],
                [stats['travel_time']['max'], f"${stats['cost']['max']:.2f}", f"{stats['safety']['max']:.2f}"],
                [stats['travel_time']['avg'], f"${stats['cost']['avg']:.2f}", f"{stats['safety']['avg']:.2f}"],
                [stats['travel_time']['median'], f"${stats['cost']['median']:.2f}", f"{stats['safety']['median']:.2f}"]
            ],
            fill_color='white',
            align='left'
        )
    )])
    
    summary_table.update_layout(
        title="Regional Statistics Summary",
        height=300
    )
    
    return summary_table


def create_top_locations_table(analysis_results: Dict[str, Any]) -> go.Figure:
    """
    Create table of best scoring locations.
    
    Args:
        analysis_results: Complete analysis results
        
    Returns:
        Plotly Figure with top locations table
    """
    top_locations = analysis_results['regional_statistics']['best_locations'][:10]
    
    locations_table = go.Figure(data=[go.Table(
        header=dict(
            values=['Rank', 'Neighborhood', 'Score', 'Travel Time', 'Cost', 'Safety'],
            fill_color='lightgreen',
            align='left'
        ),
        cells=dict(
            values=[
                [i+1 for i in range(len(top_locations))],
                [loc['neighborhood'] for loc in top_locations],
                [f"{loc['score']:.2f}" for loc in top_locations],
                [f"{loc['travel_time']:.0f} min" for loc in top_locations],
                [f"${loc['cost']:.2f}" for loc in top_locations],
                [loc['safety_grade'] for loc in top_locations]
            ],
            fill_color='white',
            align='left'
        )
    )])
    
    locations_table.update_layout(
        title="Top 10 Locations",
        height=400
    )
    
    return locations_table


def calculate_regional_statistics(grid_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate regional statistics from grid point data.
    
    Args:
        grid_points: List of analyzed grid points
        
    Returns:
        Dictionary with regional statistics
    """
    travel_times = [point['travel_analysis']['total_weekly_minutes'] for point in grid_points]
    monthly_costs = [
        point['cost_analysis']['monthly_totals']['driving_miles'] * 0.65 + 
        point['cost_analysis']['monthly_totals']['transit_cost'] 
        for point in grid_points
    ]
    safety_scores = [1 - point['safety_analysis']['crime_score'] for point in grid_points]  # Inverted
    composite_scores = [point['composite_score']['overall'] for point in grid_points]
    
    # Sort locations by composite score for best locations list
    sorted_points = sorted(grid_points, key=lambda x: x['composite_score']['overall'], reverse=True)
    best_locations = []
    
    for i, point in enumerate(sorted_points[:20]):  # Top 20
        best_locations.append({
            'lat': point['location']['lat'],
            'lon': point['location']['lon'],
            'neighborhood': point['location'].get('neighborhood', 'Unknown'),
            'score': point['composite_score']['overall'],
            'rank': i + 1,
            'travel_time': point['travel_analysis']['total_weekly_minutes'],
            'cost': (point['cost_analysis']['monthly_totals']['driving_miles'] * 0.65 + 
                    point['cost_analysis']['monthly_totals']['transit_cost']),
            'safety_grade': point['safety_analysis']['safety_grade']
        })
    
    return {
        'travel_time': {
            'min': min(travel_times),
            'max': max(travel_times),
            'avg': sum(travel_times) / len(travel_times),
            'median': sorted(travel_times)[len(travel_times) // 2]
        },
        'cost': {
            'min': min(monthly_costs),
            'max': max(monthly_costs),
            'avg': sum(monthly_costs) / len(monthly_costs),
            'median': sorted(monthly_costs)[len(monthly_costs) // 2]
        },
        'safety': {
            'min': min(safety_scores),
            'max': max(safety_scores),
            'avg': sum(safety_scores) / len(safety_scores),
            'median': sorted(safety_scores)[len(safety_scores) // 2]
        },
        'composite': {
            'min': min(composite_scores),
            'max': max(composite_scores),
            'avg': sum(composite_scores) / len(composite_scores),
            'median': sorted(composite_scores)[len(composite_scores) // 2]
        },
        'best_locations': best_locations
    }