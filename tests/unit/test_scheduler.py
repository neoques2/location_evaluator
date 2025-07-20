import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.scheduler import parse_days, calculate_monthly_pattern_dates


def test_parse_days_variants():
    assert parse_days('Mon-Fri') == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    assert parse_days('Fri-Mon') == ['Fri', 'Sat', 'Sun', 'Mon']
    assert parse_days('Tue,Thu') == ['Tue', 'Thu']
    assert parse_days('Wed') == ['Wed']


def test_monthly_pattern_dates_first_monday():
    dates = calculate_monthly_pattern_dates('first_monday', year=2023)
    assert len(dates) == 12
    assert dates[0] == datetime(2023, 1, 2)
    assert dates[1] == datetime(2023, 2, 6)
