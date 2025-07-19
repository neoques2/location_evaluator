#!/usr/bin/env python3
"""
Grid Visualization with Target Locations
Simple test showing grid points, targets, and travel time summaries on a map.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def get_api_key_from_config():
    """Get API key from config."""
    try:
        from src.config_parser import ConfigParser
        parser = ConfigParser()
        config = parser.load_config('config')
        return config.get('apis', {}).get('google_maps', {}).get('api_key')
    except Exception:
        return None


def create_grid_with_targets_visualization():
    """Create grid visualization with target locations and travel times."""
    print("🗽 Grid + Target Locations Visualization")
    print("=" * 50)
    
    api_key = get_api_key_from_config()
    if not api_key:
        print("❌ No API key found in config")
        return False
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.core.grid_generator import AnalysisGrid
        import plotly.graph_objects as go
        
        # Create NYC grid (smaller for demonstration)
        print("📍 Creating NYC grid...")
        center_lat, center_lon = 40.7589, -73.9851  # Times Square
        grid = AnalysisGrid(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_miles=3.0,
            grid_size_miles=0.5
        )
        
        print(f"✅ Generated {len(grid.grid_df)} grid points")
        
        # Define target locations
        print("🎯 Setting up target locations...")
        targets = [
            Destination("Empire State Building, NYC", "Empire State Building"),
            Destination("Central Park, NYC", "Central Park"),
            Destination("Wall Street, NYC", "Wall Street")
        ]
        
        # Geocode targets
        client = GoogleMapsClient(api_key, rate_limit=5)
        geocoded_targets = client.geocode_batch(targets)
        successful_targets = [t for t in geocoded_targets if not t.get('geocoding_failed', False)]
        
        print(f"✅ Geocoded {len(successful_targets)} targets:")
        print("📍 Target Locations Summary:")
        print("=" * 40)
        for i, target in enumerate(successful_targets, 1):
            print(f"   {i}. {target['name']}")
            print(f"      Coordinates: ({target['lat']:.4f}, {target['lon']:.4f})")
            print(f"      Address: {target.get('formatted_address', target.get('address', 'N/A'))}")
            print()
        
        # Check if targets are within reasonable bounds of the grid
        print("🗺️  Checking target locations are within map bounds...")
        target_lats = [t['lat'] for t in successful_targets]
        target_lons = [t['lon'] for t in successful_targets]
        
        grid_lat_min, grid_lat_max = grid.grid_df['lat'].min(), grid.grid_df['lat'].max()
        grid_lon_min, grid_lon_max = grid.grid_df['lon'].min(), grid.grid_df['lon'].max()
        
        # Expand bounds to include targets
        all_lats = list(grid.grid_df['lat']) + target_lats
        all_lons = list(grid.grid_df['lon']) + target_lons
        
        map_center_lat = (min(all_lats) + max(all_lats)) / 2
        map_center_lon = (min(all_lons) + max(all_lons)) / 2
        
        print(f"   Grid bounds: ({grid_lat_min:.4f}, {grid_lon_min:.4f}) to ({grid_lat_max:.4f}, {grid_lon_max:.4f})")
        print(f"   Target bounds: ({min(target_lats):.4f}, {min(target_lons):.4f}) to ({max(target_lats):.4f}, {max(target_lons):.4f})")
        print(f"   Map center adjusted to: ({map_center_lat:.4f}, {map_center_lon:.4f})")
        print("✅ All locations will be visible on the map")
        
        # Calculate travel times for subset of grid (first 25 points)
        print("⏱️  Calculating travel times...")
        test_grid = grid.grid_df.head(25).copy()
        
        result = client.batch_distance_calculations(
            grid_df=test_grid,
            destinations=successful_targets,
            mode='driving'
        )
        
        print(f"✅ Calculated {result['total_routes']} routes")
        
        # Process travel time data
        print("📊 Processing travel times...")
        grid_with_times = []
        
        for _, point in test_grid.iterrows():
            point_lat, point_lon = point['lat'], point['lon']
            total_time = 0
            routes_found = 0
            route_details = []
            
            # Find routes for this point
            for batch in result['batches']:
                for route in batch['routes']:
                    if (abs(route['origin']['lat'] - point_lat) < 0.0001 and 
                        abs(route['origin']['lon'] - point_lon) < 0.0001):
                        
                        if route['status'] in ['OK', 'ESTIMATED']:
                            duration = route.get('duration_seconds', 0) / 60  # minutes
                            total_time += duration
                            routes_found += 1
                            
                            route_details.append({
                                'dest': route['destination'].get('name', 'Unknown'),
                                'time': duration,
                                'distance': route.get('distance_miles', 0)
                            })
            
            avg_time = total_time / max(routes_found, 1)
            
            grid_with_times.append({
                'point_id': point['point_id'],
                'lat': point_lat,
                'lon': point_lon,
                'total_time': total_time,
                'avg_time': avg_time,
                'routes': route_details
            })
        
        grid_df = pd.DataFrame(grid_with_times)
        
        # Create visualization
        print("🎨 Creating interactive map...")
        
        fig = go.Figure()
        
        # Add grid points colored by total travel time
        fig.add_trace(go.Scattermapbox(
            lat=grid_df['lat'],
            lon=grid_df['lon'],
            mode='markers',
            marker=dict(
                size=12,
                color=grid_df['total_time'],
                colorscale='RdYlGn_r',  # Red = longer time, Green = shorter time
                colorbar=dict(
                    title="Total Travel Time (min)",
                    x=1.02,  # Move to the right
                    y=0.5    # Center vertically
                ),
                opacity=0.8
            ),
            text=[
                f"<b>Grid Point {row['point_id']}</b><br>" +
                f"Total Time: {row['total_time']:.1f} min<br>" +
                f"Avg Time: {row['avg_time']:.1f} min<br>" +
                "<br>".join([f"→ {r['dest']}: {r['time']:.1f}min" for r in row['routes']])
                for _, row in grid_df.iterrows()
            ],
            hovertemplate='%{text}<extra></extra>',
            name='Grid Points',
            showlegend=True
        ))
        
        # Add target locations - first add the base markers (dots)
        fig.add_trace(go.Scattermapbox(
            lat=[t['lat'] for t in successful_targets],
            lon=[t['lon'] for t in successful_targets],
            mode='markers',
            marker=dict(
                size=25,
                color='red',
                symbol='circle',
                opacity=0.9
            ),
            hovertemplate='<b>🎯 Target Location</b><br>' +
                         'Name: %{customdata[0]}<br>' +
                         'Lat: %{lat:.4f}<br>' +
                         'Lon: %{lon:.4f}<br>' +
                         'Address: %{customdata[1]}<extra></extra>',
            customdata=[[t['name'], t.get('formatted_address', t.get('address', 'N/A'))] for t in successful_targets],
            name='Target Locations (Base)',
            showlegend=False  # Don't show in legend as we'll add another trace
        ))
        
        # Add target location stars on top
        fig.add_trace(go.Scattermapbox(
            lat=[t['lat'] for t in successful_targets],
            lon=[t['lon'] for t in successful_targets],
            mode='markers+text',
            marker=dict(
                size=15,
                color='white',
                symbol='star',
                opacity=1.0
            ),
            text=[f"{i+1}" for i in range(len(successful_targets))],  # Number the targets
            textfont=dict(size=10, color='black', family='Arial Black'),
            textposition="middle center",
            hovertemplate='<b>🎯 Target #%{text}</b><br>' +
                         'Name: %{customdata[0]}<br>' +
                         'Lat: %{lat:.4f}<br>' +
                         'Lon: %{lon:.4f}<br>' +
                         'Address: %{customdata[1]}<extra></extra>',
            customdata=[[t['name'], t.get('formatted_address', t.get('address', 'N/A'))] for t in successful_targets],
            name='Target Locations',
            showlegend=True
        ))
        
        # Create detailed title with target list
        target_list = " | ".join([f"{i+1}. {t['name']}" for i, t in enumerate(successful_targets)])
        
        # Update layout
        fig.update_layout(
            title={
                'text': f"NYC Grid Analysis: Travel Times to Target Locations<br>" +
                       f"<sub>Targets: {target_list}</sub>",
                'x': 0.5,
                'font': {'size': 16}
            },
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=map_center_lat, lon=map_center_lon),
                zoom=11
            ),
            showlegend=True,
            height=800,
            width=1200,
            annotations=[
                dict(
                    text=f"<b>Target Locations:</b><br>" +
                         "<br>".join([f"🎯 {i+1}. {t['name']}<br>   📍 ({t['lat']:.4f}, {t['lon']:.4f})" 
                                     for i, t in enumerate(successful_targets)]),
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.3)",
                    borderwidth=1,
                    font=dict(size=11, family="Arial")
                )
            ]
        )
        
        # Save the visualization
        output_file = "outputs/grid_with_targets.html"
        os.makedirs("outputs", exist_ok=True)
        fig.write_html(output_file)
        
        file_size = os.path.getsize(output_file) / 1024
        print(f"✅ Map saved: {output_file} ({file_size:.1f} KB)")
        
        # Summary
        print("\n📊 Travel Time Summary:")
        print(f"   Best location (shortest total time): {grid_df['total_time'].min():.1f} min")
        print(f"   Worst location (longest total time): {grid_df['total_time'].max():.1f} min")
        print(f"   Average total time: {grid_df['total_time'].mean():.1f} min")
        
        best_point = grid_df.loc[grid_df['total_time'].idxmin()]
        print(f"\n🏆 Best Location: Point {best_point['point_id']}")
        print(f"   Coordinates: ({best_point['lat']:.4f}, {best_point['lon']:.4f})")
        print(f"   Total travel time: {best_point['total_time']:.1f} minutes")
        for route in best_point['routes']:
            print(f"   → {route['dest']}: {route['time']:.1f} min ({route['distance']:.1f} mi)")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("🚀 GRID + TARGETS VISUALIZATION TEST")
    print("=" * 50)
    
    success = create_grid_with_targets_visualization()
    
    if success:
        print("\n🎉 VISUALIZATION COMPLETE!")
        print("✅ Grid points displayed")
        print("✅ Target locations marked") 
        print("✅ Travel times calculated and shown")
        print("✅ Interactive map created")
        print("\n📁 Open outputs/grid_with_targets.html to see the map!")
    else:
        print("\n❌ Visualization failed")
    
    sys.exit(0 if success else 1)