#!/usr/bin/env python3
"""
Location Evaluator - Main CLI Entry Point
Analyzes residential location desirability based on commute patterns, travel costs, and safety metrics.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.config_parser import ConfigParser, ConfigValidationError
from src.analyzer import LocationAnalyzer


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Location Evaluator - Analyze residential location desirability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --config config/analysis.yaml --output outputs/analysis.html
  python main.py --grid-size 0.3 --max-radius 20 --verbose
  python main.py --dry-run --config config/analysis.yaml
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config",
        help="Path to configuration directory or single config file (default: config/)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/analysis.html",
        help="Output path for HTML visualization (default: outputs/analysis.html)",
    )

    parser.add_argument(
        "--grid-size", type=float, help="Override grid size from config (miles)"
    )

    parser.add_argument(
        "--max-radius", type=float, help="Override max radius from config (miles)"
    )

    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Use only cached data, don't make API calls",
    )

    parser.add_argument(
        "--force-refresh", action="store_true", help="Force refresh of all cached data"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose logging output"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and show analysis plan without execution",
    )

    return parser.parse_args()


def ensure_directories() -> None:
    """Ensure data and output directories exist."""
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("outputs").mkdir(parents=True, exist_ok=True)


def validate_config_overrides(args: argparse.Namespace) -> None:
    """Validate command line configuration overrides."""
    if args.grid_size is not None:
        if not (0.1 <= args.grid_size <= 2.0):
            raise ValueError("Grid size must be between 0.1 and 2.0 miles")

    if args.max_radius is not None:
        if not (5 <= args.max_radius <= 50):
            raise ValueError("Max radius must be between 5 and 50 miles")


def load_configuration(args: argparse.Namespace) -> Dict[str, Any]:
    """Load and validate configuration from files."""
    try:
        config_parser = ConfigParser()
        config = config_parser.load_config(args.config)

        # Apply command line overrides
        if args.grid_size is not None:
            config["analysis"]["grid_size"] = args.grid_size

        if args.max_radius is not None:
            config["analysis"]["max_radius"] = args.max_radius

        # Validate complete configuration
        config_parser.validate_config(config)

        return config

    except ConfigValidationError as e:
        logging.error(f"Configuration validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)


def show_analysis_plan(config: Dict[str, Any], output_path: str) -> None:
    """Display the analysis plan without executing."""
    print("\n" + "=" * 60)
    print("LOCATION EVALUATOR - ANALYSIS PLAN")
    print("=" * 60)

    # Grid configuration
    analysis_config = config["analysis"]
    print(f"\nGrid Configuration:")
    print(f"  Center Point: {analysis_config['center_point']}")
    print(f"  Grid Size: {analysis_config['grid_size']} miles")
    print(f"  Max Radius: {analysis_config['max_radius']} miles")

    # Estimate grid points
    import math

    estimated_points = (
        math.pi * (analysis_config["max_radius"] / analysis_config["grid_size"]) ** 2
    )
    print(f"  Estimated Grid Points: ~{int(estimated_points):,}")

    # Destinations summary
    total_destinations = sum(len(dests) for dests in config["destinations"].values())
    print(f"\nDestinations: {total_destinations} total")
    for category, destinations in config["destinations"].items():
        print(f"  {category.title()}: {len(destinations)} destinations")

    # Transportation modes
    modes = config["transportation"]["modes"]
    print(f"\nTransportation Modes: {', '.join(modes)}")

    # Scoring weights
    weights = config["weights"]
    print(f"\nScoring Weights:")
    print(f"  Travel Time: {weights['travel_time']:.1%}")
    print(f"  Travel Cost: {weights['travel_cost']:.1%}")

    # Output configuration
    print(f"\nOutput:")
    print(f"  File: {output_path}")
    print(f"  Format: {config['output']['output_format']}")
    print(f"  Cache Duration: {config['output']['cache_duration']} days")

    print("\n" + "=" * 60)


def main() -> int:
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)

        logger.info("Starting Location Evaluator")

        ensure_directories()

        # Validate overrides
        validate_config_overrides(args)

        # Load configuration
        config = load_configuration(args)

        # Create output directory if it doesn't exist
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Show analysis plan if dry run
        if args.dry_run:
            show_analysis_plan(config, str(output_path))
            logger.info("Dry run completed successfully")
            return 0

        # Create analyzer
        analyzer = LocationAnalyzer(
            config=config, cache_only=args.cache_only, force_refresh=args.force_refresh
        )

        # Run analysis
        logger.info("Starting location analysis...")
        results = analyzer.run_analysis()

        # Generate output
        logger.info(f"Generating output: {output_path}")
        analyzer.generate_output(results, str(output_path))

        logger.info("Analysis completed successfully")
        return 0

    except KeyboardInterrupt:
        logging.error("Analysis interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        if args.verbose:
            logging.exception("Full error details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
