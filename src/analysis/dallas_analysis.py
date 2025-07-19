"""
Refactored Dallas Analysis Module
Clean, modular implementation of Dallas travel time analysis.
"""
import sys
import os
from pathlib import Path
from typing import Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.grid_analysis import GridAnalyzer
from src.analysis.visualization import AnalysisVisualizer
from src.analysis.html_generator import HTMLReportGenerator
from src.analysis.dallas_targets import DallasAnalysisRunner
from src.analysis.constants import AnalysisConstants


def get_api_key_from_config() -> Optional[str]:
    """Get API key from configuration."""
    try:
        from src.config_parser import ConfigParser
        parser = ConfigParser()
        config = parser.load_config("config")
        return config.get("apis", {}).get("google_maps", {}).get("api_key")
    except Exception:
        return None


def create_dallas_travel_analysis() -> bool:
    """
    Create Dallas area travel time analysis with refactored modular approach.
    
    Returns:
        bool: True if analysis completed successfully, False otherwise.
    """
    # Print header
    DallasAnalysisRunner.print_analysis_header()
    
    # Get API key
    api_key = get_api_key_from_config()
    if not api_key:
        print(f"{AnalysisConstants.ERROR_EMOJI} No API key found in config")
        return False
    
    try:
        # Get Dallas analysis setup
        config, target_locations, schedule_info = DallasAnalysisRunner.get_complete_dallas_setup()
        
        # Print schedule summary
        from src.analysis.dallas_targets import DallasTargetDefinitions
        DallasTargetDefinitions.print_schedule_summary()
        
        # Initialize components
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Initializing analysis components...")
        grid_analyzer = GridAnalyzer(api_key, rate_limit=5)
        visualizer = AnalysisVisualizer()
        html_generator = HTMLReportGenerator()
        
        # Run complete analysis
        print(f"{AnalysisConstants.ANALYSIS_EMOJI} Running complete grid analysis...")
        analysis_result = grid_analyzer.run_full_analysis(config, target_locations)
        
        # Create visualizations
        print(f"{AnalysisConstants.ART_EMOJI} Creating interactive visualizations...")
        main_figure, supporting_figure = visualizer.create_complete_visualization(
            analysis_result, schedule_info
        )
        
        # Generate HTML report
        print(f"{AnalysisConstants.MAP_EMOJI} Generating HTML report...")
        report_path = html_generator.create_complete_report(
            analysis_result=analysis_result,
            schedule_info=schedule_info,
            main_figure=main_figure,
            supporting_figure=supporting_figure,
            report_prefix="dallas_travel"
        )
        
        # Print analysis summary
        html_generator.print_analysis_summary(analysis_result)
        
        # Success message
        print(f"\n{AnalysisConstants.SUCCESS_EMOJI} DALLAS METRO ANALYSIS COMPLETE!")
        print(f"{AnalysisConstants.SUCCESS_EMOJI} 25-mile radius Dallas metro grid generated")
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Target locations geocoded")
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Schedule-weighted travel times calculated")
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Interactive visualization created")
        print(f"{AnalysisConstants.SUCCESS_EMOJI} Best locations identified across metro area")
        print(f"\n{AnalysisConstants.MAP_EMOJI} Your Dallas location evaluator is ready!")
        print(f"📁 Check {report_path} for the complete interactive analysis!")
        print(f"🌍 Coverage includes: Downtown, Plano, Frisco, Arlington, Richardson, and more!")
        
        return True
        
    except Exception as e:
        print(f"{AnalysisConstants.ERROR_EMOJI} Dallas analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_dallas_analysis_test() -> bool:
    """
    Run Dallas area travel time analysis test.
    
    Returns:
        bool: True if analysis completed successfully, False otherwise.
    """
    print(f"🚀 DALLAS AREA TRAVEL TIME ANALYSIS")
    print("=" * 70)
    
    success = create_dallas_travel_analysis()
    
    if not success:
        print(f"\n{AnalysisConstants.ERROR_EMOJI} Dallas analysis failed")
        print("Check the error messages above for details")
    
    return success


if __name__ == "__main__":
    success = run_dallas_analysis_test()
    sys.exit(0 if success else 1)