import json
from datetime import datetime, timedelta, time
from typing import Dict

from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

# Clase para manejar la serialización de timedelta a JSON
class TimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return (obj.days * 24 * 60 * 60 + obj.seconds) * 1000  # Convertir a milisegundos
        return super().default(obj)

def convert_time_string_to_datetime(date_str: str, time_obj) -> datetime:
    """
    Convierte una cadena de fecha y un objeto time a un objeto datetime.
    
    Args:
        date_str: Fecha en formato 'YYYY-MM-DD'
        time_obj: Objeto time de Python o cadena en formato 'HH:MM:SS'
        
    Returns:
        datetime: Objeto datetime combinado o None si hay error
    """
    try:
        # Manejar caso donde time_obj es None
        if time_obj is None:
            return None
            
        # Si time_obj ya es un objeto time, usarlo directamente
        if isinstance(time_obj, time):
            return datetime.combine(datetime.strptime(date_str, "%Y-%m-%d").date(), time_obj)
            
        # Si es string, procesar como antes
        time_str = time_obj
        # Eliminar segundos si están presentes
        if isinstance(time_str, str) and len(time_str) > 5:
            time_str = time_str[:5]
            
        # Combinar fecha y hora
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except Exception as e:
        logger.warning(f"Error al convertir {date_str} {time_obj} a datetime: {e}")
        return None

def handle_midnight_crossover(events_dict: Dict[str, datetime], flight_date: datetime.date) -> Dict[str, datetime]:
    """
    Maneja los casos donde los eventos pueden cruzar la medianoche.
    
    Args:
        events_dict: Diccionario con eventos y sus timestamps
        flight_date: Fecha del vuelo
        
    Returns:
        Dict: Diccionario con eventos y timestamps ajustados
    """
    # Encontrar la hora mínima y máxima
    valid_times = [t for t in events_dict.values() if t is not None]
    if not valid_times:
        return events_dict
        
    # Identificar eventos clave para determinar si el vuelo es nocturno
    # Generalmente los primeros eventos (groomers_in, crew_at_gate) ocurren antes
    early_events = ["groomers_in", "crew_at_gate"]
    late_events = ["flight_secure", "cierre_de_puerta", "push_back", "atd"]
    
    early_times = [events_dict[e] for e in early_events if e in events_dict and events_dict[e] is not None]
    late_times = [events_dict[e] for e in late_events if e in events_dict and events_dict[e] is not None]
    
    # Si hay eventos tempranos y tardíos, y los tempranos tienen hora mayor (ej. 23:00)
    # que los tardíos (ej. 01:00), entonces estamos cruzando la medianoche
    is_overnight = False
    if early_times and late_times:
        avg_early = sum((dt.hour * 60 + dt.minute) for dt in early_times) / len(early_times)
        avg_late = sum((dt.hour * 60 + dt.minute) for dt in late_times) / len(late_times)
        
        # Si el promedio de horas tempranas es mayor que el de horas tardías,
        # probablemente estamos cruzando la medianoche
        if avg_early > avg_late and avg_early > 20 * 60 and avg_late < 4 * 60:  # 20:00 y 04:00
            is_overnight = True
            logger.info(f"Detectado vuelo nocturno: eventos tempranos ~{avg_early/60:.1f}h, eventos tardíos ~{avg_late/60:.1f}h")
    
    # Enfoque tradicional: usar la hora mínima como referencia
    min_time = min(valid_times)
    adjusted_dict = {}
    
    for event, event_time in events_dict.items():
        if event_time is None:
            adjusted_dict[event] = None
            continue
            
        # Si detectamos que es un vuelo nocturno y este es un evento tardío con hora temprana
        if is_overnight and event in late_events and event_time.hour < 12:
            # Añadir un día para que sea posterior a los eventos tempranos
            adjusted_dict[event] = event_time + timedelta(days=1)
            logger.info(f"Ajustando evento nocturno {event}: {event_time} -> {adjusted_dict[event]}")
        else:
            # Enfoque tradicional: verificar diferencia de horas
            hours_diff = (event_time - min_time).total_seconds() / 3600
            if hours_diff > 12:
                adjusted_dict[event] = event_time - timedelta(days=1)
            elif hours_diff < -12:
                adjusted_dict[event] = event_time + timedelta(days=1)
            else:
                adjusted_dict[event] = event_time
            
    return adjusted_dict