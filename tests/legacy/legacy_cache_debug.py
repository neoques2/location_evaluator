#!/usr/bin/env python3
"""
Debug Cache Issues
"""

import sys
import os
sys.path.insert(0, 'src')

def test_cache_debug():
    """Test cache with debug output."""
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.core.grid_generator import AnalysisGrid
        from datetime import datetime
        
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
        grid = AnalysisGrid(
            center_lat=32.7767,
            center_lon=-96.7970,
            radius_miles=2.0,
            grid_size_miles=1.0
        )
        
        # Take just first 2 points for testing
        test_grid = grid.grid_df.head(2).copy()
        print(f"Test grid: {len(test_grid)} points")
        
        # Test with one destination
        destinations = [
            Destination("Movement Climbing Gym Plano, TX", "Movement Plano")
        ]
        
        client = GoogleMapsClient(api_key, rate_limit=5)
        
        # Geocode first
        geocoded = client.geocode_batch(destinations)
        print(f"Geocoded: {len(geocoded)} destinations")
        
        if geocoded:
            print("Testing distance matrix...")
            
            # Test distance matrix
            result = client.batch_distance_calculations(
                grid_df=test_grid,
                destinations=geocoded,
                mode='driving',
                departure_time=datetime.now().replace(hour=19, minute=30)
            )
            
            print(f"Result status: {result.get('total_routes')} routes")
            print(f"Batches: {len(result.get('batches', []))}")
            
            if result.get('batches'):
                batch = result['batches'][0]
                print(f"First batch status: {batch.get('status')}")
                if batch.get('routes'):
                    route = batch['routes'][0]
                    print(f"First route: {route.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_cache_debug()