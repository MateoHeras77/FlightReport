import pytest
from datetime import datetime, date, time
from src.components.data_processing.time_utils import convert_time_string_to_datetime

def test_convert_valid_time_string():
    """Test converting a valid time string to a datetime object."""
    flight_date = date(2024, 3, 10)
    time_str = "14:30"
    expected_datetime = datetime(2024, 3, 10, 14, 30)
    assert convert_time_string_to_datetime(flight_date, time_str) == expected_datetime

def test_convert_empty_time_string():
    """Test converting an empty time string (should return None or handle gracefully)."""
    flight_date = date(2024, 3, 10)
    time_str = ""
    # Assuming the function is designed to return None for empty or invalid strings
    assert convert_time_string_to_datetime(flight_date, time_str) is None

def test_convert_invalid_time_format():
    """Test converting an invalid time string format."""
    flight_date = date(2024, 3, 10)
    time_str = "25:00" # Invalid hour
    assert convert_time_string_to_datetime(flight_date, time_str) is None # Assuming returns None
