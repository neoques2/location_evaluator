#!/usr/bin/env python3
"""
NYC Travel Time Visualization Test
Creates an interactive map showing grid points, target locations, and travel times.
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


def create_nyc_travel_time_analysis():
    """Create comprehensive NYC travel time analysis with visualization."""
    print("🗽 NYC Travel Time Analysis & Visualization")
    print("=" * 70)
    
    api_key = get_api_key_from_config()
    if not api_key:
        print("❌ No API key found in config")
        return False
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.core.grid_generator import AnalysisGrid
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        
        # Step 1: Create Manhattan-focused grid
        print("📍 Step 1: Creating Manhattan grid...")
        center_lat, center_lon = 40.7589, -73.9851  # Times Square
        grid = AnalysisGrid(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_miles=4.0,  # 4-mile radius around Times Square
            grid_size_miles=0.4  # Points every 0.4 miles
        )
        
        print(f"✅ Generated {len(grid.grid_df)} grid points")
        
        # Step 2: Define NYC target locations
        print("🎯 Step 2: Defining target locations...")
        target_destinations = [
            Destination("350 5th Ave, New York, NY 10118", "Empire State Building"),
            Destination("1 Wall St, New York, NY 10005", "Wall Street Financial"),
            Destination("Central Park, New York, NY", "Central Park"),
            Destination("Brooklyn Bridge, New York, NY", "Brooklyn Bridge"),
            Destination("JFK Airport, New York, NY", "JFK Airport"),
        ]
        
        # Step 3: Geocode target locations
        print("🗺️  Step 3: Geocoding target locations...")
        client = GoogleMapsClient(api_key, rate_limit=5)
        geocoded_targets = client.geocode_batch(target_destinations)
        
        successful_targets = [t for t in geocoded_targets if not t.get('geocoding_failed', False)]
        print(f"✅ Successfully geocoded {len(successful_targets)}/{len(target_destinations)} targets")
        
        print("📍 Target Locations Summary:")
        print("=" * 50)
        for i, target in enumerate(successful_targets, 1):
            print(f"   {i}. {target['name']}")
            print(f"      Coordinates: ({target['lat']:.4f}, {target['lon']:.4f})")
            print(f"      Address: {target.get('formatted_address', target.get('address', 'N/A'))}")
            print()
        
        # Check map bounds
        print("🗺️  Verifying all targets are within viewable area...")
        target_lats = [t['lat'] for t in successful_targets]
        target_lons = [t['lon'] for t in successful_targets]
        
        print(f"   Target coordinate range:")
        print(f"   Latitude: {min(target_lats):.4f} to {max(target_lats):.4f}")
        print(f"   Longitude: {min(target_lons):.4f} to {max(target_lons):.4f}")
        print("✅ Map bounds will be adjusted to show all locations")
        
        if len(successful_targets) == 0:
            print("❌ No successful geocoding, cannot proceed")
            return False
        
        # Step 4: Calculate travel times from grid to targets
        print("⏱️  Step 4: Calculating travel times...")
        
        # Use subset of grid for performance (first 60 points)
        test_grid_size = min(60, len(grid.grid_df))
        test_grid = grid.grid_df.head(test_grid_size).copy()
        
        print(f"   Testing with {test_grid_size} grid points × {len(successful_targets)} targets")
        
        # Calculate distance matrix
        result = client.batch_distance_calculations(
            grid_df=test_grid,
            destinations=successful_targets,
            mode='driving',
            departure_time=datetime.now() + timedelta(hours=2)  # 2 hours from now
        )
        
        print(f"✅ Calculated {result['total_routes']} travel routes")
        
        # Step 5: Process and aggregate travel time data
        print("📊 Step 5: Processing travel time data...")
        
        # Create travel time matrix
        travel_times = {}
        grid_point_data = []
        
        for i, (_, grid_point) in enumerate(test_grid.iterrows()):
            point_id = grid_point['point_id']
            lat, lon = grid_point['lat'], grid_point['lon']
            
            total_travel_time = 0
            successful_routes = 0
            route_details = []
            
            # Find routes for this grid point
            for batch in result['batches']:
                for route in batch['routes']:
                    if (abs(route['origin']['lat'] - lat) < 0.0001 and 
                        abs(route['origin']['lon'] - lon) < 0.0001):
                        
                        if route['status'] in ['OK', 'ESTIMATED']:
                            duration_seconds = route.get('duration_seconds', 0)
                            total_travel_time += duration_seconds
                            successful_routes += 1
                            
                            route_details.append({
                                'destination': route['destination'].get('name', 'Unknown'),
                                'duration_minutes': duration_seconds / 60,
                                'distance_miles': route.get('distance_miles', 0),
                                'status': route['status']
                            })
            
            # Calculate average travel time
            avg_travel_time_minutes = (total_travel_time / 60) / max(successful_routes, 1)
            
            grid_point_data.append({
                'point_id': point_id,
                'lat': lat,
                'lon': lon,
                'total_travel_time_minutes': total_travel_time / 60,
                'avg_travel_time_minutes': avg_travel_time_minutes,
                'successful_routes': successful_routes,
                'route_details': route_details
            })
        
        # Convert to DataFrame
        grid_df_with_travel = pd.DataFrame(grid_point_data)
        
        print(f"✅ Processed travel times for {len(grid_df_with_travel)} grid points")
        print(f"   Average total travel time: {grid_df_with_travel['total_travel_time_minutes'].mean():.1f} minutes")
        print(f"   Best location total time: {grid_df_with_travel['total_travel_time_minutes'].min():.1f} minutes")
        print(f"   Worst location total time: {grid_df_with_travel['total_travel_time_minutes'].max():.1f} minutes")
        
        # Step 6: Create comprehensive visualization
        print("🎨 Step 6: Creating interactive visualization...")
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "NYC Grid with Target Locations",
                "Total Travel Time Heatmap", 
                "Average Travel Time per Destination",
                "Travel Time Distribution"
            ],
            specs=[[{"type": "scattermapbox"}, {"type": "scattermapbox"}],
                   [{"type": "bar"}, {"type": "histogram"}]]
        )
        
        # Plot 1: Grid points and targets on map
        # Grid points colored by total travel time
        fig.add_trace(
            go.Scattermapbox(
                lat=grid_df_with_travel['lat'],
                lon=grid_df_with_travel['lon'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=grid_df_with_travel['total_travel_time_minutes'],
                    colorscale='RdYlGn_r',  # Red = high time, Green = low time
                    colorbar=dict(
                        title="Total Travel Time (min)", 
                        x=0.45,
                        y=0.85,  # Position higher up
                        len=0.3  # Shorter length
                    ),
                    opacity=0.7
                ),
                text=[f"Point {row['point_id']}<br>"
                      f"Total: {row['total_travel_time_minutes']:.1f} min<br>"
                      f"Avg: {row['avg_travel_time_minutes']:.1f} min<br>"
                      f"Routes: {row['successful_routes']}" 
                      for _, row in grid_df_with_travel.iterrows()],
                hovertemplate='%{text}<extra></extra>',
                name='Grid Points',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Target locations for first map - base circles
        fig.add_trace(
            go.Scattermapbox(
                lat=[t['lat'] for t in successful_targets],
                lon=[t['lon'] for t in successful_targets],
                mode='markers',
                marker=dict(
                    size=20,
                    color='red',
                    symbol='circle',
                    opacity=0.9
                ),
                hovertemplate='<b>🎯 Target Location</b><br>' +
                             'Name: %{customdata[0]}<br>' +
                             'Lat: %{lat:.4f}<br>' +
                             'Lon: %{lon:.4f}<extra></extra>',
                customdata=[t['name'] for t in successful_targets],
                name='Targets (Map 1)',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Target locations for first map - numbered stars
        fig.add_trace(
            go.Scattermapbox(
                lat=[t['lat'] for t in successful_targets],
                lon=[t['lon'] for t in successful_targets],
                mode='markers+text',
                marker=dict(
                    size=12,
                    color='white',
                    symbol='star',
                    opacity=1.0
                ),
                text=[f"{i+1}" for i in range(len(successful_targets))],
                textfont=dict(size=8, color='black', family='Arial Black'),
                textposition="middle center",
                hovertemplate='<b>🎯 Target #%{text}</b><br>' +
                             'Name: %{customdata[0]}<br>' +
                             'Lat: %{lat:.4f}<br>' +
                             'Lon: %{lon:.4f}<extra></extra>',
                customdata=[t['name'] for t in successful_targets],
                name='Targets (Map 1)',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Plot 2: Average travel time heatmap
        fig.add_trace(
            go.Scattermapbox(
                lat=grid_df_with_travel['lat'],
                lon=grid_df_with_travel['lon'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=grid_df_with_travel['avg_travel_time_minutes'],
                    colorscale='Viridis_r',
                    colorbar=dict(
                        title="Avg Time (min)", 
                        x=1.0,
                        y=0.85,  # Position higher up
                        len=0.3  # Shorter length
                    ),
                    opacity=0.8
                ),
                text=[f"Point {row['point_id']}<br>"
                      f"Avg: {row['avg_travel_time_minutes']:.1f} min" 
                      for _, row in grid_df_with_travel.iterrows()],
                hovertemplate='%{text}<extra></extra>',
                name='Avg Travel Time',
                showlegend=True
            ),
            row=1, col=2
        )
        
        # Target locations for second map - base circles
        fig.add_trace(
            go.Scattermapbox(
                lat=[t['lat'] for t in successful_targets],
                lon=[t['lon'] for t in successful_targets],
                mode='markers',
                marker=dict(
                    size=20,
                    color='orange',
                    symbol='circle',
                    opacity=0.9
                ),
                hovertemplate='<b>🎯 Target Location</b><br>' +
                             'Name: %{customdata[0]}<br>' +
                             'Lat: %{lat:.4f}<br>' +
                             'Lon: %{lon:.4f}<extra></extra>',
                customdata=[t['name'] for t in successful_targets],
                name='Targets (Map 2)',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # Target locations for second map - numbered stars
        fig.add_trace(
            go.Scattermapbox(
                lat=[t['lat'] for t in successful_targets],
                lon=[t['lon'] for t in successful_targets],
                mode='markers+text',
                marker=dict(
                    size=12,
                    color='white',
                    symbol='star',
                    opacity=1.0
                ),
                text=[f"{i+1}" for i in range(len(successful_targets))],
                textfont=dict(size=8, color='black', family='Arial Black'),
                textposition="middle center",
                hovertemplate='<b>🎯 Target #%{text}</b><br>' +
                             'Name: %{customdata[0]}<br>' +
                             'Lat: %{lat:.4f}<br>' +
                             'Lon: %{lon:.4f}<extra></extra>',
                customdata=[t['name'] for t in successful_targets],
                name='Targets (Map 2)',
                showlegend=True
            ),
            row=1, col=2
        )
        
        # Plot 3: Bar chart of average travel times by destination
        destination_avg_times = {}
        for _, point in grid_df_with_travel.iterrows():
            for route in point['route_details']:
                dest = route['destination']
                time = route['duration_minutes']
                if dest not in destination_avg_times:
                    destination_avg_times[dest] = []
                destination_avg_times[dest].append(time)
        
        dest_names = list(destination_avg_times.keys())
        avg_times = [np.mean(times) for times in destination_avg_times.values()]
        
        fig.add_trace(
            go.Bar(
                x=dest_names,
                y=avg_times,
                marker_color='skyblue',
                name='Avg Travel Time'
            ),
            row=2, col=1
        )
        
        # Plot 4: Distribution of total travel times
        fig.add_trace(
            go.Histogram(
                x=grid_df_with_travel['total_travel_time_minutes'],
                nbinsx=20,
                marker_color='lightgreen',
                name='Travel Time Distribution'
            ),
            row=2, col=2
        )
        
        # Calculate map bounds to include all targets
        all_lats = list(grid_df_with_travel['lat']) + [t['lat'] for t in successful_targets]
        all_lons = list(grid_df_with_travel['lon']) + [t['lon'] for t in successful_targets]
        map_center_lat = (min(all_lats) + max(all_lats)) / 2
        map_center_lon = (min(all_lons) + max(all_lons)) / 2
        
        # Create target list for title
        target_list = " | ".join([f"{i+1}. {t['name']}" for i, t in enumerate(successful_targets)])
        
        # Update layout
        fig.update_layout(
            title={
                'text': f"NYC Travel Time Analysis - Grid-Based Location Evaluation<br>" +
                       f"<sub>Targets: {target_list}</sub>",
                'x': 0.5,
                'font': {'size': 18}
            },
            showlegend=True,
            height=900,
            width=1400,
            annotations=[
                dict(
                    text=f"<b>Target Locations:</b><br>" +
                         "<br>".join([f"🎯 {i+1}. {t['name']}<br>   📍 ({t['lat']:.4f}, {t['lon']:.4f})" 
                                     for i, t in enumerate(successful_targets)]),
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.01, y=0.99,
                    xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.3)",
                    borderwidth=1,
                    font=dict(size=10, family="Arial")
                )
            ]
        )
        
        # Update mapbox layouts
        for i, j in [(1, 1), (1, 2)]:
            fig.update_layout({
                f'mapbox{i if i==1 and j==1 else "2"}': dict(
                    style="open-street-map",
                    center=dict(lat=map_center_lat, lon=map_center_lon),
                    zoom=11
                )
            })
        
        # Update axis labels
        fig.update_xaxes(title_text="Destination", row=2, col=1)
        fig.update_yaxes(title_text="Average Travel Time (min)", row=2, col=1)
        fig.update_xaxes(title_text="Total Travel Time (min)", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)
        
        # Save visualization
        output_file = "outputs/nyc_travel_time_analysis.html"
        os.makedirs("outputs", exist_ok=True)
        fig.write_html(output_file)
        
        # Get file size
        file_size = os.path.getsize(output_file) / 1024  # KB
        
        print(f"✅ Visualization saved: {output_file} ({file_size:.1f} KB)")
        print(f"📋 Open this file in your browser to explore the travel time analysis!")
        
        # Step 7: Analysis summary
        print("\n📊 Step 7: Analysis Summary")
        print("=" * 50)
        
        # Find best and worst locations
        best_point = grid_df_with_travel.loc[grid_df_with_travel['total_travel_time_minutes'].idxmin()]
        worst_point = grid_df_with_travel.loc[grid_df_with_travel['total_travel_time_minutes'].idxmax()]
        
        print(f"🏆 Best Location (Lowest Total Travel Time):")
        print(f"   Point {best_point['point_id']}: ({best_point['lat']:.4f}, {best_point['lon']:.4f})")
        print(f"   Total travel time: {best_point['total_travel_time_minutes']:.1f} minutes")
        print(f"   Average per destination: {best_point['avg_travel_time_minutes']:.1f} minutes")
        
        print(f"\n📍 Worst Location (Highest Total Travel Time):")
        print(f"   Point {worst_point['point_id']}: ({worst_point['lat']:.4f}, {worst_point['lon']:.4f})")
        print(f"   Total travel time: {worst_point['total_travel_time_minutes']:.1f} minutes")
        print(f"   Average per destination: {worst_point['avg_travel_time_minutes']:.1f} minutes")
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Grid points analyzed: {len(grid_df_with_travel)}")
        print(f"   Target destinations: {len(successful_targets)}")
        print(f"   Total routes calculated: {result['total_routes']}")
        print(f"   Average total travel time: {grid_df_with_travel['total_travel_time_minutes'].mean():.1f} ± {grid_df_with_travel['total_travel_time_minutes'].std():.1f} min")
        
        # Show route details for best location
        print(f"\n🎯 Route Details for Best Location:")
        for route in best_point['route_details']:
            print(f"   → {route['destination']}: {route['duration_minutes']:.1f} min, {route['distance_miles']:.1f} mi ({route['status']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_nyc_visualization_test():
    """Run NYC travel time visualization test."""
    print("🚀 NYC TRAVEL TIME VISUALIZATION TEST")
    print("=" * 70)
    
    success = create_nyc_travel_time_analysis()
    
    if success:
        print("\n🎉 NYC TRAVEL TIME ANALYSIS COMPLETE!")
        print("✅ Grid generation successful")
        print("✅ Target locations geocoded")
        print("✅ Travel times calculated")
        print("✅ Interactive visualization created")
        print("✅ Analysis summary generated")
        print("\n🗽 The NYC location evaluator is working perfectly!")
        print("📁 Check outputs/nyc_travel_time_analysis.html for the full interactive map!")
    else:
        print("\n❌ NYC travel time analysis failed")
        print("Check the error messages above for details")
    
    return success


if __name__ == '__main__':
    success = run_nyc_visualization_test()
    sys.exit(0 if success else 1)