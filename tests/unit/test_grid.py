import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pandas as pd
from src.core.grid_generator import AnalysisGrid


def test_grid_generation_basic():
    grid = AnalysisGrid(40.0, -75.0, radius_miles=1.0, grid_size_miles=0.5)
    df = grid.get_grid_dataframe()
    assert len(df) > 0
    assert {"lat", "lon", "distance_from_center", "point_id"}.issubset(df.columns)


def test_grid_bounds_consistent():
    grid = AnalysisGrid(40.0, -75.0, radius_miles=1.0, grid_size_miles=0.5)
    bounds = grid.get_grid_bounds()
    assert bounds["north"] >= bounds["south"]
    assert bounds["east"] >= bounds["west"]
