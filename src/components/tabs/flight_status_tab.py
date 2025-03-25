import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import pytz
from typing import Dict, List, Any, Optional

from src.config.logging_config import setup_logger
from src.components.charts.flight_status_charts import create_flight_map, create_flight_progress_chart

# Configurar logger
logger = setup_logger()

def fetch_flight_status(flight_number: str, custom_date: Optional[str] = None) -> Optional[List[Dict]]: 
    """
    Consulta la API de AeroDataBox para obtener el estado actual de un vuelo.
    
    Args:
        flight_number: Número de vuelo (ej: av204)
        custom_date: Fecha personalizada para la consulta (opcional)
        
    Returns:
        Optional[List[Dict]]: Datos del vuelo o None si ocurre un error
    """
    try:
        # Formatear el número de vuelo eliminando espacios
        flight_number = flight_number.replace(" ", "").lower()
        
        # URL de la API con el número de vuelo
        url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number}"
        
        # Parámetros de la consulta
        today = date.today().strftime("%Y-%m-%d")
        querystring = {"withAircraftImage": "false", "withLocation": "false", "scheduledDepartureDate": custom_date or today}
        
        # Headers con la clave de API desde secrets.toml
        api_key = st.secrets["aerodatabox"]["api_key"]
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
        }
        
        # Realizar la petición a la API
        logger.info(f"Consultando API para vuelo {flight_number} en la fecha {custom_date or today}")
        response = requests.get(url, headers=headers, params=querystring)
        
        # Verificar si la respuesta fue exitosa
        if response.status_code == 200:
            flight_data = response.json()
            logger.info(f"API respondió exitosamente para vuelo {flight_number}")
            return flight_data
        else:
            logger.error(f"Error al consultar API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.exception(f"Error al obtener estado del vuelo: {e}")
        return None

def format_flight_time(time_data: Dict, timezone_name: str) -> str:
    """
    Formatea un tiempo de vuelo para mostrar.
    
    Args:
        time_data: Diccionario con datos de tiempo (UTC y local)
        timezone_name: Nombre de la zona horaria para contexto
        
    Returns:
        str: Tiempo formateado
    """
    if not time_data or 'local' not in time_data:
        return "No disponible"
    
    try:
        # Extraer la parte de la fecha y hora
        local_datetime = time_data['local']
        
        # Convertir a un objeto datetime
        dt = datetime.strptime(local_datetime, "%Y-%m-%d %H:%M%z")
        
        # Formatear para mostrar la hora y minutos con timezone
        return f"{dt.strftime('%H:%M')} ({timezone_name})"
    except Exception as e:
        logger.error(f"Error al formatear tiempo: {e}")
        return time_data.get('local', 'No disponible')

def render_flight_info_card(flight_data: Dict) -> None:
    """
    Renderiza una tarjeta con la información básica del vuelo.
    
    Args:
        flight_data: Diccionario con datos del vuelo
    """
    # Extraer datos principales
    status = flight_data.get('status', 'Desconocido')
    airline = flight_data.get('airline', {}).get('name', 'Desconocido')
    flight_number = flight_data.get('number', 'Desconocido')
    aircraft = flight_data.get('aircraft', {}).get('model', 'Desconocido')
    aircraft_reg = flight_data.get('aircraft', {}).get('reg', 'Desconocido')
    
    # Crear estilos según el estado del vuelo
    status_colors = {
        'Scheduled': '#1E88E5',    # Azul
        'EnRoute': '#43A047',      # Verde
        'Landed': '#7CB342',       # Verde claro
        'Delayed': '#FBC02D',      # Amarillo
        'Diverted': '#F57C00',     # Naranja
        'Cancelled': '#E53935',    # Rojo
    }
    
    status_color = status_colors.get(status, '#757575')  # Gris por defecto
    
    # Tarjeta de información del vuelo
    st.markdown(f"""
    <div style="
        border-radius: 10px;
        background-color: white;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 5px solid {status_color};
    ">
        <h3 style="margin: 0; color: #333;">✈️ {flight_number}</h3>
        <p style="margin: 5px 0; color: #666;">🛫 {airline} - {aircraft} ({aircraft_reg})</p>
        <div style="
            display: inline-block;
            background-color: {status_color};
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            margin-top: 5px;
            font-weight: bold;
        ">
            {status}
        </div>
        <a href="https://www.flightradar24.com/" target="_blank" style="
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    padding: 12px 20px;
    background: linear-gradient(135deg, #1a1a1a, #333);
    color: #ffffff;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
">
    ✈️ <span>Ver en FlightRadar24</span>
    </a>

    """, unsafe_allow_html=True)

def display_route_info(flight_data: Dict) -> None:
    """
    Muestra la información de la ruta del vuelo.
    
    Args:
        flight_data: Diccionario con datos del vuelo
    """
    # Extraer información de origen y destino
    departure = flight_data.get('departure', {})
    arrival = flight_data.get('arrival', {})
    
    # Aeropuertos
    dep_airport = departure.get('airport', {})
    arr_airport = arrival.get('airport', {})
    
    # Códigos IATA
    dep_iata = dep_airport.get('iata', '---')
    arr_iata = arr_airport.get('iata', '---')
    
    # Nombres de ciudades
    dep_city = dep_airport.get('municipalityName', 'Desconocido')
    arr_city = arr_airport.get('municipalityName', 'Desconocido')
    
    # Nombres de aeropuertos
    dep_name = dep_airport.get('shortName', 'Desconocido')
    arr_name = arr_airport.get('shortName', 'Desconocido')
    
    # Zonas horarias
    dep_timezone = dep_airport.get('timeZone', 'Local')
    arr_timezone = arr_airport.get('timeZone', 'Local')
    
    # Tiempos programados y revisados
    dep_scheduled = format_flight_time(departure.get('scheduledTime'), dep_timezone)
    dep_revised = format_flight_time(departure.get('revisedTime'), dep_timezone)
    
    arr_scheduled = format_flight_time(arrival.get('scheduledTime'), arr_timezone)
    arr_revised = format_flight_time(arrival.get('revisedTime'), arr_timezone)
    arr_predicted = format_flight_time(arrival.get('predictedTime'), arr_timezone)
    
    # Terminal, puerta y banda de equipaje
    dep_terminal = departure.get('terminal', 'N/A')
    dep_gate = departure.get('gate', 'N/A')
    
    arr_terminal = arrival.get('terminal', 'N/A')
    arr_gate = arrival.get('gate', 'N/A')
    arr_belt = arrival.get('baggageBelt', 'N/A')
    
    # Distancia
    distance = flight_data.get('greatCircleDistance', {}).get('km', 'N/A')
    
    # Mostrar información en dos columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌍 Origen")
        st.markdown(f"**{dep_city}** ({dep_iata})")
        st.markdown(f"Aeropuerto: {dep_name}")
        st.markdown(f"Terminal: {dep_terminal} • Puerta: {dep_gate}")
        st.markdown("##### ⏰ Horarios")
        st.markdown(f"**Programado:** {dep_scheduled}")
        st.markdown(f"**Revisado:** {dep_revised}")
    
    with col2:
        st.markdown("### 🌍 Destino")
        st.markdown(f"**{arr_city}** ({arr_iata})")
        st.markdown(f"Aeropuerto: {arr_name}")
        st.markdown(f"Terminal: {arr_terminal} • Puerta: {arr_gate} • <span style='color: red; font-weight: bold;'>Banda: {arr_belt}</span>", unsafe_allow_html=True)
        st.markdown("##### ⏰ Horarios")
        st.markdown(f"**Programado:** {arr_scheduled}")
        st.markdown(f"**Revisado:** {arr_revised}")
        st.markdown(f"**Estimado:** {arr_predicted}")
    
    st.markdown(f"**Distancia:** {distance} km")

def render_flight_status_tab(client) -> None:
    """
    Renderiza la pestaña de Estado de Vuelo en tiempo real.
    
    Args:
        client: Cliente de Supabase (no utilizado, pero mantenido por consistencia)
    """
    st.header("Estado de Vuelo en Tiempo Real")
    
    # Input para el número de vuelo
    col1, col2 = st.columns([3, 1])
    with col1:
        flight_number = st.text_input(
            "Número de Vuelo",
            value="",
            placeholder="Ejemplo: AV204",
            help="Ingresa el número de vuelo de Avianca (ej: AV204, AV626, AV254)",
        ).strip()
    
    with col2:
        search_button = st.button("🔍 Buscar", use_container_width=True)
    
    # Input para la fecha personalizada
    custom_date = st.date_input("Fecha de Salida", value=date.today(), help="Selecciona la fecha de salida del vuelo")
    
    # Mostrar información si se presiona el botón y hay un número de vuelo
    if search_button and flight_number:
        # Validación básica
        if not flight_number:
            st.warning("Por favor, ingresa un número de vuelo.")
            return
        
        # Convertir la fecha personalizada a string
        custom_date_str = custom_date.strftime("%Y-%m-%d") if custom_date else None
        
        # Mostrar indicador de carga
        with st.spinner(f"Consultando estado del vuelo {flight_number} para la fecha {custom_date_str or 'hoy'}..."):
            flight_data = fetch_flight_status(flight_number, custom_date_str)
        
        # Mostrar resultados o error
        if not flight_data:
            st.error(f"No se pudo obtener información para el vuelo {flight_number}. Intenta con otro número de vuelo.")
            return
        
        if len(flight_data) == 0:
            st.warning(f"No hay datos disponibles para el vuelo {flight_number}.")
            return
        
        # Usar el primer resultado (normalmente solo hay uno para un número de vuelo específico)
        flight_info = flight_data[0]
        
        # Mostrar tarjeta de información del vuelo
        render_flight_info_card(flight_info)

        # Mostrar progreso del vuelo
        st.subheader("Progreso del Vuelo")
        try:
            fig = create_flight_progress_chart(flight_info)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.exception(f"Error al generar gráfico de progreso: {e}")
            st.error(f"Error al generar gráfico de progreso: {str(e)}")

        # Mostrar ruta
        display_route_info(flight_info)
        
        # Mostrar última actualización
        last_update = flight_info.get('lastUpdatedUtc', 'Desconocido')
        if last_update != 'Desconocido':
            try:
                update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                update_str = update_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                st.caption(f"Última actualización: {update_str}")
            except:
                st.caption(f"Última actualización: {last_update}")
        
        # Mostrar visualizaciones
        st.subheader("Visualizaciones")

        # Seleccionar visualización
        viz_type = st.radio(
            "Seleccione el tipo de visualización:",
            options=["Mapa de Ruta"],  # Eliminado "Progreso del Vuelo"
            horizontal=True,
            key="viz_type"
        )

        # Mostrar visualización seleccionada
        try:
            if viz_type == "Mapa de Ruta":
                fig = create_flight_map(flight_info)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.exception(f"Error al generar visualización: {e}")
            st.error(f"Error al generar visualización: {str(e)}")