"""
HTML Generator Module for Location Analysis Reports
"""

import os
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
from pathlib import Path

from src.analysis.constants import AnalysisConstants
from src.analysis.grid_analysis import GridAnalysisResult


class HTMLReportGenerator:
    """Generates HTML reports for location analysis."""

    def __init__(self, output_dir: str = AnalysisConstants.OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def save_plotly_figure(self, fig: go.Figure, filename: str) -> str:
        """Save a Plotly figure as HTML and return file info."""
        file_path = self.output_dir / filename
        fig.write_html(file_path)
        file_size = file_path.stat().st_size / 1024  # KB
        print(
            f"{AnalysisConstants.SUCCESS_EMOJI} Saved: {file_path} ({file_size:.1f} KB)"
        )
        return str(file_path)

    def generate_target_locations_html(self, targets: List[Dict[str, Any]]) -> str:
        """Generate HTML list of target locations."""
        return "".join(
            [
                f"<li><strong>{i+1}. {t['name']}</strong> - "
                f"({t['lat']:.4f}, {t['lon']:.4f})</li>"
                for i, t in enumerate(targets)
            ]
        )

    def generate_schedule_html(self, schedule_info: Dict[str, str]) -> str:
        """Generate HTML list of schedule information."""
        return "".join(
            [
                f"<li><strong>{name}:</strong> {schedule}</li>"
                for name, schedule in schedule_info.items()
            ]
        )

    def generate_combined_analysis_html(
        self,
        analysis_result: GridAnalysisResult,
        schedule_info: Dict[str, str],
        main_map_filename: str,
        supporting_plots_filename: str,
    ) -> str:
        """Generate combined HTML report with embedded iframes."""
        stats = analysis_result.get_summary_stats()
        config = analysis_result.analysis_config

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{config.analysis_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .map-section {{ margin-bottom: 50px; }}
        .plots-section {{ margin-top: 50px; }}
        .description {{ 
            background-color: #f8f9fa; 
            padding: 20px; 
            border-left: 4px solid #007bff; 
            margin: 20px 0; 
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #fff;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #ddd;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{AnalysisConstants.MAP_EMOJI} {config.analysis_name}</h1>
        <p><strong>Interactive Location Optimization for Weekly Commute Schedule</strong></p>
    </div>
    
    <div class="description">
        <h3>{AnalysisConstants.INFO_EMOJI} Analysis Overview</h3>
        <p>This analysis evaluates <strong>{stats['grid_points']:,} potential residential locations</strong> across the {config.coverage_description} ({config.radius_miles}-mile radius) based on weekly travel time to <strong>{stats['target_count']} target destinations</strong>.</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['min_travel_time']:.1f} min</div>
                <div class="stat-label">Best Location</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['mean_travel_time']:.1f} min</div>
                <div class="stat-label">Average Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['std_travel_time']:.1f} min</div>
                <div class="stat-label">Standard Deviation</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_travel_time']:.1f} min</div>
                <div class="stat-label">Worst Location</div>
            </div>
        </div>
        
        <h4>{AnalysisConstants.TARGET_EMOJI} Target Destinations:</h4>
        <ul>
        {self.generate_target_locations_html(analysis_result.successful_targets)}
        </ul>
        
        <h4>{AnalysisConstants.TIME_EMOJI} Weekly Schedule:</h4>
        <ul>
        {self.generate_schedule_html(schedule_info)}
        </ul>
    </div>
    
    <div class="map-section">
        <h2>{AnalysisConstants.MAP_EMOJI} Interactive Map View</h2>
        <p><em>Zoom in/out and click on points for detailed information. Red markers show target destinations, colored grid points show travel time optimization.</em></p>
        <iframe src="{main_map_filename}" width="100%" height="{AnalysisConstants.MAP_HEIGHT + 50}" frameborder="0"></iframe>
    </div>
    
    <div class="plots-section">
        <h2>{AnalysisConstants.ANALYSIS_EMOJI} Supporting Data Analysis</h2>
        <p><em>Additional charts showing travel time distributions, schedule impact, and distance relationships.</em></p>
        <iframe src="{supporting_plots_filename}" width="100%" height="{AnalysisConstants.SUPPORTING_PLOTS_HEIGHT + 50}" frameborder="0"></iframe>
    </div>
    
    <div class="description">
        <h3>{AnalysisConstants.SUCCESS_EMOJI} How to Use This Analysis</h3>
        <ol>
            <li><strong>Explore the map:</strong> Zoom and pan to explore different neighborhoods. Green areas have shorter total weekly travel times.</li>
            <li><strong>Check specific locations:</strong> Click on any grid point to see exact travel times and coordinates.</li>
            <li><strong>Identify optimal areas:</strong> Look for green clusters that balance proximity to multiple destinations.</li>
            <li><strong>Consider trade-offs:</strong> Use the supporting charts to understand travel time distributions and destination-specific impacts.</li>
        </ol>
    </div>
</body>
</html>
"""
        return html_template

    def create_complete_report(
        self,
        analysis_result: GridAnalysisResult,
        schedule_info: Dict[str, str],
        main_figure: go.Figure,
        supporting_figure: go.Figure,
        report_prefix: str = "analysis",
    ) -> str:
        """Create complete HTML report with all components."""
        print(f"{AnalysisConstants.ART_EMOJI} Generating HTML report...")

        # Generate filenames
        main_filename = f"{report_prefix}_map.html"
        supporting_filename = f"{report_prefix}_supporting.html"
        combined_filename = f"{report_prefix}_complete.html"

        # Save individual figures
        main_path = self.save_plotly_figure(main_figure, main_filename)
        supporting_path = self.save_plotly_figure(
            supporting_figure, supporting_filename
        )

        # Generate combined HTML
        combined_html = self.generate_combined_analysis_html(
            analysis_result=analysis_result,
            schedule_info=schedule_info,
            main_map_filename=main_filename,
            supporting_plots_filename=supporting_filename,
        )

        # Save combined report
        combined_path = self.output_dir / combined_filename
        with open(combined_path, "w") as f:
            f.write(combined_html)

        combined_size = combined_path.stat().st_size / 1024
        print(
            f"{AnalysisConstants.SUCCESS_EMOJI} Complete report saved: {combined_path} ({combined_size:.1f} KB)"
        )

        return str(combined_path)

    def print_analysis_summary(self, analysis_result: GridAnalysisResult) -> None:
        """Print detailed analysis summary to console."""
        print(f"\n{AnalysisConstants.ANALYSIS_EMOJI} Analysis Summary")
        print("=" * 60)

        stats = analysis_result.get_summary_stats()
        best_location = analysis_result.get_best_location()
        worst_location = analysis_result.get_worst_location()

        print(
            f"{AnalysisConstants.SUCCESS_EMOJI} Best Location (Lowest Weekly Travel Time):"
        )
        print(
            f"   Point {best_location['point_id']}: ({best_location['lat']:.4f}, {best_location['lon']:.4f})"
        )
        print(
            f"   Total weekly travel time: {best_location['total_weekly_travel_time']:.1f} minutes"
        )
        print(f"   Average trip time: {best_location['avg_trip_time']:.1f} minutes")

        print(
            f"\n{AnalysisConstants.INFO_EMOJI} Worst Location (Highest Weekly Travel Time):"
        )
        print(
            f"   Point {worst_location['point_id']}: ({worst_location['lat']:.4f}, {worst_location['lon']:.4f})"
        )
        print(
            f"   Total weekly travel time: {worst_location['total_weekly_travel_time']:.1f} minutes"
        )
        print(f"   Average trip time: {worst_location['avg_trip_time']:.1f} minutes")

        print(f"\n{AnalysisConstants.ANALYSIS_EMOJI} Overall Statistics:")
        print(f"   Grid points analyzed: {stats['grid_points']:,}")
        print(f"   Target destinations: {stats['target_count']}")
        print(f"   Total routes calculated: {analysis_result.total_routes:,}")
        print(
            f"   Average weekly travel time: {stats['mean_travel_time']:.1f} ± {stats['std_travel_time']:.1f} min"
        )

        print(
            f"\n{AnalysisConstants.TARGET_EMOJI} Weekly Schedule Details for Best Location:"
        )
        for route in best_location["route_details"]:
            print(
                f"   → {route['destination']}: {route['travel_time']:.1f} min/trip × {route['frequency']} = {route['weekly_time']:.1f} min/week"
            )


class ReportFileManager:
    """Manages report file organization and cleanup."""

    def __init__(self, output_dir: str = AnalysisConstants.OUTPUT_DIR):
        self.output_dir = Path(output_dir)

    def ensure_output_directory(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(exist_ok=True)

    def cleanup_old_reports(self, report_prefix: str) -> None:
        """Clean up old report files with given prefix."""
        patterns = [f"{report_prefix}_*.html", f"{report_prefix}_complete.html"]

        for pattern in patterns:
            for file_path in self.output_dir.glob(pattern):
                try:
                    file_path.unlink()
                    print(f"Cleaned up old report: {file_path}")
                except OSError:
                    pass

    def get_report_info(self, report_prefix: str) -> Dict[str, Any]:
        """Get information about generated report files."""
        files = {
            "main": self.output_dir / f"{report_prefix}_map.html",
            "supporting": self.output_dir / f"{report_prefix}_supporting.html",
            "combined": self.output_dir / f"{report_prefix}_complete.html",
        }

        info = {}
        for name, path in files.items():
            if path.exists():
                info[name] = {
                    "path": str(path),
                    "size_kb": path.stat().st_size / 1024,
                    "exists": True,
                }
            else:
                info[name] = {"exists": False}

        return info
