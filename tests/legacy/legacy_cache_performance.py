#!/usr/bin/env python3
"""
Test Caching Performance
Demonstrates the performance improvement from caching API calls.
"""

import time
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_cache_performance():
    """Test caching performance with a small subset of Dallas analysis."""
    print("🚀 CACHING PERFORMANCE TEST")
    print("=" * 50)
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.apis.cache import get_cache_stats
        from src.core.grid_generator import AnalysisGrid
        
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
        
        # Create small test grid
        print("📍 Creating small test grid...")
        grid = AnalysisGrid(
            center_lat=32.7767,
            center_lon=-96.7970,
            radius_miles=5.0,
            grid_size_miles=2.0  # Larger spacing for fewer points
        )
        
        # Take just first 10 points for testing
        test_grid = grid.grid_df.head(10).copy()
        print(f"   Test grid: {len(test_grid)} points")
        
        # Test destinations
        destinations = [
            Destination("Movement Climbing Gym Plano, TX", "Movement Plano"),
            Destination("Movement Climbing Gym Design District, Dallas, TX", "Movement Design District"),
        ]
        
        client = GoogleMapsClient(api_key, rate_limit=5)
        
        # Test 1: Geocoding performance
        print("\n📍 Testing geocoding performance...")
        
        # First run - should hit API
        start_time = time.time()
        geocoded_targets = client.geocode_batch(destinations)
        first_run_time = time.time() - start_time
        print(f"   First run (API calls): {first_run_time:.2f} seconds")
        
        # Second run - should use cache
        start_time = time.time()
        geocoded_targets = client.geocode_batch(destinations)
        second_run_time = time.time() - start_time
        print(f"   Second run (cached): {second_run_time:.2f} seconds")
        print(f"   Geocoding speedup: {first_run_time/second_run_time:.1f}x faster")
        
        # Test 2: Distance matrix performance
        print("\n🚗 Testing distance matrix performance...")
        
        if len(geocoded_targets) > 0:
            # First run - should hit API
            start_time = time.time()
            result1 = client.batch_distance_calculations(
                grid_df=test_grid,
                destinations=geocoded_targets,
                mode='driving',
                departure_time=datetime.now().replace(hour=19, minute=30)
            )
            first_matrix_time = time.time() - start_time
            print(f"   First run (API calls): {first_matrix_time:.2f} seconds")
            
            # Second run - should use cache
            start_time = time.time()
            result2 = client.batch_distance_calculations(
                grid_df=test_grid,
                destinations=geocoded_targets,
                mode='driving',
                departure_time=datetime.now().replace(hour=19, minute=30)
            )
            second_matrix_time = time.time() - start_time
            print(f"   Second run (cached): {second_matrix_time:.2f} seconds")
            print(f"   Distance matrix speedup: {first_matrix_time/second_matrix_time:.1f}x faster")
            
            # Show cache stats
            print("\n📊 Cache Statistics:")
            stats = get_cache_stats()
            print(f"   Cache files: {stats['valid_files']} valid, {stats['expired_files']} expired")
            print(f"   Cache size: {stats['total_size_mb']} MB")
        
        print("\n✅ Cache performance test complete!")
        print("🎉 Subsequent runs will be much faster thanks to caching!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_cache_performance()
    sys.exit(0 if success else 1)