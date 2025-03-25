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
        Dict[str, datetime]: Diccionario con eventos y sus tiempos promedio
    """
    try:
        # Eventos a procesar
        events = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", 
            "flight_secure", "cierre_de_puerta", "push_back", "std", "atd"
        ]
        
        # Diccionario para almacenar todos los tiempos por evento
        event_times = {event: [] for event in events}
        
        # Procesar cada vuelo
        for flight in flights_data:
            flight_date = flight.get("flight_date")
            if not flight_date:
                continue
                
            # Convertir tiempos a datetime
            for event in events:
                time_obj = flight.get(event)
                if time_obj:
                    dt = convert_time_string_to_datetime(flight_date, time_obj)
                    if dt:
                        event_times[event].append(dt)
        
        # Calcular promedios considerando cruces de medianoche
        average_times = {}
        
        for event, times in event_times.items():
            if not times:
                continue
                
            # Ordenar tiempos
            sorted_times = sorted(times)
            
            # Detectar si hay cruces de medianoche
            is_overnight = False
            for i in range(len(sorted_times) - 1):
                if (sorted_times[i+1] - sorted_times[i]).total_seconds() > 12 * 3600:  # Más de 12 horas de diferencia
                    is_overnight = True
                    break
            
            if is_overnight:
                # Para cruces de medianoche, ajustar tiempos
                adjusted_times = []
                for i, t in enumerate(sorted_times):
                    if i > 0 and (t - sorted_times[i-1]).total_seconds() > 12 * 3600:
                        # Si hay un salto grande, ajustar el tiempo actual
                        adjusted_times.append(t - timedelta(days=1))
                    else:
                        adjusted_times.append(t)
                
                # Calcular promedio de tiempos ajustados
                total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in adjusted_times)
                avg_seconds = total_seconds / len(adjusted_times)
                
                # Crear datetime promedio
                avg_hour = int(avg_seconds // 3600)
                avg_minute = int((avg_seconds % 3600) // 60)
                avg_second = int(avg_seconds % 60)
                
                # Usar la fecha del primer vuelo como referencia
                reference_date = sorted_times[0].date()
                average_times[event] = datetime.combine(reference_date, time(avg_hour, avg_minute, avg_second))
            else:
                # Para vuelos normales, calcular promedio directo
                total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in sorted_times)
                avg_seconds = total_seconds / len(sorted_times)
                
                avg_hour = int(avg_seconds // 3600)
                avg_minute = int((avg_seconds % 3600) // 60)
                avg_second = int(avg_seconds % 60)
                
                reference_date = sorted_times[0].date()
                average_times[event] = datetime.combine(reference_date, time(avg_hour, avg_minute, avg_second))
        
        return average_times
        
    except Exception as e:
        logger.exception(f"Error al calcular tiempos promedio: {e}")
        return {}