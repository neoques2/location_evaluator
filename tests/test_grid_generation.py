#!/usr/bin/env python3
"""
Test Grid Generation - Deep Dive
Examining how the grid generation works step by step.
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_grid_generation():
    """Analyze the grid generation process step by step."""
    print("🔍 GRID GENERATION DEEP DIVE")
    print("=" * 50)
    
    try:
        from src.core.grid_generator import AnalysisGrid
        
        # Create a small test grid to examine the pattern
        print("📍 Creating test grid...")
        center_lat, center_lon = 32.7767, -96.7970  # Dallas
        radius_miles = 5.0
        grid_size_miles = 0.5
        
        print(f"   Center: ({center_lat}, {center_lon})")
        print(f"   Radius: {radius_miles} miles")
        print(f"   Grid spacing: {grid_size_miles} miles")
        
        # Create grid
        grid = AnalysisGrid(center_lat, center_lon, radius_miles, grid_size_miles)
        
        print(f"✅ Generated {len(grid.grid_df)} grid points")
        print()
        
        # Show the underlying calculation steps
        print("🔢 Step-by-step calculation:")
        print("=" * 30)
        
        # Step 1: Convert miles to degrees
        lat_per_mile = 1.0 / 69.0
        lon_per_mile = 1.0 / (69.0 * np.cos(np.radians(center_lat)))
        
        print(f"1. Coordinate conversion:")
        print(f"   lat_per_mile = {lat_per_mile:.6f}")
        print(f"   lon_per_mile = {lon_per_mile:.6f}")
        
        # Step 2: Grid spacing
        lat_spacing = grid_size_miles * lat_per_mile
        lon_spacing = grid_size_miles * lon_per_mile
        
        print(f"2. Grid spacing in degrees:")
        print(f"   lat_spacing = {lat_spacing:.6f}°")
        print(f"   lon_spacing = {lon_spacing:.6f}°")
        
        # Step 3: Bounding box
        radius_lat = radius_miles * lat_per_mile
        radius_lon = radius_miles * lon_per_mile
        
        print(f"3. Bounding box:")
        print(f"   radius_lat = {radius_lat:.6f}°")
        print(f"   radius_lon = {radius_lon:.6f}°")
        
        # Step 4: Generate ranges
        lat_range = np.arange(
            center_lat - radius_lat,
            center_lat + radius_lat + lat_spacing,
            lat_spacing
        )
        lon_range = np.arange(
            center_lon - radius_lon,
            center_lon + radius_lon + lon_spacing,
            lon_spacing
        )
        
        print(f"4. Grid ranges:")
        print(f"   lat_range: {len(lat_range)} points from {lat_range[0]:.6f} to {lat_range[-1]:.6f}")
        print(f"   lon_range: {len(lon_range)} points from {lon_range[0]:.6f} to {lon_range[-1]:.6f}")
        print(f"   Total combinations: {len(lat_range)} × {len(lon_range)} = {len(lat_range) * len(lon_range)}")
        
        # Step 5: Show first few points
        print(f"5. First 10 grid points:")
        for i in range(min(10, len(grid.grid_df))):
            row = grid.grid_df.iloc[i]
            print(f"   Point {i}: ({row['lat']:.6f}, {row['lon']:.6f}) - {row['distance_from_center']:.2f} miles")
        
        # Step 6: Show grid pattern
        print(f"6. Grid pattern analysis:")
        
        # Check if points are evenly spaced
        lats = sorted(grid.grid_df['lat'].unique())
        lons = sorted(grid.grid_df['lon'].unique())
        
        print(f"   Unique latitudes: {len(lats)}")
        print(f"   Unique longitudes: {len(lons)}")
        
        if len(lats) > 1:
            lat_diffs = np.diff(lats)
            print(f"   Latitude spacing: {lat_diffs[0]:.6f}° (should be {lat_spacing:.6f}°)")
            print(f"   Latitude spacing consistent: {np.allclose(lat_diffs, lat_spacing)}")
        
        if len(lons) > 1:
            lon_diffs = np.diff(lons)
            print(f"   Longitude spacing: {lon_diffs[0]:.6f}° (should be {lon_spacing:.6f}°)")
            print(f"   Longitude spacing consistent: {np.allclose(lon_diffs, lon_spacing)}")
        
        # Step 7: Test sampling impact
        print(f"\n7. Testing sampling impact:")
        
        # Original grid
        original_count = len(grid.grid_df)
        print(f"   Original grid: {original_count} points")
        
        # Simulate Dallas-style sampling
        test_size = 50
        if original_count > test_size:
            # Method 1: Just take first N (bad)
            first_n = grid.grid_df.head(test_size)
            print(f"   First {test_size} points: Regular pattern? {check_grid_regularity(first_n)}")
            
            # Method 2: Every nth point (better)
            step = original_count // test_size
            every_nth = grid.grid_df.iloc[::step].head(test_size)
            print(f"   Every {step}th point: Regular pattern? {check_grid_regularity(every_nth)}")
            
            # Method 3: Sorted sampling (what Dallas does - destroys pattern)
            sorted_df = grid.grid_df.sort_values(['lat', 'lon']).reset_index(drop=True)
            sorted_sample = sorted_df.iloc[::step].head(test_size)
            print(f"   Sorted sampling: Regular pattern? {check_grid_regularity(sorted_sample)}")
        
        # Step 8: Visualize if possible
        print(f"\n8. Grid visualization:")
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 4))
            
            # Plot 1: Full grid
            plt.subplot(1, 3, 1)
            plt.scatter(grid.grid_df['lon'], grid.grid_df['lat'], s=10, alpha=0.6)
            plt.title(f'Full Grid ({len(grid.grid_df)} points)')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.grid(True, alpha=0.3)
            
            # Plot 2: Every nth sampling
            if original_count > test_size:
                plt.subplot(1, 3, 2)
                plt.scatter(every_nth['lon'], every_nth['lat'], s=20, alpha=0.8, color='orange')
                plt.title(f'Every {step}th Point ({len(every_nth)} points)')
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.grid(True, alpha=0.3)
                
                # Plot 3: Sorted sampling
                plt.subplot(1, 3, 3)
                plt.scatter(sorted_sample['lon'], sorted_sample['lat'], s=20, alpha=0.8, color='red')
                plt.title(f'Sorted Sampling ({len(sorted_sample)} points)')
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('outputs/grid_analysis.png', dpi=150, bbox_inches='tight')
            print("   ✅ Grid visualization saved to outputs/grid_analysis.png")
            
        except Exception as e:
            print(f"   ⚠️  Could not create visualization: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_grid_regularity(df):
    """Check if a dataframe represents a regular grid."""
    if len(df) < 4:
        return "Too few points"
    
    # Check if we have regular spacing
    lats = sorted(df['lat'].unique())
    lons = sorted(df['lon'].unique())
    
    if len(lats) < 2 or len(lons) < 2:
        return "Not enough unique coordinates"
    
    # Check latitude spacing
    lat_diffs = np.diff(lats)
    lat_regular = np.allclose(lat_diffs, lat_diffs[0], rtol=1e-5)
    
    # Check longitude spacing
    lon_diffs = np.diff(lons)
    lon_regular = np.allclose(lon_diffs, lon_diffs[0], rtol=1e-5)
    
    if lat_regular and lon_regular:
        return "YES - Regular grid"
    else:
        return "NO - Irregular spacing"


if __name__ == '__main__':
    print("🚀 GRID GENERATION ANALYSIS")
    print("=" * 70)
    
    # Make sure outputs directory exists
    os.makedirs('outputs', exist_ok=True)
    
    success = analyze_grid_generation()
    
    if success:
        print("\n✅ Grid analysis complete!")
        print("📊 Check the output above to understand the grid generation process")
        print("🖼️  Check outputs/grid_analysis.png for visual comparison")
    else:
        print("\n❌ Grid analysis failed")
    
    sys.exit(0 if success else 1)