#!/usr/bin/env python3
"""
Test Geocoding Functionality
Tests the Google Maps geocoding implementation with mock and real data.
"""

import sys
import os
from pathlib import Path

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


def test_geocoding_mock():
    """Test geocoding with mock API responses."""
    print("🗺️  Testing Geocoding (Mock Mode)")
    print("=" * 50)
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        from src.config_parser import ConfigParser
        
        # Load sample destinations from config
        parser = ConfigParser()
        config = parser.load_config('config')
        
        # Extract destinations from config
        destinations = []
        for category, dest_list in config['destinations'].items():
            for dest in dest_list:
                destinations.append(Destination(
                    address=dest['address'],
                    name=dest['name']
                ))
        
        print(f"Found {len(destinations)} destinations to test:")
        for i, dest in enumerate(destinations):
            print(f"  {i+1}. {dest.name}: {dest.address}")
        
        # Test with invalid API key (should handle gracefully)
        print(f"\n🔧 Testing with mock/invalid API key...")
        
        try:
            client = GoogleMapsClient("MOCK_API_KEY_FOR_TESTING")
            
            # This should fail gracefully and use default coordinates
            geocoded = client.geocode_batch(destinations)
            
            print(f"✅ Geocoding completed (mock mode)")
            print(f"✅ Processed {len(geocoded)} destinations")
            
            # Check results
            failed_count = sum(1 for d in geocoded if d.get('geocoding_failed', False))
            success_count = len(geocoded) - failed_count
            
            print(f"✅ Results: {success_count} successful, {failed_count} failed (expected in mock mode)")
            
            # Show sample results
            print(f"\n📍 Sample geocoding results:")
            for i, result in enumerate(geocoded[:3]):
                status = "❌ Failed" if result.get('geocoding_failed', False) else "✅ Success"
                print(f"  {i+1}. {result['name']}: {result['lat']:.4f}, {result['lon']:.4f} {status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Mock geocoding test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def test_geocoding_with_config_key():
    """Test geocoding with API key from config."""
    print("\n🔑 Testing Geocoding (Real API Key)")
    print("=" * 50)
    
    api_key = get_api_key_from_config()
    
    if not api_key:
        print("⚠️  No API key found in config")
        print("   Check config/api.yaml for Google Maps API key")
        print("   For now, testing with dummy key...")
        api_key = "AIzaSyDummyKeyForTestingPurposes1234567890"
    elif api_key.startswith('AIzaSyDummy'):
        print("⚠️  Dummy API key found in config")
        print("   Replace with real Google Maps API key in config/api.yaml")
        print("   For now, testing with dummy key...")
    else:
        print(f"✅ Real API key found in config: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from src.apis.google_maps import GoogleMapsClient, Destination
        
        # Test with simple, well-known addresses
        test_destinations = [
            Destination("1600 Amphitheatre Parkway, Mountain View, CA", "Google HQ"),
            Destination("350 Fifth Avenue, New York, NY", "Empire State Building"),
            Destination("Invalid Address That Should Fail", "Invalid Location")
        ]
        
        print(f"Testing with {len(test_destinations)} well-known addresses:")
        for dest in test_destinations:
            print(f"  - {dest.name}: {dest.address}")
        
        client = GoogleMapsClient(api_key, rate_limit=1)  # Slow rate for testing
        
        print(f"\n🔄 Making API calls...")
        geocoded = client.geocode_batch(test_destinations)
        
        print(f"✅ API calls completed")
        
        # Analyze results
        failed_count = sum(1 for d in geocoded if d.get('geocoding_failed', False))
        success_count = len(geocoded) - failed_count
        
        print(f"✅ Results: {success_count} successful, {failed_count} failed")
        
        # Show detailed results
        print(f"\n📍 Detailed results:")
        for i, result in enumerate(geocoded):
            status = "❌ Failed" if result.get('geocoding_failed', False) else "✅ Success"
            formatted_addr = result.get('formatted_address', 'N/A')
            print(f"  {i+1}. {result['name']}: {result['lat']:.4f}, {result['lon']:.4f} {status}")
            if not result.get('geocoding_failed', False):
                print(f"      Formatted: {formatted_addr}")
        
        # Check if we got reasonable coordinates for known locations
        if success_count > 0:
            print(f"\n✅ Geocoding appears to be working correctly!")
            return True
        else:
            print(f"\n⚠️  All geocoding failed - may indicate API key issues")
            return False
        
    except Exception as e:
        print(f"❌ Real API test failed: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n⏱️  Testing Rate Limiting")
    print("=" * 50)
    
    try:
        from src.apis.rate_limiter import RateLimiter
        import time
        
        print("Testing rate limiter with 2 requests per second...")
        
        rate_limiter = RateLimiter(requests_per_second=2)
        
        # Make several rapid requests
        start_time = time.time()
        for i in range(4):
            print(f"  Request {i+1}...")
            rate_limiter.wait_if_needed()
        
        total_time = time.time() - start_time
        expected_min_time = 1.5  # Should take at least 1.5 seconds for 4 requests at 2/sec
        
        print(f"✅ Completed 4 requests in {total_time:.2f} seconds")
        
        if total_time >= expected_min_time:
            print(f"✅ Rate limiting working correctly (min expected: {expected_min_time:.1f}s)")
            return True
        else:
            print(f"⚠️  Rate limiting may not be working (expected at least {expected_min_time:.1f}s)")
            return False
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False


def run_all_geocoding_tests():
    """Run all geocoding tests."""
    print("🚀 GEOCODING AND API INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Mock Geocoding", test_geocoding_mock),
        ("Real API Geocoding", test_geocoding_with_config_key),
        ("Rate Limiting", test_rate_limiting),
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
    print("📊 GEOCODING TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL GEOCODING TESTS PASSED!")
        print("✅ Mock geocoding working")
        print("✅ API integration framework working")
        print("✅ Rate limiting working")
        
        api_key = get_api_key_from_config()
        if api_key and not api_key.startswith('AIzaSyDummy'):
            print("✅ Real API calls working (API key in config)")
        else:
            print("⚠️  Real API calls not tested (no valid API key)")
            print("   Add real Google Maps API key to config/api.yaml")
        
        print("\n🚀 Ready to implement Distance Matrix API!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please check the output above for details")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_geocoding_tests()
    sys.exit(0 if success else 1)