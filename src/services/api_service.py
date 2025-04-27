import requests
import streamlit as st
from datetime import date
from typing import Optional, List, Dict
import time
import logging # Import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Diccionario para almacenar el caché manualmente
cache = {}
CACHE_EXPIRATION = 15 * 60  # 15 minutos en segundos

def fetch_flight_status(flight_number: str, custom_date: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Consulta la API de AeroDataBox para obtener el estado actual de un vuelo.
    Si la primera clave API falla, se intenta con la segunda clave API.

    Args:
        flight_number: Número de vuelo (ej: AV204)
        custom_date: Fecha personalizada para la consulta (opcional)

    Returns:
        Optional[List[Dict]]: Datos del vuelo o None si ocurre un error
    """
    try:
        # Formatear el número de vuelo eliminando espacios
        flight_number_formatted = flight_number.replace(" ", "").lower()
        flight_date = custom_date or date.today().strftime("%Y-%m-%d")
        logger.info(f"Iniciando consulta para vuelo: {flight_number_formatted} en fecha {flight_date}.") # Log flight number and date

        # Verificar si el vuelo está en caché y no ha expirado
        current_time = time.time()
        cache_key = f"{flight_number_formatted}_{flight_date}" # Use formatted flight number and date in cache key
        if cache_key in cache:
            cached_data, timestamp = cache[cache_key]
            if current_time - timestamp < CACHE_EXPIRATION:
                logger.info(f"Datos obtenidos del caché para el vuelo {flight_number_formatted} en fecha {flight_date}.")
                return cached_data

        # URL de la API con el número de vuelo
        url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number_formatted}"

        # Definir querystring
        querystring = {"date": flight_date}

        # Cargar claves API desde secrets.toml
        api_key_1 = st.secrets["aerodatabox"]["api_key"]
        api_key_2 = st.secrets["aerodatabox"]["api_key_2"]
        api_keys = [api_key_1, api_key_2]

        # Headers base para la petición
        base_headers = {
            "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
        }

        flight_data = None
        response = None

        # Intentar con ambas claves API
        for i, key in enumerate(api_keys):
            headers = base_headers.copy()
            headers["x-rapidapi-key"] = key

            logger.info(f"Llamando a la API para vuelo {flight_number_formatted} con clave API {i+1}.") # Changed to INFO
            try:
                response = requests.get(url, headers=headers, params=querystring, timeout=10)

                if response.status_code == 200:
                    flight_data = response.json()
                    logger.info(f"Respuesta exitosa de la API para {flight_number_formatted} con clave API {i+1}.") # Changed to INFO
                    cache[cache_key] = (flight_data, current_time)
                    return flight_data
                else:
                    logger.warning(f"Error en la respuesta de la API con clave {i+1}: {response.status_code} - {response.text}")
                    if i < len(api_keys) - 1:
                         logger.info(f"Intentando con clave API {i+2}.") # Inform about trying next key
                    else:
                        logger.error(f"Ambas claves API fallaron para el vuelo {flight_number_formatted}.")
                        return None
            except requests.exceptions.RequestException as req_err:
                 logger.error(f"Error de conexión/timeout con clave {i+1} para vuelo {flight_number_formatted}: {req_err}")
                 if i < len(api_keys) - 1:
                     logger.info(f"Intentando con clave API {i+2}.") # Inform about trying next key
                 else:
                     logger.error(f"Ambas claves API fallaron debido a errores de conexión para el vuelo {flight_number_formatted}.")
                     return None
            # Esperar un poco antes de reintentar con la siguiente clave si la primera falla
            if i < len(api_keys) - 1:
                time.sleep(1)

        # Si el bucle termina sin retornar, significa que ambas claves fallaron
        return None

    except Exception as e:
        logger.error(f"Error inesperado en fetch_flight_status para vuelo {flight_number}: {e}", exc_info=True)
        return None