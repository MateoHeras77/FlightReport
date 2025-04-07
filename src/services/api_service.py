import requests
import streamlit as st
from datetime import date
from typing import Optional, List, Dict

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

        # URL base de la API
        base_url = "https://aerodatabox.p.rapidapi.com/flights/number/"

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

        # Intentar con la primera clave API
        headers["x-rapidapi-key"] = api_key_1
        try:
            response = requests.get(f"{base_url}{flight_number}/{flight_date}", headers=headers)
            if response.status_code == 200:
                print("API Key 1 used successfully.")
                return response.json()
            else:
                print(f"API Key 1 failed with status code {response.status_code}. Trying API Key 2...")
        except Exception as e:
            print(f"Error with API Key 1: {e}. Trying API Key 2...")

        # Intentar con la segunda clave API
        headers["x-rapidapi-key"] = api_key_2
        try:
            response = requests.get(f"{base_url}{flight_number}/{flight_date}", headers=headers)
            if response.status_code == 200:
                print("API Key 2 used successfully.")
                return response.json()
            else:
                print(f"API Key 2 failed with status code {response.status_code}.")
        except Exception as e:
            print(f"Error with API Key 2: {e}.")

        # Si ambas claves fallan, retornar None
        print("Both API keys failed.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None