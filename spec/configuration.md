# Configuration Specification

## Configuration Architecture

The Location Evaluator uses modular YAML configuration files organized by functional area. This approach allows users to modify specific aspects without affecting other settings.

### Configuration Files Structure

**`config/analysis.yaml`** - Core analysis parameters
- Grid size and spacing settings
- Analysis radius and center point
- Regional boundaries

**`config/destinations.yaml`** - Destination definitions and schedules
- Work, personal, and monthly destination categories
- Flexible scheduling patterns (weekly, monthly)
- Support for complex recurrence rules

**`config/transportation.yaml`** - Transportation mode preferences
- Enabled transportation modes (driving, walking, transit, biking)
- Mode-specific settings (toll avoidance, walking limits)
- Cost calculation preferences

**`config/api.yaml`** - External API configuration
- Google Maps API credentials and rate limits
- FBI crime data API settings
- Batch processing parameters

**`config/weights.yaml`** - Scoring algorithm weights
- Relative importance of travel time, cost, and safety
- Composite score calculation parameters

**`config/output.yaml`** - Output and visualization preferences
- Map styling and layer options
- Cache duration settings
- Export format preferences

## Schedule Pattern Design

### Weekly Schedule Patterns
- **Range patterns**: Support day ranges like "Mon-Fri" for consecutive workdays
- **List patterns**: Support comma-separated days like "Mon,Wed,Fri" for specific days
- **Single patterns**: Support individual days for one-off weekly activities

### Monthly Schedule Patterns
- **Ordinal patterns**: Support "first_monday", "second_tuesday", etc. for numbered occurrences
- **Last patterns**: Support "last_friday", "last_sunday" for end-of-month scheduling
- **Flexible recurrence**: Handle months with varying numbers of occurrences

### Frequency Calculation Design
- **Annual normalization**: Convert all patterns to annual occurrence counts
- **Weekly equivalents**: Monthly patterns normalized to weekly frequency (52/12 ratio)
- **Mixed pattern support**: Handle destinations with both weekly and monthly schedules

### Configuration Validation
- **Time format validation**: Ensure HH:MM format for all times
- **Pattern validation**: Verify monthly patterns exist in all months
- **Destination validation**: Ensure all addresses are geocodable
- **Weight validation**: Ensure scoring weights sum to 1.0

### Implementation Reference
See `config/destinations.yaml` for example configuration and `src/core/scheduler.py` for pattern processing implementation.