"""
Dashboard Generation
Combines multiple visualizations into a comprehensive dashboard.
"""

import os
import plotly.graph_objects as go
from typing import Dict, Any
from .plotly_maps import create_main_map
from .statistics import create_summary_stats, create_top_locations_table


def generate_interactive_map(
    analysis_results: Dict[str, Any], output_path: str
) -> None:
    """Generate an interactive dashboard and save component figures.

    This function saves the individual Plotly figures first and then creates a
    small HTML page that embeds them via iframes. This helps troubleshoot issues
    where the combined figure may appear blank.

    Args:
        analysis_results: Complete analysis results
        output_path: Path to save final HTML dashboard
    """
    base_dir = os.path.dirname(output_path) or "."
    base_name = os.path.splitext(os.path.basename(output_path))[0]

    main_file = os.path.join(base_dir, f"{base_name}_map.html")
    stats_file = os.path.join(base_dir, f"{base_name}_stats.html")
    locations_file = os.path.join(base_dir, f"{base_name}_locations.html")

    main_fig = create_main_map(analysis_results)
    stats_fig = create_summary_stats(analysis_results)
    locations_fig = create_top_locations_table(analysis_results)

    main_fig.write_html(main_file)
    stats_fig.write_html(stats_file)
    locations_fig.write_html(locations_file)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Location Desirability Analysis Dashboard</title>
</head>
<body>
    <iframe src="{os.path.basename(main_file)}" width="100%" height="600" frameborder="0"></iframe>
    <div style="display:flex; gap:1%; margin-top:20px;">
        <iframe src="{os.path.basename(stats_file)}" width="49%" height="400" frameborder="0"></iframe>
        <iframe src="{os.path.basename(locations_file)}" width="49%" height="400" frameborder="0"></iframe>
    </div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Interactive map saved to: {output_path}")


def create_simple_map_output(
    analysis_results: Dict[str, Any], output_path: str
) -> None:
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
        "metadata": analysis_results["analysis_metadata"],
        "regional_stats": analysis_results["regional_statistics"],
        "top_locations": analysis_results["regional_statistics"]["best_locations"][:50],
        "grid_summary": [
            {
                "lat": point["location"]["lat"],
                "lon": point["location"]["lon"],
                "neighborhood": point["location"].get("neighborhood", "Unknown"),
                "overall_score": point["composite_score"]["overall"],
                "travel_time": point["travel_analysis"]["total_weekly_minutes"],
                "monthly_cost": (
                    point["cost_analysis"]["monthly_totals"]["driving_miles"] * 0.65
                    + point["cost_analysis"]["monthly_totals"]["transit_cost"]
                ),
            }
            for point in analysis_results["grid_points"]
        ],
    }

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"Data export saved to: {output_path}")
