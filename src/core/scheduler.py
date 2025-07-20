"""
Schedule Processing
Converts schedule patterns into specific departure times and calculates frequencies.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import calendar


def process_schedules(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert YAML schedule patterns into specific departure times.
    
    Args:
        config: Configuration dictionary with destinations and schedules
        
    Returns:
        List of schedule items with departure times and frequencies
    """
    schedules = []
    
    for dest_category in config['destinations']:
        for destination in config['destinations'][dest_category]:
            for schedule_item in destination['schedule']:
                if 'days' in schedule_item:
                    # Weekly patterns
                    days = parse_days(schedule_item['days'])
                    for day in days:
                        schedules.append({
                            'destination': destination['address'],
                            'destination_name': destination['name'],
                            'category': dest_category,
                            'departure_time': schedule_item['arrival_time'],
                            'day': day,
                            'frequency': 'weekly',
                            'annual_occurrences': 52,
                            'lat': destination.get('lat'),
                            'lon': destination.get('lon'),
                        })
                        
                elif 'pattern' in schedule_item:
                    # Monthly patterns
                    schedules.append({
                        'destination': destination['address'],
                        'destination_name': destination['name'],
                        'category': dest_category,
                        'departure_time': schedule_item['arrival_time'],
                        'pattern': schedule_item['pattern'],
                        'frequency': 'monthly',
                        'annual_occurrences': 12,
                        'lat': destination.get('lat'),
                        'lon': destination.get('lon'),
                    })
    
    return schedules


def parse_days(days_str: str) -> List[str]:
    """
    Parse day string patterns into list of individual days.
    
    Args:
        days_str: String like "Mon-Fri", "Mon,Wed,Fri", etc.
        
    Returns:
        List of individual day strings
    """
    if '-' in days_str:
        # Range pattern like "Mon-Fri"
        start, end = days_str.split('-')
        day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        start_idx = day_map.index(start)
        end_idx = day_map.index(end)
        
        # Handle wrap-around (e.g., "Sat-Mon")
        if start_idx <= end_idx:
            return day_map[start_idx:end_idx + 1]
        else:
            return day_map[start_idx:] + day_map[:end_idx + 1]
            
    elif ',' in days_str:
        # Comma-separated like "Mon,Wed,Fri"
        return [day.strip() for day in days_str.split(',')]
    else:
        # Single day
        return [days_str]


def calculate_monthly_pattern_dates(pattern: str, year: int = None) -> List[datetime]:
    """
    Calculate specific dates for monthly patterns.
    
    Args:
        pattern: Monthly pattern like "first_monday", "last_friday"
        year: Year to calculate for (default current year)
        
    Returns:
        List of datetime objects for the pattern occurrences
    """
    if year is None:
        year = datetime.now().year
    
    dates = []
    
    # Parse pattern
    parts = pattern.split('_')
    if len(parts) != 2:
        return dates
    
    occurrence, day_name = parts
    
    # Map day names to weekday numbers (0=Monday, 6=Sunday)
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    if day_name not in day_map:
        return dates
    
    target_weekday = day_map[day_name]
    
    # Calculate for each month
    for month in range(1, 13):
        if occurrence == 'first':
            date = get_first_weekday_of_month(year, month, target_weekday)
        elif occurrence == 'second':
            date = get_nth_weekday_of_month(year, month, target_weekday, 2)
        elif occurrence == 'third':
            date = get_nth_weekday_of_month(year, month, target_weekday, 3)
        elif occurrence == 'fourth':
            date = get_nth_weekday_of_month(year, month, target_weekday, 4)
        elif occurrence == 'last':
            date = get_last_weekday_of_month(year, month, target_weekday)
        else:
            continue
        
        if date:
            dates.append(date)
    
    return dates


def get_first_weekday_of_month(year: int, month: int, weekday: int) -> datetime:
    """
    Get the first occurrence of a weekday in a month.
    
    Args:
        year: Year
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        
    Returns:
        datetime object for the first occurrence
    """
    # Start with the first day of the month
    first_day = datetime(year, month, 1)
    
    # Calculate days to add to get to the target weekday
    days_ahead = weekday - first_day.weekday()
    if days_ahead < 0:
        days_ahead += 7
    
    return first_day + timedelta(days=days_ahead)


def get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> datetime:
    """
    Get the nth occurrence of a weekday in a month.
    
    Args:
        year: Year
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        n: Which occurrence (2nd, 3rd, 4th)
        
    Returns:
        datetime object for the nth occurrence, or None if doesn't exist
    """
    first_occurrence = get_first_weekday_of_month(year, month, weekday)
    nth_occurrence = first_occurrence + timedelta(weeks=n-1)
    
    # Check if it's still in the same month
    if nth_occurrence.month == month:
        return nth_occurrence
    else:
        return None


def get_last_weekday_of_month(year: int, month: int, weekday: int) -> datetime:
    """
    Get the last occurrence of a weekday in a month.
    
    Args:
        year: Year
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        
    Returns:
        datetime object for the last occurrence
    """
    # Get the last day of the month
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Calculate days to subtract to get to the target weekday
    days_back = (last_day.weekday() - weekday) % 7
    
    return last_day - timedelta(days=days_back)


def calculate_weekly_frequency(schedules: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate weekly trip frequencies by destination.
    
    Args:
        schedules: List of schedule items
        
    Returns:
        Dictionary with weekly trip counts by destination
    """
    weekly_counts = {}
    
    for schedule in schedules:
        dest = schedule['destination']
        if dest not in weekly_counts:
            weekly_counts[dest] = 0
        
        if schedule['frequency'] == 'weekly':
            weekly_counts[dest] += 1
        elif schedule['frequency'] == 'monthly':
            # Monthly trips count as 1/4.33 weekly trips (52/12)
            weekly_counts[dest] += 12/52
    
    return weekly_counts


def calculate_monthly_frequency(schedules: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate monthly trip frequencies by destination.
    
    Args:
        schedules: List of schedule items
        
    Returns:
        Dictionary with monthly trip counts by destination
    """
    monthly_counts = {}
    
    for schedule in schedules:
        dest = schedule['destination']
        if dest not in monthly_counts:
            monthly_counts[dest] = 0
        
        if schedule['frequency'] == 'weekly':
            # Weekly trips: multiply by ~4.33 (52/12)
            monthly_counts[dest] += 52/12
        elif schedule['frequency'] == 'monthly':
            monthly_counts[dest] += 1
    
    return monthly_counts