import requests
import streamlit as st
from datetime import date
from typing import Optional, List, Dict
import streamlit as st # Import Streamlit
import time
import logging # Import logging
from typing import Optional, List, Dict
from datetime import date

# Configurar logger
logger = logging.getLogger(__name__)

@st.cache_data(ttl=900) # Cache for 15 minutes
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
        logger.info(f"Fetching flight status for: {flight_number_formatted} on date {flight_date}.") # Log flight number and date

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

            logger.info(f"Calling API for flight {flight_number_formatted} with API key {i+1}.")
            try:
                response = requests.get(url, headers=headers, params=querystring, timeout=10)

                if response.status_code == 200:
                    flight_data = response.json()
                    logger.info(f"API response successful for {flight_number_formatted} with API key {i+1}.")
                    return flight_data
                else:
                    logger.warning(f"API request for {flight_number_formatted} with key {i+1} failed with status {response.status_code}: {response.text}")
                    if i < len(api_keys) - 1:
                         logger.info(f"Trying with API key {i+2}.")
                    else:
                        logger.error(f"All API keys failed for flight {flight_number_formatted}.")
                        return None
            except requests.exceptions.RequestException as req_err:
                 logger.error(f"Connection/timeout error with API key {i+1} for flight {flight_number_formatted}: {req_err}")
                 if i < len(api_keys) - 1:
                     logger.info(f"Trying with API key {i+2}.")
                 else:
                     logger.error(f"All API keys failed due to connection errors for flight {flight_number_formatted}.")
                     return None
            # Wait a bit before retrying with the next key if the first one fails
            if i < len(api_keys) - 1:
                time.sleep(1) # Consider if this sleep is necessary or if rapid retries are okay

        # If the loop finishes without returning, it means all keys failed.
        logger.error(f"All API attempts failed for flight {flight_number_formatted}.")
        return None

    except Exception as e:
        logger.error(f"Unexpected error in fetch_flight_status for flight {flight_number}: {e}", exc_info=True)
        return None