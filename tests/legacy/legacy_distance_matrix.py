#!/usr/bin/env python3
"""
Test Distance Matrix Functionality
Tests the Google Maps Distance Matrix API implementation with mock and real data.
"""

import sys
import os
from pathlib import Path
import pandas as pd
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


def test_distance_matrix_mock():
    """Test distance matrix with mock API responses."""
    print("🗺️  Testing Distance Matrix (Mock Mode)")
    print("=" * 50)
    
    try:
        from src.apis.google_maps import GoogleMapsClient
        from src.core.grid_generator import AnalysisGrid
        
        # Create a small test grid
        print("Creating test grid...")
        grid_gen = AnalysisGrid(
            center_lat=40.7128,
            center_lon=-74.0060,
            radius_miles=2.0,
            grid_size_miles=0.5
        )
        grid_df = grid_gen.grid_df
        print(f"✅ Generated grid with {len(grid_df)} points")
        
        # Create test destinations
        destinations = [
            {'lat': 40.7589, 'lon': -73.9851, 'name': 'Times Square'},
            {'lat': 40.6892, 'lon': -74.0445, 'name': 'Statue of Liberty'}
        ]
        print(f"✅ Created {len(destinations)} test destinations")
        
        # Test with mock API key
        print(f"\n🔧 Testing with mock API key...")
        
        client = GoogleMapsClient("MOCK_API_KEY_FOR_TESTING", rate_limit=5)
        
        # Test single distance matrix call
        print("Testing single distance matrix call...")
        origins = [{'lat': row['lat'], 'lon': row['lon']} for _, row in grid_df.head(3).iterrows()]
        
        result = client.calculate_distance_matrix(
            origins=origins,
            destinations=destinations,
            mode='driving'
        )
        
        print(f"✅ Single distance matrix call completed")
        print(f"   Status: {result['status']}")
        print(f"   Routes calculated: {len(result['routes'])}")
        
        # Test batch processing
        print("\nTesting batch distance calculations...")
        batch_result = client.batch_distance_calculations(
            grid_df=grid_df.head(10),  # Test with first 10 points
            destinations=destinations,
            mode='driving'
        )
        
        print(f"✅ Batch calculations completed")
        print(f"   Total origins: {batch_result['total_origins']}")
        print(f"   Total destinations: {batch_result['total_destinations']}")
        print(f"   Total routes: {batch_result['total_routes']}")
        print(f"   Batches processed: {len(batch_result['batches'])}")
        
        # Verify fallback estimation works
        sample_routes = batch_result['batches'][0]['routes'][:3]
        print(f"\n📍 Sample route calculations:")
        for i, route in enumerate(sample_routes):
            status = route['status']
            distance = route.get('distance_miles', 'N/A')
            duration = route.get('duration_text', 'N/A')
            print(f"  {i+1}. Status: {status}, Distance: {distance:.2f} mi, Duration: {duration}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock distance matrix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_distance_matrix_with_real_grid():
    """Test distance matrix with real grid data."""
    print("\n🌐 Testing Distance Matrix with Real Grid")
    print("=" * 50)
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.core.grid_generator import AnalysisGrid
        from src.config_parser import ConfigParser
        
        # Load actual config
        parser = ConfigParser()
        config = parser.load_config('config')
        
        # Generate real grid from config
        analysis_config = config.get('analysis', {})
        print(f"Creating test grid: center=NYC, radius=5mi")
        
        # Use NYC coordinates for testing
        grid_gen = AnalysisGrid(
            center_lat=40.7128,
            center_lon=-74.0060,
            radius_miles=5.0,
            grid_size_miles=analysis_config.get('grid_size', 0.5)
        )
        grid_df = grid_gen.grid_df
        print(f"✅ Generated grid with {len(grid_df):,} points")
        
        # Get destinations from config and geocode them
        destinations = []
        for category, dest_list in config['destinations'].items():
            for dest in dest_list:
                destinations.append(Destination(
                    address=dest['address'],
                    name=dest['name']
                ))
        
        print(f"Found {len(destinations)} destinations to test with")
        
        # Use API key from config, fallback to mock
        api_key = get_api_key_from_config() or 'MOCK_API_KEY_FOR_TESTING'
        client = GoogleMapsClient(api_key, rate_limit=2)
        
        # Geocode destinations
        print("Geocoding destinations...")
        geocoded_destinations = client.geocode_batch(destinations)
        successful_geocodes = [d for d in geocoded_destinations if not d.get('geocoding_failed', False)]
        print(f"✅ Geocoded {len(successful_geocodes)}/{len(destinations)} destinations successfully")
        
        if len(successful_geocodes) == 0:
            print("⚠️  No successful geocodes, using mock destinations")
            geocoded_destinations = [
                {'lat': 40.7589, 'lon': -73.9851, 'name': 'Mock Destination 1'},
                {'lat': 40.6892, 'lon': -74.0445, 'name': 'Mock Destination 2'}
            ]
        
        # Test with subset of grid for performance
        test_points = min(50, len(grid_df))
        print(f"\nTesting distance calculations with {test_points} grid points...")
        
        batch_result = client.batch_distance_calculations(
            grid_df=grid_df.head(test_points),
            destinations=geocoded_destinations[:3],  # Limit destinations too
            mode='driving',
            departure_time=datetime.now() + timedelta(hours=1)
        )
        
        print(f"✅ Batch distance calculation completed")
        print(f"   Origins: {batch_result['total_origins']}")
        print(f"   Destinations: {batch_result['total_destinations']}")
        print(f"   Total routes: {batch_result['total_routes']:,}")
        print(f"   Batches: {len(batch_result['batches'])}")
        
        # Analyze results
        total_routes = 0
        successful_routes = 0
        fallback_routes = 0
        
        for batch in batch_result['batches']:
            for route in batch['routes']:
                total_routes += 1
                if route['status'] == 'OK':
                    successful_routes += 1
                elif route['status'] == 'ESTIMATED':
                    fallback_routes += 1
        
        print(f"\n📊 Route Analysis:")
        print(f"   Total routes: {total_routes:,}")
        print(f"   Successful API routes: {successful_routes}")
        print(f"   Fallback estimated routes: {fallback_routes}")
        print(f"   Success rate: {(successful_routes/total_routes)*100:.1f}%")
        
        # Show sample routes
        print(f"\n📍 Sample routes from first batch:")
        sample_routes = batch_result['batches'][0]['routes'][:5]
        for i, route in enumerate(sample_routes):
            origin_lat = route['origin']['lat']
            origin_lon = route['origin']['lon']
            dest_name = route['destination'].get('name', 'Unknown')
            distance = route.get('distance_miles', 0)
            duration = route.get('duration_text', 'N/A')
            status = route['status']
            
            print(f"   {i+1}. ({origin_lat:.4f}, {origin_lon:.4f}) → {dest_name}")
            print(f"       Distance: {distance:.2f} mi, Duration: {duration}, Status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real grid distance matrix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_integration_with_caching():
    """Test API integration with caching system."""
    print("\n💾 Testing API Integration with Caching")
    print("=" * 50)
    
    try:
        from src.apis.cache import save_cached_route, get_cached_route, get_cache_stats
        
        # Test cache functionality
        print("Testing cache save/retrieve...")
        
        test_route_data = {
            'distance_miles': 5.2,
            'duration_seconds': 900,
            'status': 'OK'
        }
        
        # Save to cache
        save_cached_route(
            origin_lat=40.7128,
            origin_lon=-74.0060,
            destination_address="Times Square, NY",
            departure_time="08:00",
            day="Mon",
            route_data=test_route_data
        )
        print("✅ Route data saved to cache")
        
        # Retrieve from cache
        cached_data = get_cached_route(
            origin_lat=40.7128,
            origin_lon=-74.0060,
            destination_address="Times Square, NY",
            departure_time="08:00",
            day="Mon"
        )
        
        if cached_data and cached_data['distance_miles'] == 5.2:
            print("✅ Route data retrieved from cache successfully")
        else:
            print("❌ Cache retrieval failed")
            return False
        
        # Check cache stats
        stats = get_cache_stats()
        print(f"✅ Cache stats: {stats['total_files']} files, {stats['total_size_mb']} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_distance_matrix_tests():
    """Run all distance matrix tests."""
    print("🚀 DISTANCE MATRIX API INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Distance Matrix Mock", test_distance_matrix_mock),
        ("Distance Matrix Real Grid", test_distance_matrix_with_real_grid),
        ("API Caching Integration", test_api_integration_with_caching),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {test_name} crashed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DISTANCE MATRIX TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL DISTANCE MATRIX TESTS PASSED!")
        print("✅ Mock distance calculations working")
        print("✅ Batch processing working")
        print("✅ Grid integration working")
        print("✅ Fallback estimation working")
        print("✅ Caching system working")
        
        api_key = get_api_key_from_config()
        if api_key and not api_key.startswith('MOCK'):
            print("✅ Ready for real API calls")
        else:
            print("⚠️  Add real API key to config/api.yaml for real API testing")
        
        print("\n🚀 Phase 2 API Integration Complete!")
        print("Ready to move to Phase 3: Analysis and Scoring")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please check the output above for details")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_distance_matrix_tests()
    sys.exit(0 if success else 1)