from typing import Dict, List, Any
from datetime import datetime, time, timedelta
import pandas as pd

from src.config.logging_config import setup_logger
from src.components.data_processing.time_utils import convert_time_string_to_datetime, handle_midnight_crossover

# Configurar logger
logger = setup_logger()

def calculate_average_event_times(flights_data: List[Dict[str, Any]]) -> Dict[str, datetime]:
    """
    Calcula los tiempos promedio para cada evento considerando cruces de medianoche.
    
    Args:
        flights_data: Lista de diccionarios con datos de vuelos
        
    Returns:
        Dict[str, datetime]: Dictionary with events and their average times.
    """
    try:
        # Define the list of event types to be processed.
        # These correspond to columns in the flight data that store time information.
        events = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", 
            "flight_secure", "cierre_de_puerta", "push_back", "std", "atd"
        ]
        
        # Initialize a dictionary to store lists of datetime objects for each event type.
        # e.g., event_times = {"groomers_in": [datetime1, datetime2], "std": [datetime3, datetime4]}
        event_times: Dict[str, List[datetime]] = {event: [] for event in events}
        
        # Iterate over each flight record in the input data.
        for flight in flights_data:
            # Get the flight date, which is essential for converting time strings to datetime objects.
            flight_date_str = flight.get("flight_date")
            if not flight_date_str:
                # If flight_date is missing, skip this flight record as times cannot be accurately processed.
                logger.warning(f"Skipping flight due to missing flight_date: {flight.get('id', 'Unknown ID')}")
                continue
                
            # For each defined event, attempt to get its time string from the flight record.
            for event_name in events:
                time_str = flight.get(event_name)
                if time_str:
                    # Convert the time string to a datetime object using the flight_date.
                    # convert_time_string_to_datetime is expected to handle various time formats and return a datetime object.
                    datetime_obj = convert_time_string_to_datetime(flight_date_str, time_str)
                    if datetime_obj:
                        # If conversion is successful, add the datetime object to the list for the current event.
                        event_times[event_name].append(datetime_obj)
                    else:
                        logger.warning(f"Could not convert time string for event '{event_name}' with value '{time_str}' in flight {flight.get('id', 'Unknown ID')}")

        # Initialize a dictionary to store the calculated average time for each event.
        average_times: Dict[str, datetime] = {}
        
        # Iterate over each event and its list of collected datetime objects.
        for event_name, times_list in event_times.items():
            if not times_list:
                # If no times were collected for an event (e.g., all flights had missing data for this event), skip it.
                logger.info(f"No data found for event '{event_name}' to calculate average.")
                continue
                
            # Sort the datetime objects chronologically. This is crucial for accurately detecting midnight crossovers.
            sorted_times = sorted(times_list)
            
            # --- Midnight Crossover Detection and Handling ---
            # This section aims to normalize times that might span across midnight.
            # For example, if an event usually happens around 11 PM, but one instance is recorded at 1 AM,
            # it's likely the 1 AM event refers to the "next day" relative to the flight's operational window.
            # The logic assumes that a large gap (more than 12 hours) between consecutive sorted times
            # indicates a potential midnight crossover.
            
            is_overnight = False
            # Check for large time gaps between consecutive events.
            for i in range(len(sorted_times) - 1):
                # Calculate the difference in seconds between the current and next time.
                time_difference_seconds = (sorted_times[i+1] - sorted_times[i]).total_seconds()
                # A common threshold for detecting overnight crossover is a difference greater than half a day (12 hours).
                if time_difference_seconds > 12 * 3600:
                    is_overnight = True
                    logger.debug(f"Overnight crossover detected for event '{event_name}' between {sorted_times[i]} and {sorted_times[i+1]}.")
                    break # Crossover detected, no need to check further for this event.
            
            adjusted_times_for_avg = []
            if is_overnight:
                # If a potential midnight crossover is detected, adjust times to a consistent day for averaging.
                # The goal is to treat times like 1:00 AM (next day) as effectively 25:00 for averaging purposes
                # if most other times are on the "previous day" (e.g., 11:00 PM).
                
                # Heuristic: If a time entry is significantly later than the previous one (by >12 hours),
                # it's assumed to be on the "next day" and is adjusted back by 24 hours (1 day)
                # to bring it into the same conceptual day as the earlier times for averaging.
                # This is a simplified approach and might need refinement for complex scenarios.
                
                # Base the adjustment on the first time entry.
                # All times will be conceptually brought closer to this first_time's day.
                # This is a simple heuristic. A more robust method might involve looking at the distribution of times.
                
                # Temporary list to hold times, potentially adjusted.
                temp_adjusted_times = [sorted_times[0]] # Start with the first time.
                for i in range(1, len(sorted_times)):
                    current_time = sorted_times[i]
                    previous_time = temp_adjusted_times[i-1] # Compare with the *last adjusted* time.

                    if (current_time - previous_time).total_seconds() > 12 * 3600:
                        # If current_time is much later than previous_time, pull it back by a day.
                        logger.debug(f"Adjusting time for event '{event_name}': {current_time} -> {current_time - timedelta(days=1)}")
                        temp_adjusted_times.append(current_time - timedelta(days=1))
                    elif (previous_time - current_time).total_seconds() > 12 * 3600:
                        # If current_time is much earlier than previous_time (e.g. prev was 23:00, current is 01:00 after sorting),
                        # push current_time forward by a day. This case might be less common with initial sorting
                        # but is a safeguard.
                        logger.debug(f"Adjusting time for event '{event_name}': {current_time} -> {current_time + timedelta(days=1)}")
                        temp_adjusted_times.append(current_time + timedelta(days=1))
                    else:
                        temp_adjusted_times.append(current_time)
                adjusted_times_for_avg = temp_adjusted_times
            else:
                # If no significant overnight crossover is detected, use the original sorted times for averaging.
                adjusted_times_for_avg = sorted_times
            
            # --- Calculate Average Time ---
            # Convert all (potentially adjusted) datetime objects to total seconds from the beginning of their day.
            # This allows for a simple numerical average of the time-of-day component.
            total_seconds_from_midnight = sum(t.hour * 3600 + t.minute * 60 + t.second for t in adjusted_times_for_avg)
            
            # Calculate the average number of seconds from midnight.
            avg_seconds_from_midnight = total_seconds_from_midnight / len(adjusted_times_for_avg)
            
            # Convert the average seconds back into hour, minute, and second components.
            avg_hour = int(avg_seconds_from_midnight // 3600)
            avg_minute = int((avg_seconds_from_midnight % 3600) // 60)
            avg_second = int(avg_seconds_from_midnight % 60)
            
            # Use the date part of the first original sorted time as a reference date for the final average datetime object.
            # The date part itself isn't strictly meaningful for an "average time", but datetime objects require a date.
            reference_date = sorted_times[0].date()
            average_times[event_name] = datetime.combine(reference_date, time(avg_hour, avg_minute, avg_second))
            logger.debug(f"Calculated average time for event '{event_name}': {average_times[event_name].time()}")
        
        return average_times
        
    except Exception as e:
        logger.exception(f"Error calculating average event times: {e}")
        return {}