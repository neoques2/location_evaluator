import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pandas as pd
import plotly.graph_objects as go
from src.analysis.html_generator import HTMLReportGenerator
from src.analysis.grid_analysis import GridAnalysisResult
from src.analysis.constants import AnalysisConfig


def make_dummy_result():
    cfg = AnalysisConfig(
        center_lat=40.0,
        center_lon=-75.0,
        radius_miles=1.0,
        grid_size_miles=0.5,
        analysis_name="Test",
        coverage_description="Test area",
    )
    df = pd.DataFrame(
        {
            "point_id": [0],
            "lat": [40.0],
            "lon": [-75.0],
            "total_weekly_travel_time": [0.0],
            "avg_trip_time": [0.0],
            "route_details": [[]],
            "successful_routes": [0],
        }
    )
    return GridAnalysisResult(
        grid_df=df, successful_targets=[], total_routes=0, analysis_config=cfg
    )


def test_html_generation(tmp_path):
    result = make_dummy_result()
    gen = HTMLReportGenerator(output_dir=str(tmp_path))
    html = gen.generate_combined_analysis_html(result, {}, "map.html", "plots.html")
    assert "<html" in html
    path = gen.create_complete_report(
        result, {}, go.Figure(), go.Figure(), report_prefix="test"
    )
    assert os.path.exists(path)
