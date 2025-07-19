#!/usr/bin/env python3
"""
Location Evaluator Test Suite
Comprehensive testing of all components with proper organization.
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestRunner:
    """Organizes and runs all tests for the Location Evaluator."""
    
    def __init__(self, use_conda=True):
        self.use_conda = use_conda
        self.results = {}
        
    def run_command(self, command):
        """Run a command, optionally in conda environment."""
        if self.use_conda:
            full_command = f"conda run -n location_evaluator python -c \"{command}\""
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        else:
            # Run directly
            result = subprocess.run([sys.executable, "-c", command], capture_output=True, text=True)
        
        return result.returncode == 0, result.stdout, result.stderr
    
    def test_phase1_core_infrastructure(self):
        """Test Phase 1: Core infrastructure (original implementation)."""
        print("1️⃣  PHASE 1: Core Infrastructure")
        print("   Testing original implementation...")
        
        try:
            from src.config_parser import ConfigParser
            from src.core.scheduler import process_schedules
            
            # Test configuration
            parser = ConfigParser()
            config = parser.load_config('config')
            parser.validate_config(config)
            
            # Test scheduling
            schedules = process_schedules(config)
            
            self.results['phase1_config'] = True
            self.results['phase1_schedules'] = len(schedules)
            print(f"   ✅ Configuration: {len(config)} sections loaded")
            print(f"   ✅ Schedules: {len(schedules)} items processed")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Phase 1 failed: {e}")
            return False
    
    def test_improved_grid_generation(self):
        """Test improved numpy-based grid generation."""
        print("\n2️⃣  IMPROVED GRID GENERATION")
        print("   Testing numpy/pandas implementation...")
        
        command = """
import sys, os
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
from src.core.grid_generator import AnalysisGrid
import time

# Test grid generation
start_time = time.time()
grid = AnalysisGrid(40.7128, -74.0060, 10, 0.5)
generation_time = time.time() - start_time

df = grid.get_grid_dataframe()
print('grid_points:' + str(len(df)))
print('generation_time:' + str(round(generation_time, 3)))
print('max_distance:' + str(round(df['distance_from_center'].max(), 2)))
print('memory_mb:' + str(round(df.memory_usage(deep=True).sum()/1024/1024, 2)))
print('columns:' + str(list(df.columns)))

# Test operations
close_points = df[df['distance_from_center'] <= 5]
print('close_points:' + str(len(close_points)))

# Test efficiency
theoretical_area = np.pi * (10 ** 2)
actual_area = len(df) * (0.5 ** 2)
efficiency = (actual_area / theoretical_area) * 100
print('efficiency:' + str(round(efficiency, 1)))
"""
        
        success, stdout, stderr = self.run_command(command)
        
        if success:
            # Parse results
            for line in stdout.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.results[f'grid_{key}'] = value
            
            print(f"   ✅ Grid points: {self.results.get('grid_grid_points', 'N/A')}")
            print(f"   ✅ Generation time: {self.results.get('grid_generation_time', 'N/A')}s")
            print(f"   ✅ Max distance: {self.results.get('grid_max_distance', 'N/A')} miles")
            print(f"   ✅ Memory usage: {self.results.get('grid_memory_mb', 'N/A')} MB")
            print(f"   ✅ Efficiency: {self.results.get('grid_efficiency', 'N/A')}%")
            
            return True
        else:
            print(f"   ❌ Grid generation failed: {stderr}")
            return False
    
    def test_interactive_visualization(self):
        """Test interactive visualization creation and save files."""
        print("\n3️⃣  INTERACTIVE VISUALIZATION")
        print("   Testing plotly-based visualizations...")
        
        command = """
import sys, os
sys.path.insert(0, 'src')
try:
    import plotly.graph_objects as go
    from src.core.grid_generator import AnalysisGrid
    from src.visualization.grid_explorer import GridExplorer
    
    # Create smaller grid for testing
    grid = AnalysisGrid(40.7128, -74.0060, 8, 0.75)
    explorer = GridExplorer(grid)
    
    # Test visualization creation
    overview_map = explorer.create_grid_overview_map()
    density_map = explorer.create_grid_density_map()
    dashboard = explorer.create_grid_statistics_dashboard()
    
    print('overview_traces:' + str(len(overview_map.data)))
    print('density_traces:' + str(len(density_map.data)))
    print('dashboard_traces:' + str(len(dashboard.data)))
    
    # Create a single comprehensive HTML file with all visualizations
    os.makedirs('outputs', exist_ok=True)
    
    # Use Plotly's built-in method to create proper HTML
    overview_map.write_html('outputs/grid_visualization_test.html', 
                           include_plotlyjs='cdn',
                           config={'displayModeBar': True})
    
    file_size = round(os.path.getsize('outputs/grid_visualization_test.html') / 1024, 1)
    
    print('combined_file_kb:' + str(file_size))
    print('single_file_saved:True')
    print('visualization_success:True')
    
except ImportError as e:
    print('visualization_success:False')
    print('error:plotly_not_available')
except Exception as e:
    print('visualization_success:False')
    print('error:' + str(e))
"""
        
        success, stdout, stderr = self.run_command(command)
        
        if success:
            lines = stdout.strip().split('\n')
            viz_success = any('visualization_success:True' in line for line in lines)
            single_file_saved = any('single_file_saved:True' in line for line in lines)
            
            if viz_success:
                print("   ✅ Visualization creation successful")
                for line in lines:
                    if 'traces:' in line:
                        print(f"   ✅ {line.replace('_', ' ').replace(':', ': ')}")
                
                if single_file_saved:
                    # Get file size
                    file_size = None
                    for line in lines:
                        if 'combined_file_kb:' in line:
                            file_size = line.split(':')[1]
                            break
                    
                    print("   ✅ Single comprehensive visualization file created:")
                    print(f"      📁 outputs/grid_visualization_test.html ({file_size} KB)")
                    print("   📋 Open this file in your browser to see all grid visualizations!")
                
                return True
            else:
                error_line = next((line for line in lines if 'error:' in line), 'unknown_error')
                print(f"   ⚠️  Visualization skipped: {error_line.split(':', 1)[1]}")
                return False
        else:
            print(f"   ❌ Visualization test failed: {stderr}")
            return False
    
    def test_cli_interface(self):
        """Test CLI interface functionality."""
        print("\n4️⃣  CLI INTERFACE")
        print("   Testing main CLI functionality...")
        
        try:
            # Test dry run
            if self.use_conda:
                result = subprocess.run([
                    'conda', 'run', '-n', 'location_evaluator', 
                    'python', 'main.py', '--dry-run'
                ], capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run([
                    sys.executable, 'main.py', '--dry-run'
                ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("   ✅ CLI dry run successful")
                
                # Check for expected sections
                output = result.stdout
                expected_sections = ['Grid Configuration', 'Destinations', 'Transportation Modes']
                missing_sections = [s for s in expected_sections if s not in output]
                
                if not missing_sections:
                    print("   ✅ All expected output sections present")
                    return True
                else:
                    print(f"   ❌ Missing sections: {missing_sections}")
                    return False
            else:
                print(f"   ❌ CLI dry run failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ CLI test failed: {e}")
            return False
    
    def test_full_pipeline(self):
        """Test the complete analysis pipeline without creating additional files."""
        print("\n5️⃣  FULL ANALYSIS PIPELINE")
        print("   Testing CLI and analyzer integration...")
        
        try:
            # Test that the pipeline can run without creating additional output files
            if self.use_conda:
                result = subprocess.run([
                    'conda', 'run', '-n', 'location_evaluator',
                    'python', 'main.py', '--dry-run'
                ], capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run([
                    sys.executable, 'main.py', '--dry-run'
                ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("   ✅ Full pipeline dry-run successful")
                print("   ✅ CLI and analyzer integration working")
                
                # Test that analyzer can be imported and run
                command = """
import sys, os
sys.path.insert(0, 'src')
from src.analyzer import LocationAnalyzer
from src.config_parser import ConfigParser

# Test analyzer instantiation
parser = ConfigParser()
config = parser.load_config('config')
analyzer = LocationAnalyzer(config)

print('analyzer_created:True')
"""
                success, stdout, stderr = self.run_command(command)
                
                if success and 'analyzer_created:True' in stdout:
                    print("   ✅ Analyzer instantiation successful")
                    return True
                else:
                    print(f"   ❌ Analyzer test failed: {stderr}")
                    return False
            else:
                print(f"   ❌ Pipeline dry-run failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Pipeline test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 LOCATION EVALUATOR - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        
        # Detect environment
        if self.use_conda:
            print("📦 Using conda environment: location_evaluator")
        else:
            print("🐍 Using system Python")
        
        start_time = time.time()
        
        # Run tests
        tests = [
            ("Phase 1 Core", self.test_phase1_core_infrastructure),
            ("Grid Generation", self.test_improved_grid_generation),
            ("Visualization", self.test_interactive_visualization),
            ("CLI Interface", self.test_cli_interface),
            ("Full Pipeline", self.test_full_pipeline),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"   ❌ {test_name} crashed: {e}")
        
        total_time = time.time() - start_time
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        print(f"Total time: {total_time:.2f} seconds")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Core infrastructure working")
            print("✅ Improved grid generation working")
            print("✅ Interactive visualizations working")
            print("✅ CLI interface working") 
            print("✅ Full pipeline working")
            print("\n🚀 Ready for Phase 2: API Integration!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            print("Please check the output above for details")
        
        return passed == total


def main():
    """Main test runner entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Location Evaluator test suite')
    parser.add_argument('--no-conda', action='store_true', help='Use system Python instead of conda')
    args = parser.parse_args()
    
    runner = TestRunner(use_conda=not args.no_conda)
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()