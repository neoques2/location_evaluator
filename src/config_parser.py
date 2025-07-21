"""
Configuration Parser and Validator
Loads and validates modular YAML configuration files.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Union
import logging

from .apis.geocoding import geocode_address
from .apis.network_utils import check_network_connectivity


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigParser:
    """
    Parses and validates configuration from modular YAML files.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _load_api_secrets(self, config_dir: Path) -> None:
        """Load API secrets from optional file and set environment variables."""
        secrets_file = config_dir / "api_secrets.yaml"
        if not secrets_file.exists():
            return
        try:
            with open(secrets_file, "r", encoding="utf-8") as f:
                secrets = yaml.safe_load(f) or {}
            if isinstance(secrets, dict):
                for key, value in secrets.items():
                    os.environ.setdefault(key, str(value))
                self.logger.debug(f"Loaded API secrets from {secrets_file}")
            else:
                self.logger.warning("api_secrets.yaml must contain a dictionary")
        except yaml.YAMLError as e:
            self.logger.warning(f"Invalid YAML in {secrets_file}: {e}")
        except Exception as e:
            self.logger.warning(f"Error loading {secrets_file}: {e}")

    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from directory of YAML files or single file.

        Args:
            config_path: Path to config directory or single config file

        Returns:
            Combined configuration dictionary
        """
        config_path = Path(config_path)

        if config_path.is_file():
            # Single config file
            return self._load_single_config(config_path)
        elif config_path.is_dir():
            # Directory of config files
            return self._load_modular_config(config_path)
        else:
            raise ConfigValidationError(f"Config path does not exist: {config_path}")

    def _load_single_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from a single YAML file."""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ConfigValidationError("Configuration must be a dictionary")

            return config

        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML in {config_file}: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Error loading {config_file}: {e}")

    def _load_modular_config(self, config_dir: Path) -> Dict[str, Any]:
        """Load configuration from modular YAML files in directory."""
        self._load_api_secrets(config_dir)
        config = {}

        # Expected config files
        config_files = {
            "analysis.yaml": "analysis",
            "destinations.yaml": "destinations",
            "transportation.yaml": "transportation",
            "api.yaml": "apis",
            "weights.yaml": "weights",
            "output.yaml": "output",
        }

        for filename, section in config_files.items():
            file_path = config_dir / filename

            if not file_path.exists():
                raise ConfigValidationError(
                    f"Required config file missing: {file_path}"
                )

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)

                if not isinstance(file_config, dict):
                    raise ConfigValidationError(
                        f"Config file {filename} must contain a dictionary"
                    )

                # Merge into main config
                config.update(file_config)

                self.logger.debug(f"Loaded config from {filename}")

            except yaml.YAMLError as e:
                raise ConfigValidationError(f"Invalid YAML in {file_path}: {e}")
            except Exception as e:
                raise ConfigValidationError(f"Error loading {file_path}: {e}")

        return config

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate complete configuration.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        self._validate_analysis_config(config.get("analysis", {}))
        self._validate_destinations_config(config.get("destinations", {}))
        self._validate_transportation_config(config.get("transportation", {}))
        self._validate_api_config(config.get("apis", {}))
        self._check_api_connectivity(config.get("apis", {}))
        self._validate_weights_config(config.get("weights", {}))
        self._validate_output_config(config.get("output", {}))

    def _validate_analysis_config(self, analysis: Dict[str, Any]) -> None:
        """Validate analysis configuration."""
        required_fields = ["center_point", "grid_size", "max_radius"]

        for field in required_fields:
            if field not in analysis:
                raise ConfigValidationError(f"Missing required analysis field: {field}")

        # Validate grid size
        grid_size = analysis["grid_size"]
        if not isinstance(grid_size, (int, float)) or not (0.1 <= grid_size <= 2.0):
            raise ConfigValidationError("Grid size must be between 0.1 and 2.0 miles")

        # Validate max radius
        max_radius = analysis["max_radius"]
        if not isinstance(max_radius, (int, float)) or not (5 <= max_radius <= 50):
            raise ConfigValidationError("Max radius must be between 5 and 50 miles")

        # Validate center point
        center_point = analysis["center_point"]
        if isinstance(center_point, str):
            # Address string - will be geocoded later
            pass
        elif isinstance(center_point, list) and len(center_point) == 2:
            # [lat, lon] coordinates
            lat, lon = center_point
            if not (-90 <= lat <= 90):
                raise ConfigValidationError("Latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ConfigValidationError("Longitude must be between -180 and 180")
        else:
            raise ConfigValidationError(
                "Center point must be address string or [lat, lon] coordinates"
            )

    def _validate_destinations_config(self, destinations: Dict[str, Any]) -> None:
        """Validate destinations configuration."""
        if not destinations:
            raise ConfigValidationError("At least one destination category is required")

        total_destinations = 0

        for category, dest_list in destinations.items():
            if not isinstance(dest_list, list):
                raise ConfigValidationError(
                    f"Destination category '{category}' must be a list"
                )

            for i, dest in enumerate(dest_list):
                if not isinstance(dest, dict):
                    raise ConfigValidationError(
                        f"Destination {i} in '{category}' must be a dictionary"
                    )

                # Required fields
                if "address" not in dest:
                    raise ConfigValidationError(
                        f"Destination {i} in '{category}' missing address"
                    )
                if "name" not in dest:
                    raise ConfigValidationError(
                        f"Destination {i} in '{category}' missing name"
                    )
                if "schedule" not in dest:
                    raise ConfigValidationError(
                        f"Destination {i} in '{category}' missing schedule"
                    )

                # Validate schedule
                self._validate_schedule(dest["schedule"], f"{category}[{i}]")

                # Validate geocoding for address unless network checks are disabled
                if os.getenv("LE_SKIP_NETWORK") == "1":
                    geo = {"lat": 0.0, "lon": 0.0}
                else:
                    geo = geocode_address(dest["address"])
                    if geo is None:
                        raise ConfigValidationError(
                            f"Could not geocode address '{dest['address']}' in category '{category}'"
                        )
                dest["lat"] = geo["lat"]
                dest["lon"] = geo["lon"]

                total_destinations += 1

        if total_destinations == 0:
            raise ConfigValidationError("At least one destination is required")

    def _validate_schedule(self, schedule: list, dest_name: str) -> None:
        """Validate schedule configuration for a destination."""
        if not isinstance(schedule, list) or len(schedule) == 0:
            raise ConfigValidationError(
                f"Schedule for {dest_name} must be a non-empty list"
            )

        for i, schedule_item in enumerate(schedule):
            if not isinstance(schedule_item, dict):
                raise ConfigValidationError(
                    f"Schedule item {i} for {dest_name} must be a dictionary"
                )

            # Must have arrival_time
            if "arrival_time" not in schedule_item:
                raise ConfigValidationError(
                    f"Schedule item {i} for {dest_name} missing arrival_time"
                )

            # Validate time format (HH:MM)
            arrival_time = schedule_item["arrival_time"]
            if not self._validate_time_format(arrival_time):
                raise ConfigValidationError(
                    f"Invalid time format '{arrival_time}' in {dest_name}. Use HH:MM format"
                )

            # Must have either 'days' (weekly) or 'pattern' (monthly)
            if "days" in schedule_item:
                # Weekly pattern
                days = schedule_item["days"]
                if not isinstance(days, str):
                    raise ConfigValidationError(
                        f"Days field in {dest_name} must be a string"
                    )

                # Validate day patterns
                if not self._validate_days_pattern(days):
                    raise ConfigValidationError(
                        f"Invalid days pattern '{days}' in {dest_name}"
                    )

            elif "pattern" in schedule_item:
                # Monthly pattern
                pattern = schedule_item["pattern"]
                if not isinstance(pattern, str):
                    raise ConfigValidationError(
                        f"Pattern field in {dest_name} must be a string"
                    )

                # Validate monthly patterns
                if not self._validate_monthly_pattern(pattern):
                    raise ConfigValidationError(
                        f"Invalid monthly pattern '{pattern}' in {dest_name}"
                    )

            else:
                raise ConfigValidationError(
                    f"Schedule item {i} for {dest_name} must have 'days' or 'pattern'"
                )

    def _validate_time_format(self, time_str: str) -> bool:
        """Validate time string is in HH:MM format."""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False

            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, TypeError):
            return False

    def _validate_days_pattern(self, days: str) -> bool:
        """Validate days pattern (Mon-Fri, Mon,Wed,Fri, etc.)."""
        valid_days = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

        if "-" in days:
            # Range pattern
            try:
                start, end = days.split("-")
                return start.strip() in valid_days and end.strip() in valid_days
            except ValueError:
                return False
        elif "," in days:
            # Comma-separated
            day_list = [day.strip() for day in days.split(",")]
            return all(day in valid_days for day in day_list)
        else:
            # Single day
            return days.strip() in valid_days

    def _validate_monthly_pattern(self, pattern: str) -> bool:
        """Validate monthly pattern (first_monday, last_friday, etc.)."""
        valid_occurrences = {"first", "second", "third", "fourth", "last"}
        valid_days = {
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        }

        try:
            occurrence, day = pattern.split("_")
            return occurrence in valid_occurrences and day in valid_days
        except ValueError:
            return False

    def _validate_transportation_config(self, transportation: Dict[str, Any]) -> None:
        """Validate transportation configuration."""
        if "modes" not in transportation:
            raise ConfigValidationError("Transportation config missing 'modes' field")

        modes = transportation["modes"]
        if not isinstance(modes, list) or len(modes) == 0:
            raise ConfigValidationError("Transportation modes must be a non-empty list")

        valid_modes = {"driving", "walking", "transit", "biking"}
        for mode in modes:
            if mode not in valid_modes:
                raise ConfigValidationError(f"Invalid transportation mode: {mode}")

    def _validate_api_config(self, apis: Dict[str, Any]) -> None:
        """Validate API configuration."""
        if "osrm" not in apis:
            raise ConfigValidationError("API config missing OSRM section")

        osrm_cfg = apis["osrm"]
        if "base_url" not in osrm_cfg:
            raise ConfigValidationError("OSRM config missing base_url")

        if (
            not isinstance(osrm_cfg["base_url"], str)
            or osrm_cfg["base_url"].strip() == ""
        ):
            raise ConfigValidationError("Invalid OSRM base_url")

        if "timeout" in osrm_cfg and (
            not isinstance(osrm_cfg["timeout"], int) or osrm_cfg["timeout"] <= 0
        ):
            raise ConfigValidationError("OSRM timeout must be positive integer")

        if "requests_per_second" in osrm_cfg:
            rps = osrm_cfg["requests_per_second"]
            if not isinstance(rps, int) or rps <= 0:
                raise ConfigValidationError(
                    "requests_per_second must be positive integer"
                )

        if "cache" in osrm_cfg and not isinstance(osrm_cfg["cache"], bool):
            raise ConfigValidationError("OSRM cache must be boolean")

        if "batch_size" in osrm_cfg:
            bs = osrm_cfg["batch_size"]
            if not isinstance(bs, int) or bs <= 0:
                raise ConfigValidationError("OSRM batch_size must be positive integer")

        if "fbi_crime" not in apis:
            raise ConfigValidationError("API config missing fbi_crime section")

        fbi_cfg = apis["fbi_crime"]
        if "base_url" not in fbi_cfg:
            raise ConfigValidationError("FBI crime config missing base_url")

        if "timeout" in fbi_cfg and (
            not isinstance(fbi_cfg["timeout"], int) or fbi_cfg["timeout"] <= 0
        ):
            raise ConfigValidationError("FBI crime timeout must be positive integer")

    def _check_api_connectivity(self, apis: Dict[str, Any]) -> None:
        """Check that API endpoints are reachable."""
        if os.getenv("LE_SKIP_NETWORK") == "1":
            return
        osrm_url = apis.get("osrm", {}).get("base_url")
        if osrm_url and not check_network_connectivity(osrm_url):
            raise ConfigValidationError(f"Cannot reach OSRM server at {osrm_url}")

        fbi_url = apis.get("fbi_crime", {}).get("base_url")
        if fbi_url and not check_network_connectivity(fbi_url):
            raise ConfigValidationError(f"Cannot reach FBI API at {fbi_url}")

    def _validate_weights_config(self, weights: Dict[str, Any]) -> None:
        """Validate weights configuration."""
        required_weights = ["travel_time", "travel_cost", "safety"]

        for weight in required_weights:
            if weight not in weights:
                raise ConfigValidationError(f"Missing weight: {weight}")

            value = weights[weight]
            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                raise ConfigValidationError(f"Weight {weight} must be between 0 and 1")

        # Check weights sum to 1.0 (with small tolerance for floating point)
        total = sum(weights[w] for w in required_weights)
        if abs(total - 1.0) > 0.001:
            raise ConfigValidationError(f"Weights must sum to 1.0, got {total}")

        # Optional safety parameter calibration
        params = weights.get("safety_parameters", {})
        if params:
            for field in [
                "violent_weight",
                "property_weight",
                "other_weight",
                "density_scale",
                "score_scale",
            ]:
                if field not in params:
                    raise ConfigValidationError(f"Missing safety parameter: {field}")
                val = params[field]
                if not isinstance(val, (int, float)) or val <= 0:
                    raise ConfigValidationError(
                        f"Safety parameter {field} must be positive number"
                    )

    def _validate_output_config(self, output: Dict[str, Any]) -> None:
        """Validate output configuration."""
        if "output_format" in output:
            valid_formats = {"html", "json", "both"}
            if output["output_format"] not in valid_formats:
                raise ConfigValidationError(
                    f"Invalid output format: {output['output_format']}"
                )

        if "cache_duration" in output:
            duration = output["cache_duration"]
            if not isinstance(duration, (int, float)) or duration < 1:
                raise ConfigValidationError("Cache duration must be at least 1 day")
