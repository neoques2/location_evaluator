#!/usr/bin/env python3
"""
Dallas Area Travel Time Analysis
Grid analysis between Addison and Plano with specific target locations and schedules.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def get_api_key_from_config():
    """Get API key from config."""
    try:
        from src.config_parser import ConfigParser

        parser = ConfigParser()
        config = parser.load_config("config")
        return config.get("apis", {}).get("google_maps", {}).get("api_key")
    except Exception:
        return None


def create_dallas_travel_analysis():
    """Create Dallas area travel time analysis with specific targets and schedules."""
    print("🏙️  Dallas Area Travel Time Analysis")
    print("=" * 70)

    api_key = get_api_key_from_config()
    if not api_key:
        print("❌ No API key found in config")
        return False

    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.core.grid_generator import AnalysisGrid
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Step 1: Define expanded Dallas metro area grid
        print("📍 Step 1: Creating expanded Dallas metro area grid...")

        # Dallas city center coordinates for broader coverage
        dallas_center_lat, dallas_center_lon = 32.7767, -96.7970  # Downtown Dallas

        print(
            f"   Grid center: ({dallas_center_lat:.4f}, {dallas_center_lon:.4f}) - Downtown Dallas"
        )
        print(f"   Coverage: Expanded Dallas metro area")

        # Create much larger grid covering greater Dallas area
        grid = AnalysisGrid(
            center_lat=dallas_center_lat,
            center_lon=dallas_center_lon,
            radius_miles=25.0,  # 25-mile radius covers most of Dallas metro
            grid_size_miles=1.0,  # Points every 1 mile for broader coverage
        )

        print(f"✅ Generated {len(grid.grid_df)} grid points")

        # Step 2: Define target locations with specific addresses
        print("🎯 Step 2: Setting up Dallas target locations...")
        target_destinations = [
            # Arts venues
            Destination(
                "Sammons Center for the Arts, Dallas, TX", "Sammons Center for the Arts"
            ),
            Destination("Sons of Hermann Hall, Dallas, TX", "Sons of Hermann Hall"),
            # Climbing gyms
            Destination("525 Talbert Dr, Plano, TX 75093", "Movement Plano"),
            Destination("The Hill Climbing Gym, Dallas, TX", "The Hill Climbing"),
            Destination(
                "Movement Climbing Gym Design District, Dallas, TX",
                "Movement Design District",
            ),
        ]

        # Step 3: Geocode target locations
        print("🗺️  Step 3: Geocoding Dallas target locations...")
        client = GoogleMapsClient(api_key, rate_limit=5)
        geocoded_targets = client.geocode_batch(target_destinations)

        successful_targets = [
            t for t in geocoded_targets if not t.get("geocoding_failed", False)
        ]
        print(
            f"✅ Successfully geocoded {len(successful_targets)}/{len(target_destinations)} targets"
        )

        print("📍 Dallas Target Locations Summary:")
        print("=" * 60)
        for i, target in enumerate(successful_targets, 1):
            print(f"   {i}. {target['name']}")
            print(f"      Coordinates: ({target['lat']:.4f}, {target['lon']:.4f})")
            print(
                f"      Address: {target.get('formatted_address', target.get('address', 'N/A'))}"
            )
            print()

        if len(successful_targets) == 0:
            print("❌ No successful geocoding, cannot proceed")
            return False

        # Step 4: Define schedule requirements
        print("⏰ Step 4: Analyzing schedule requirements...")

        # Define the weekly schedule (corrected climbing gym frequency)
        schedule_requirements = [
            {
                "location": "Sammons Center for the Arts",
                "day": "Saturday",
                "time": "21:00",  # 9 PM
                "end_time": "23:30",  # 11:30 PM
                "frequency": "weekly",
                "description": "Saturday night arts events",
            },
            {
                "location": "Sons of Hermann Hall",
                "day": "Wednesday",
                "time": "21:00",  # 9 PM
                "end_time": "23:30",  # 11:30 PM
                "frequency": "weekly",
                "description": "Wednesday night events",
            },
            {
                "location": "Movement Plano",
                "day": "Weekday",
                "time": "19:30",  # 7:30 PM
                "end_time": "22:00",  # 10 PM
                "frequency": "1x_weekly",
                "description": "Climbing session (1x per week)",
            },
            {
                "location": "The Hill Climbing",
                "day": "Weekday",
                "time": "19:30",  # 7:30 PM
                "end_time": "22:00",  # 10 PM
                "frequency": "1x_weekly",
                "description": "Climbing session (1x per week)",
            },
            {
                "location": "Movement Design District",
                "day": "Weekend",
                "time": "19:30",  # 7:30 PM
                "end_time": "22:00",  # 10 PM
                "frequency": "2x_weekly",
                "description": "Climbing sessions (2x per week - weekend)",
            },
            {
                "location": "Movement Design District",
                "day": "Sunday",
                "time": "12:00",  # Noon
                "end_time": "14:00",  # 2 PM (estimated)
                "frequency": "weekly",
                "description": "Sunday noon session",
            },
        ]

        print("📅 Weekly Schedule Summary:")
        print("=" * 40)
        for req in schedule_requirements:
            print(f"   • {req['location']}")
            print(
                f"     {req['day']} {req['time']}-{req['end_time']} ({req['frequency']})"
            )
            print(f"     {req['description']}")
            print()

        # Step 5: Calculate travel times from grid to targets
        print("🚗 Step 5: Calculating travel times...")

        # Use the full grid - no sampling needed
        test_grid = grid.grid_df.copy()

        print(
            f"   Analyzing {len(test_grid)} grid points × {len(successful_targets)} targets across expanded Dallas metro"
        )
        print(
            f"   Coverage: Downtown to suburbs (Plano, Frisco, Arlington, Richardson, etc.)"
        )

        # Calculate distance matrix for evening schedule (7:30 PM weekday)
        weekday_evening = datetime.now().replace(
            hour=19, minute=30, second=0
        ) + timedelta(days=1)

        result = client.batch_distance_calculations(
            grid_df=test_grid,
            destinations=successful_targets,
            mode="driving",
            departure_time=weekday_evening,
        )

        print(f"✅ Calculated {result['total_routes']} travel routes")

        # Step 6: Process travel time data with schedule weighting
        print("📊 Step 6: Processing travel times with schedule weighting...")

        # Create weighted travel time analysis
        grid_point_data = []

        for i, (_, grid_point) in enumerate(test_grid.iterrows()):
            point_id = grid_point["point_id"]
            lat, lon = grid_point["lat"], grid_point["lon"]

            # Find routes for this grid point
            point_routes = {}
            for batch in result["batches"]:
                for route in batch["routes"]:
                    if (
                        abs(route["origin"]["lat"] - lat) < 0.0001
                        and abs(route["origin"]["lon"] - lon) < 0.0001
                    ):

                        dest_name = route["destination"].get("name", "Unknown")
                        if route["status"] in ["OK", "ESTIMATED"]:
                            point_routes[dest_name] = {
                                "duration_minutes": route.get("duration_seconds", 0)
                                / 60,
                                "distance_miles": route.get("distance_miles", 0),
                                "status": route["status"],
                            }

            # Calculate weighted score based on schedule frequency
            total_weekly_travel_time = 0
            route_details = []

            # Weight the travel times by frequency
            for target in successful_targets:
                target_name = target["name"]
                if target_name in point_routes:
                    travel_time = point_routes[target_name]["duration_minutes"]
                    distance = point_routes[target_name]["distance_miles"]

                    # Apply corrected frequency weights
                    if "Sammons Center" in target_name:
                        weekly_time = travel_time * 1  # 1x per week
                        freq_desc = "1x/week (Sat)"
                    elif "Sons of Hermann" in target_name:
                        weekly_time = travel_time * 1  # 1x per week
                        freq_desc = "1x/week (Wed)"
                    elif "Movement Plano" in target_name:
                        weekly_time = travel_time * 1  # 1x per week
                        freq_desc = "1x/week"
                    elif "Hill" in target_name:
                        weekly_time = travel_time * 1  # 1x per week
                        freq_desc = "1x/week"
                    elif "Movement Design District" in target_name:
                        weekly_time = travel_time * 1  # 1x Sunday
                        freq_desc = "1x/week"
                    else:
                        weekly_time = travel_time
                        freq_desc = "1x/week"

                    total_weekly_travel_time += weekly_time
                    route_details.append(
                        {
                            "destination": target_name,
                            "travel_time": travel_time,
                            "weekly_time": weekly_time,
                            "distance": distance,
                            "frequency": freq_desc,
                            "status": point_routes[target_name]["status"],
                        }
                    )

            grid_point_data.append(
                {
                    "point_id": point_id,
                    "lat": lat,
                    "lon": lon,
                    "total_weekly_travel_time": total_weekly_travel_time,
                    "avg_trip_time": total_weekly_travel_time
                    / max(len(route_details), 1),
                    "route_details": route_details,
                    "successful_routes": len(route_details),
                }
            )

        # Convert to DataFrame
        grid_df_dallas = pd.DataFrame(grid_point_data)

        print(f"✅ Processed travel times for {len(grid_df_dallas)} grid points")
        print(
            f"   Average weekly travel time: {grid_df_dallas['total_weekly_travel_time'].mean():.1f} minutes"
        )
        print(
            f"   Best location weekly time: {grid_df_dallas['total_weekly_travel_time'].min():.1f} minutes"
        )
        print(
            f"   Worst location weekly time: {grid_df_dallas['total_weekly_travel_time'].max():.1f} minutes"
        )

        # Helper function for target schedule info
        def get_target_schedule(target_name):
            """Get schedule summary for target location."""
            if "Sammons Center" in target_name:
                return "Sat 9-11:30 PM"
            elif "Sons of Hermann" in target_name:
                return "Wed 9-11:30 PM"
            elif "Movement Plano" in target_name:
                return "1x/week 7:30-10 PM"
            elif "Hill" in target_name:
                return "1x/week 7:30-10 PM"
            elif "Movement Design District" in target_name:
                return "1x/week"
            else:
                return "Custom schedule"

        # Step 7: Create Dallas visualization
        print("🎨 Step 7: Creating Dallas area interactive visualization...")

        # Calculate map bounds
        all_lats = list(grid_df_dallas["lat"]) + [t["lat"] for t in successful_targets]
        all_lons = list(grid_df_dallas["lon"]) + [t["lon"] for t in successful_targets]
        map_center_lat = (min(all_lats) + max(all_lats)) / 2
        map_center_lon = (min(all_lons) + max(all_lons)) / 2

        # Create main map figure (full size)
        fig = go.Figure()
        radius_mult = 5
        fig.add_trace(
            go.Densitymapbox(
                lat=grid_df_dallas["lat"],
                lon=grid_df_dallas["lon"],
                z=grid_df_dallas["total_weekly_travel_time"],
                radius=25 * 1.5,
                zmin=grid_df_dallas["total_weekly_travel_time"].min(),
                zmax=grid_df_dallas["total_weekly_travel_time"].max() / 2.5,
                colorscale="RdYlGn_r",
                opacity=0.4,
                showscale=False,
            )
        )

        # 2️⃣  Sample grid points
        fig.add_trace(
            go.Scattermapbox(
                lat=grid_df_dallas["lat"],
                lon=grid_df_dallas["lon"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=grid_df_dallas["total_weekly_travel_time"],
                    colorscale="RdYlGn_r",
                    colorbar=dict(
                        title="Weekly travel time (min)", thickness=15, len=0.7
                    ),
                    opacity=0.8,
                ),
                text=[
                    f"<b>Grid {r.point_id}</b><br>"
                    f"📍 ({r.lat:.4f}, {r.lon:.4f})<br>"
                    f"🕐 {r.total_weekly_travel_time:.1f} min<br>"
                    f"📊 Avg trip {r.avg_trip_time:.1f} min<br>"
                    f"🚗 Routes: {r.successful_routes}"
                    for r in grid_df_dallas.itertuples()
                ],
                hovertemplate="%{text}<extra></extra>",
                name="Grid points",
            )
        )
        fig.add_trace(
            go.Scattermapbox(
                lat=[t["lat"] for t in successful_targets],
                lon=[t["lon"] for t in successful_targets],
                mode="markers+text",
                marker=dict(size=28, color="red", symbol="star"),
                text=[str(i + 1) for i in range(len(successful_targets))],
                textfont=dict(size=12, color="white", family="Arial Black"),
                textposition="middle center",
                name="Dallas targets",
            )
        )

        # 4️⃣  Tell Mapbox what to show
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",  # any Mapbox style you like
                center=dict(
                    lat=grid_df_dallas["lat"].mean(), lon=grid_df_dallas["lon"].mean()
                ),
                zoom=10,
            ),
            margin=dict(l=0, r=0, t=40, b=0),
        )

        # Configure main map layout
        target_list = " | ".join(
            [
                f"{i+1}. {t['name'].replace('Movement ', 'Mvmt ')}"
                for i, t in enumerate(successful_targets)
            ]
        )

        fig.update_layout(
            title={
                "text": f"Dallas Metro Travel Time Analysis - Interactive Map<br>"
                + f"<sub>25-Mile Coverage | Targets: {target_list}</sub>",
                "x": 0.5,
                "font": {"size": 20},
            },
            map=dict(
                style="open-street-map",
                center=dict(lat=map_center_lat, lon=map_center_lon),
                zoom=9,  # Good zoom level for Dallas metro area
            ),
            height=800,  # Full height for better viewing
            width=1400,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.3)",
                borderwidth=1,
            ),
            annotations=[
                dict(
                    text=f"<b>🎯 Dallas Targets:</b><br>"
                    + "<br>".join(
                        [
                            f"{i+1}. {t['name']}<br>   📍 ({t['lat']:.4f}, {t['lon']:.4f})"
                            for i, t in enumerate(successful_targets)
                        ]
                    )
                    + "<br><br><b>📅 Weekly Schedule:</b><br>"
                    + "• Sammons Center: Sat 9-11:30 PM<br>"
                    + "• Sons Hermann: Wed 9-11:30 PM<br>"
                    + "• Movement Plano: 1x/week 7:30-10 PM<br>"
                    + "• The Hill: 1x/week 7:30-10 PM<br>"
                    + "• Design District: 2x weekend + Sun 12 PM",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.99,
                    y=0.01,
                    xanchor="right",
                    yanchor="bottom",
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.3)",
                    borderwidth=1,
                    font=dict(size=10, family="Arial"),
                )
            ],
        )

        # Create supporting plots figure
        supporting_fig = make_subplots(
            rows=1,
            cols=3,
            subplot_titles=[
                "Average Trip Time Distribution",
                "Weekly Schedule Impact by Destination",
                "Distance vs Travel Time Relationship",
            ],
            specs=[[{"type": "histogram"}, {"type": "bar"}, {"type": "scatter"}]],
            horizontal_spacing=0.1,
        )

        # Plot 1: Histogram of average trip times
        supporting_fig.add_trace(
            go.Histogram(
                x=grid_df_dallas["avg_trip_time"],
                nbinsx=20,
                marker_color="lightblue",
                name="Trip Time Distribution",
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        # Plot 2: Bar chart showing weekly schedule impact
        location_weekly_times = {}
        for _, point in grid_df_dallas.iterrows():
            for route in point["route_details"]:
                dest = route["destination"]
                weekly_time = route["weekly_time"]
                if dest not in location_weekly_times:
                    location_weekly_times[dest] = []
                location_weekly_times[dest].append(weekly_time)

        dest_names = [
            name.replace("Movement ", "Mvmt ").replace("Climbing", "Climb")
            for name in location_weekly_times.keys()
        ]
        avg_weekly_times = [np.mean(times) for times in location_weekly_times.values()]

        supporting_fig.add_trace(
            go.Bar(
                x=dest_names,
                y=avg_weekly_times,
                marker_color="orange",
                name="Avg Weekly Time",
                showlegend=False,
            ),
            row=1,
            col=2,
        )

        # Plot 3: Distance vs Time scatter
        distances = []
        times = []
        destinations_scatter = []
        for _, point in grid_df_dallas.iterrows():
            for route in point["route_details"]:
                distances.append(route["distance"])
                times.append(route["travel_time"])
                destinations_scatter.append(
                    route["destination"].replace("Movement ", "Mvmt ")
                )

        supporting_fig.add_trace(
            go.Scatter(
                x=distances,
                y=times,
                mode="markers",
                marker=dict(color=distances, colorscale="Viridis", opacity=0.7, size=6),
                text=destinations_scatter,
                hovertemplate="<b>%{text}</b><br>Distance: %{x:.1f} mi<br>Time: %{y:.1f} min<extra></extra>",
                name="Routes",
                showlegend=False,
            ),
            row=1,
            col=3,
        )

        # Configure supporting plots layout
        supporting_fig.update_layout(
            title={
                "text": "Dallas Metro Analysis - Supporting Data Visualizations",
                "x": 0.5,
                "font": {"size": 16},
            },
            height=500,
            width=1400,
            showlegend=False,
        )

        # Update axis labels for supporting plots
        supporting_fig.update_xaxes(title_text="Average Trip Time (min)", row=1, col=1)
        supporting_fig.update_yaxes(title_text="Frequency", row=1, col=1)
        supporting_fig.update_xaxes(title_text="Destination", row=1, col=2)
        supporting_fig.update_yaxes(title_text="Avg Weekly Time (min)", row=1, col=2)
        supporting_fig.update_xaxes(title_text="Distance (miles)", row=1, col=3)
        supporting_fig.update_yaxes(title_text="Travel Time (min)", row=1, col=3)

        # Save visualizations
        os.makedirs("outputs", exist_ok=True)

        # Save main map
        main_map_file = "outputs/dallas_travel_map.html"
        fig.write_html(main_map_file)
        main_file_size = os.path.getsize(main_map_file) / 1024
        print(
            f"✅ Dallas interactive map saved: {main_map_file} ({main_file_size:.1f} KB)"
        )

        # Save supporting plots
        supporting_plots_file = "outputs/dallas_supporting_plots.html"
        supporting_fig.write_html(supporting_plots_file)
        supporting_file_size = os.path.getsize(supporting_plots_file) / 1024
        print(
            f"✅ Supporting plots saved: {supporting_plots_file} ({supporting_file_size:.1f} KB)"
        )

        # Create combined HTML file that shows both
        combined_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dallas Metro Travel Time Analysis</title>
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
    </style>
</head>
<body>
    <div class="header">
        <h1>🏙️ Dallas Metro Area Travel Time Analysis</h1>
        <p><strong>Interactive Location Optimization for Weekly Commute Schedule</strong></p>
    </div>
    
    <div class="description">
        <h3>📍 Analysis Overview</h3>
        <p>This analysis evaluates <strong>{len(grid_df_dallas):,} potential residential locations</strong> across the Dallas metro area (25-mile radius) based on weekly travel time to <strong>{len(successful_targets)} target destinations</strong>.</p>
        
        <h4>🎯 Target Destinations:</h4>
        <ul>
        {"".join([f"<li><strong>{i+1}. {t['name']}</strong> - ({t['lat']:.4f}, {t['lon']:.4f})</li>" for i, t in enumerate(successful_targets)])}
        </ul>
        
        <h4>📅 Weekly Schedule:</h4>
        <ul>
            <li><strong>Sammons Center for the Arts:</strong> Saturday 9:00-11:30 PM</li>
            <li><strong>Sons of Hermann Hall:</strong> Wednesday 9:00-11:30 PM</li>
            <li><strong>Movement Plano:</strong> 1x/week, 7:30-10:00 PM</li>
            <li><strong>The Hill Climbing:</strong> 1x/week, 7:30-10:00 PM</li>
            <li><strong>Movement Design District:</strong> 3x/week (2x weekend + Sunday noon)</li>
        </ul>
        
        <p><strong>🏆 Best Location:</strong> Grid point with <strong>{grid_df_dallas['total_weekly_travel_time'].min():.1f} minutes</strong> total weekly travel time.<br>
        <strong>📊 Average:</strong> {grid_df_dallas['total_weekly_travel_time'].mean():.1f} ± {grid_df_dallas['total_weekly_travel_time'].std():.1f} minutes across all locations.</p>
    </div>
    
    <div class="map-section">
        <h2>🗺️ Interactive Map View</h2>
        <p><em>Zoom in/out and click on points for detailed information. Red markers show target destinations, colored grid points show travel time optimization.</em></p>
        <iframe src="dallas_travel_map.html" width="100%" height="850" frameborder="0"></iframe>
    </div>
    
    <div class="plots-section">
        <h2>📊 Supporting Data Analysis</h2>
        <p><em>Additional charts showing travel time distributions, schedule impact, and distance relationships.</em></p>
        <iframe src="dallas_supporting_plots.html" width="100%" height="550" frameborder="0"></iframe>
    </div>
    
    <div class="description">
        <h3>💡 How to Use This Analysis</h3>
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

        combined_file = "outputs/dallas_travel_analysis.html"
        with open(combined_file, "w") as f:
            f.write(combined_html)

        combined_file_size = os.path.getsize(combined_file) / 1024
        print(
            f"✅ Combined analysis saved: {combined_file} ({combined_file_size:.1f} KB)"
        )

        # Step 8: Analysis summary
        print("\n📊 Step 8: Dallas Analysis Summary")
        print("=" * 60)

        # Find best and worst locations
        best_point = grid_df_dallas.loc[
            grid_df_dallas["total_weekly_travel_time"].idxmin()
        ]
        worst_point = grid_df_dallas.loc[
            grid_df_dallas["total_weekly_travel_time"].idxmax()
        ]

        print(f"🏆 Best Location (Lowest Weekly Travel Time):")
        print(
            f"   Point {best_point['point_id']}: ({best_point['lat']:.4f}, {best_point['lon']:.4f})"
        )
        print(
            f"   Total weekly travel time: {best_point['total_weekly_travel_time']:.1f} minutes"
        )
        print(f"   Average trip time: {best_point['avg_trip_time']:.1f} minutes")

        print(f"\n📍 Worst Location (Highest Weekly Travel Time):")
        print(
            f"   Point {worst_point['point_id']}: ({worst_point['lat']:.4f}, {worst_point['lon']:.4f})"
        )
        print(
            f"   Total weekly travel time: {worst_point['total_weekly_travel_time']:.1f} minutes"
        )
        print(f"   Average trip time: {worst_point['avg_trip_time']:.1f} minutes")

        print(f"\n📈 Overall Statistics:")
        print(f"   Grid points analyzed: {len(grid_df_dallas)}")
        print(f"   Target destinations: {len(successful_targets)}")
        print(f"   Total routes calculated: {result['total_routes']}")
        print(
            f"   Average weekly travel time: {grid_df_dallas['total_weekly_travel_time'].mean():.1f} ± {grid_df_dallas['total_weekly_travel_time'].std():.1f} min"
        )

        # Show route details for best location
        print(f"\n🎯 Weekly Schedule Details for Best Location:")
        for route in best_point["route_details"]:
            print(
                f"   → {route['destination']}: {route['travel_time']:.1f} min/trip × {route['frequency']} = {route['weekly_time']:.1f} min/week"
            )

        return True

    except Exception as e:
        print(f"❌ Dallas analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_dallas_analysis_test():
    """Run Dallas area travel time analysis."""
    print("🚀 DALLAS AREA TRAVEL TIME ANALYSIS")
    print("=" * 70)

    success = create_dallas_travel_analysis()

    if success:
        print("\n🎉 DALLAS METRO ANALYSIS COMPLETE!")
        print("✅ 25-mile radius Dallas metro grid generated")
        print("✅ Target locations geocoded")
        print("✅ Schedule-weighted travel times calculated")
        print("✅ Interactive visualization created")
        print("✅ Best locations identified across metro area")
        print("\n🏙️  Your expanded Dallas location evaluator is ready!")
        print("📁 Check outputs/dallas_travel_analysis.html for the interactive map!")
        print(
            "🌍 Coverage includes: Downtown, Plano, Frisco, Arlington, Richardson, and more!"
        )
    else:
        print("\n❌ Dallas analysis failed")
        print("Check the error messages above for details")

    return success


if __name__ == "__main__":
    success = run_dallas_analysis_test()
    sys.exit(0 if success else 1)
