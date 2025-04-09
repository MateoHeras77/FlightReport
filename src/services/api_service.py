import requests
import streamlit as st
from datetime import date
from typing import Optional, List, Dict
import time

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
        flight_number = flight_number.replace(" ", "").lower()


        # Verificar si el vuelo está en caché y no ha expirado
        current_time = time.time()
        if flight_number in cache:
            cached_data, timestamp = cache[flight_number]
            if current_time - timestamp < CACHE_EXPIRATION:
                print(f"[DEBUG] Datos obtenidos del caché para el vuelo {flight_number}.")
                return cached_data

        # URL de la API con el número de vuelo
        url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number}"


        # Fecha de consulta
        today = date.today().strftime("%Y-%m-%d")
        flight_date = custom_date or today

        # Cargar claves API desde secrets.toml
        api_key_1 = st.secrets["aerodatabox"]["api_key"]
        api_key_2 = st.secrets["aerodatabox"]["api_key_2"]

        # Headers para la petición
        headers = {
            "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
        }


        # Realizar la petición a la API
        print(f"[DEBUG] Llamando a la API para obtener datos del vuelo {flight_number}.")
        response = requests.get(url, headers=headers, params=querystring)

        # Verificar si la respuesta fue exitosa
        if response.status_code == 200:
            flight_data = response.json()
            print(f"[DEBUG] Respuesta de la API para {flight_number}: {flight_data}")
            # Almacenar en caché los datos obtenidos
            cache[flight_number] = (flight_data, current_time)
            return flight_data
        else:
            print(f"[DEBUG] Error en la respuesta de la API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None