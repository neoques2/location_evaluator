#!/usr/bin/env python3
"""
Debug Google Maps Distance Matrix API
Investigate why API calls are failing with INVALID_REQUEST
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

def debug_distance_matrix_api():
    """Debug Distance Matrix API issues step by step."""
    print("🔍 GOOGLE MAPS DISTANCE MATRIX API DEBUG")
    print("=" * 60)
    
    try:
        # Get API key
        def get_api_key_from_config():
            try:
                from src.config_parser import ConfigParser
                parser = ConfigParser()
                config = parser.load_config('config')
                return config.get('apis', {}).get('google_maps', {}).get('api_key')
            except Exception:
                return None
        
        api_key = get_api_key_from_config()
        if not api_key:
            print("❌ No API key found")
            return False
        
        print(f"✅ API key found: {api_key[:10]}...")
        
        # Test 1: Simple manual API call
        print("\n📍 Test 1: Manual Distance Matrix API Call")
        print("-" * 40)
        
        # Simple coordinates
        origin_lat, origin_lon = 32.7767, -96.7970  # Dallas downtown
        dest_lat, dest_lon = 33.0216577, -96.6979973  # Plano (from geocoding cache)
        
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': f"{origin_lat},{origin_lon}",
            'destinations': f"{dest_lat},{dest_lon}",
            'mode': 'driving',
            'key': api_key,
            'units': 'imperial'
        }
        
        print(f"   URL: {url}")
        print(f"   Origins: {params['origins']}")
        print(f"   Destinations: {params['destinations']}")
        print(f"   Mode: {params['mode']}")
        print(f"   Units: {params['units']}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"   HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   API Status: {data.get('status', 'UNKNOWN')}")
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                if data.get('status') == 'OK' and data.get('rows'):
                    element = data['rows'][0]['elements'][0]
                    print(f"   Element Status: {element.get('status', 'UNKNOWN')}")
                    if element.get('status') == 'OK':
                        print(f"   ✅ SUCCESS: {element['distance']['text']}, {element['duration']['text']}")
                    else:
                        print(f"   ❌ Element Error: {element}")
                else:
                    print(f"   ❌ API Error: {data}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        # Test 2: Test with departure time
        print("\n📍 Test 2: Distance Matrix with Departure Time")
        print("-" * 40)
        
        departure_time = datetime.now().replace(hour=19, minute=30, second=0) + timedelta(days=1)
        params_with_time = params.copy()
        params_with_time.update({
            'departure_time': int(departure_time.timestamp()),
            'traffic_model': 'best_guess'
        })
        
        print(f"   Departure time: {departure_time}")
        print(f"   Timestamp: {params_with_time['departure_time']}")
        
        try:
            response = requests.get(url, params=params_with_time, timeout=10)
            print(f"   HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   API Status: {data.get('status', 'UNKNOWN')}")
                
                if data.get('status') == 'OK' and data.get('rows'):
                    element = data['rows'][0]['elements'][0]
                    print(f"   Element Status: {element.get('status', 'UNKNOWN')}")
                    if element.get('status') == 'OK':
                        print(f"   ✅ SUCCESS with traffic: {element['duration_in_traffic']['text']}")
                    else:
                        print(f"   ❌ Element Error: {element}")
                else:
                    print(f"   ❌ API Error: {data}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        # Test 3: Test GoogleMapsClient
        print("\n📍 Test 3: GoogleMapsClient Implementation")
        print("-" * 40)
        
        from src.apis.google_maps import GoogleMapsClient
        
        client = GoogleMapsClient(api_key, rate_limit=5)
        
        origins = [{'lat': origin_lat, 'lon': origin_lon}]
        destinations = [{'lat': dest_lat, 'lon': dest_lon}]
        
        print(f"   Origins: {origins}")
        print(f"   Destinations: {destinations}")
        
        result = client.calculate_distance_matrix(
            origins=origins,
            destinations=destinations,
            mode='driving',
            departure_time=departure_time
        )
        
        print(f"   Result status: {result.get('status', 'UNKNOWN')}")
        print(f"   Number of routes: {len(result.get('routes', []))}")
        
        if result.get('routes'):
            route = result['routes'][0]
            print(f"   Route status: {route.get('status', 'UNKNOWN')}")
            if route.get('status') == 'OK':
                print(f"   ✅ SUCCESS: {route.get('distance_miles', 0):.1f} miles, {route.get('duration_seconds', 0)} seconds")
            else:
                print(f"   ❌ Route error: {route}")
        
        # Test 4: Test with multiple origins/destinations
        print("\n📍 Test 4: Multiple Origins/Destinations")
        print("-" * 40)
        
        # Test with grid points like in Dallas analysis
        from src.core.grid_generator import AnalysisGrid
        
        grid = AnalysisGrid(
            center_lat=32.7767,
            center_lon=-96.7970,
            radius_miles=2.0,
            grid_size_miles=1.0
        )
        
        test_grid = grid.grid_df.head(3)  # Just 3 points
        test_origins = [{'lat': row['lat'], 'lon': row['lon']} for _, row in test_grid.iterrows()]
        test_destinations = [{'lat': dest_lat, 'lon': dest_lon}]
        
        print(f"   Test origins: {len(test_origins)}")
        print(f"   Test destinations: {len(test_destinations)}")
        
        result = client.calculate_distance_matrix(
            origins=test_origins,
            destinations=test_destinations,
            mode='driving',
            departure_time=departure_time
        )
        
        print(f"   Result status: {result.get('status', 'UNKNOWN')}")
        print(f"   Number of routes: {len(result.get('routes', []))}")
        
        success_count = sum(1 for route in result.get('routes', []) if route.get('status') == 'OK')
        print(f"   Successful routes: {success_count}/{len(result.get('routes', []))}")
        
        # Test 5: Check API quotas and usage
        print("\n📍 Test 5: API Quota Information")
        print("-" * 40)
        print("   Check your Google Cloud Console for:")
        print("   - Distance Matrix API is enabled")
        print("   - API key has proper permissions")
        print("   - No quota limits exceeded")
        print("   - Billing account is active")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_distance_matrix_api()
    sys.exit(0 if success else 1)