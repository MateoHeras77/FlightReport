import streamlit as st
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Any, Optional

from src.config.logging_config import setup_logger
from src.config.supabase_config import DEFAULT_TABLE_NAME
from src.services.supabase_service import fetch_data_from_supabase, SupabaseReadError
from src.components.charts.gantt_chart import create_gantt_chart
from src.components.charts.bar_chart import create_cascade_timeline_chart
from src.components.charts.combined_events_chart import create_combined_events_chart

# Configurar logger
logger = setup_logger()

def fetch_flight_data_for_chart(client, date=None, flight_number=None, created_at=None):
    """
    Obtiene datos de vuelos desde Supabase con filtros opcionales.
    
    Args:
        client: Cliente de Supabase
        date: Fecha para filtrar (opcional)
        flight_number: Número de vuelo para filtrar (opcional)
        created_at: Timestamp de creación para filtrar (opcional)
        
    Returns:
        List[Dict]: List of flight data.
    """
    query_params = {}
    if date:
        logger.info(f"Filtering by date: {date} (type: {type(date).__name__})")
        query_params["flight_date"] = date
    if flight_number:
        logger.info(f"Filtering by flight number: {flight_number}")
        query_params["flight_number"] = flight_number
    if created_at:
        logger.info(f"Filtering by creation timestamp: {created_at}")
        query_params["created_at"] = created_at
    
    # Note: Ordering is not directly supported by the current fetch_data_from_supabase
    # This would need to be handled post-fetch or by enhancing fetch_data_from_supabase
    # For now, we'll fetch and then sort if needed, or rely on default table order.
    # query = query.order("flight_date", desc=True).order("std", desc=True)

    try:
        logger.info(f"Fetching flight data from Supabase table: {DEFAULT_TABLE_NAME} with params: {query_params}")
        # Assuming fetch_data_from_supabase can handle an empty query_params dict for "select all"
        flights_data = fetch_data_from_supabase(client, DEFAULT_TABLE_NAME, query_params if query_params else None)
        
        logger.info(f"Query successful. Results obtained: {len(flights_data)}")
        if len(flights_data) > 0 and flights_data[0] is not None: # Check if flights_data[0] is not None
            logger.info(f"Available keys in data: {list(flights_data[0].keys())}")
        
        # Implement sorting here if necessary, e.g., by flight_date and std
        if flights_data:
            flights_data.sort(key=lambda x: (x.get('flight_date', ''), x.get('std', '')), reverse=True)

        return flights_data
    except SupabaseReadError as e:
        logger.error(f"Error fetching flight data from Supabase: {e}", exc_info=True)
        st.error(f"Error fetching data: {str(e)}")
        return []
    except Exception as e: # Catch any other unexpected errors
        logger.exception(f"Unexpected error fetching flight data: {e}")
        st.error(f"Unexpected error fetching data: {str(e)}")
        return []

def render_timeline_tab(client):
    """
    Renderiza la pestaña de visualización de línea de tiempo.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    st.header("Visualización de Eventos de Vuelo")
    
    if not client:
        st.error("No hay conexión con Supabase. Verifique la configuración.")
        return

    # Inicializar session_state para datos preliminares y finales
    if "preliminary_data" not in st.session_state:
        st.session_state.preliminary_data = None
    if "created_at_filter" not in st.session_state:
        st.session_state.created_at_filter = None
    if "flights_data" not in st.session_state:
        st.session_state.flights_data = None

    # Obtener todas las fechas y números de vuelo disponibles para los filtros
    try:
        logger.info(f"Fetching unique flight dates from table: {DEFAULT_TABLE_NAME}")
        # fetch_data_from_supabase expects query_params for specific columns,
        # but here we need distinct values. This might require a more specific utility
        # or adjusting fetch_data_from_supabase to handle column selection.
        # For now, let's assume we fetch all and process, or this part needs a dedicated function.
        # This part is tricky as fetch_data_from_supabase selects ALL columns ("*")
        # We'll fetch all data and then extract unique dates and flight numbers.
        # This is inefficient but works with the current fetch_data_from_supabase.
        # A better approach would be to enhance fetch_data_from_supabase or add new specific functions.
        
        all_data_for_filters = fetch_data_from_supabase(client, DEFAULT_TABLE_NAME) # Fetches all data

        if not all_data_for_filters: # Check if data is empty or None
            dates = []
            flight_numbers = []
            st.warning("No data available to populate filters.")
        else:
            all_dates = [item['flight_date'] for item in all_data_for_filters if item and 'flight_date' in item]
            dates = sorted(list(set(all_dates)), reverse=True)
            
            all_flights = [item['flight_number'] for item in all_data_for_filters if item and 'flight_number' in item]
            flight_numbers = sorted(list(set(all_flights)))

        # Filtros para seleccionar fecha y vuelo
        col1, col2 = st.columns(2)
        
        with col1:
            selected_date = st.selectbox(
                "Seleccione fecha:",
                options=["Todas"] + dates,
                index=0
            )
            
        with col2:
            selected_flight = st.selectbox(
                "Seleccione número de vuelo:",
                options=["Todos"] + flight_numbers,
                index=0
            )
            
        # Convertir "Todas"/"Todos" a None para la función de búsqueda
        date_filter = None if selected_date == "Todas" else selected_date
        flight_filter = None if selected_flight == "Todos" else selected_flight
        
        # Botón para buscar datos iniciales
        if st.button("Buscar Datos Iniciales"):
            logger.info(f"Filtros aplicados - Fecha: {date_filter}, Vuelo: {flight_filter}")
            st.session_state.preliminary_data = fetch_flight_data_for_chart(client, date_filter, flight_filter)
            st.session_state.created_at_filter = None  # Reiniciar filtro de timestamp
            st.session_state.flights_data = None  # Reiniciar datos finales
        
        # Mostrar selectbox para timestamp si hay datos preliminares
        if st.session_state.preliminary_data:
            created_at_values = []
            for item in st.session_state.preliminary_data:
                if 'created_at' in item and item['created_at']:
                    try:
                        dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                        formatted_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
                        created_at_values.append((formatted_dt, item['created_at']))
                    except Exception as e:
                        logger.error(f"Error al formatear timestamp: {e}")
                        created_at_values.append((str(item['created_at']), item['created_at']))
            
            created_at_values = sorted(set(created_at_values), key=lambda x: x[0], reverse=True)
            display_values = ["Todos"] + [dt[0] for dt in created_at_values]
            raw_values = [None] + [dt[1] for dt in created_at_values]
            
            selected_index = st.selectbox(
                "Seleccione la fecha y hora de creación del reporte:",
                options=display_values,
                index=0
            )
            
            if selected_index != "Todos":
                selected_idx = display_values.index(selected_index)
                st.session_state.created_at_filter = raw_values[selected_idx]

        # Botón para buscar datos finales
        if st.button("Buscar Datos Finales"):
            st.session_state.flights_data = fetch_flight_data_for_chart(
                client,
                date_filter,
                flight_filter,
                st.session_state.created_at_filter
            )
        
        # Mostrar resultados finales si existen
        if st.session_state.flights_data:
            flights_data = st.session_state.flights_data
            if not flights_data:
                st.warning("No se encontraron vuelos con los filtros seleccionados.")
                return

            # Mover la selección del tipo de visualización al inicio
            st.subheader("Visualización de Eventos")
            chart_type = st.radio(
                "Seleccione el tipo de visualización:",
                options=["Gráfico de Gantt (Cascada)", "Gráfico de Barras", "Gráfico de Eventos Combinados"],
                horizontal=True
            )

            # Crear y mostrar el gráfico según selección
            try:
                if chart_type == "Gráfico de Gantt (Cascada)":
                    fig = create_gantt_chart(flights_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Gráfico de Eventos Combinados":
                    fig = create_combined_events_chart(flights_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = create_cascade_timeline_chart(flights_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                logger.exception(f"Error al mostrar gráfico: {e}")
                st.error(f"Error al generar el gráfico: {str(e)}")

            # Mostrar información del vuelo
            display_flight_details(flights_data)

            # Tabla de horarios
            if len(flights_data) == 1:
                display_flight_schedule(flights_data[0])
    except Exception as e:
        logger.exception(f"Error al renderizar la pestaña de línea de tiempo: {e}")
        st.error(f"Error in timeline visualization: {str(e)}")
    except SupabaseReadError as e: # Catch Supabase read errors for filter data fetching
        logger.error(f"Error fetching filter data for timeline tab: {e}", exc_info=True)
        st.error(f"Error loading filter options: {str(e)}")
    except Exception as e: # General error catch for the tab
        logger.exception(f"Error rendering timeline tab: {e}")
        st.error(f"Error in timeline visualization: {str(e)}")


def display_flight_details(flights):
    """
    Muestra información detallada de uno o varios vuelos.
    
    Args:
        flights: Lista de diccionarios con datos de vuelos
    """
    st.subheader("Información del Vuelo")
    
    # Crear contenedores para diferentes secciones de información
    for flight in flights:
        # Información básica del vuelo con emojis
        with st.container():
            st.markdown("##### ✈️ Información Básica")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"📅 **Fecha:** {flight.get('flight_date', 'N/A')}")
                st.write(f"🔢 **Número de Vuelo:** {flight.get('flight_number', 'N/A')}")
                st.write(f"📍 **Gate:** {flight.get('gate', 'N/A')}")
                st.write(f"🧳 **Gate Bag Status:** {flight.get('gate_bag', 'N/A')}")
            with col2:
                st.write(f"🌍 **Origen:** {flight.get('origin', 'N/A')}")
                st.write(f"✈️ **Destino:** {flight.get('destination', 'N/A')}")
                st.write(f"🎡 **Carrusel:** {flight.get('carrousel', 'N/A')}")
            with col3:
                st.write(f"⏰ **STD:** {flight.get('std', 'N/A')}")
                st.write(f"⏰ **ATD:** {flight.get('atd', 'N/A')}")
                st.write(f"⏳ **Delay:** {flight.get('delay', 'N/A')} min")

        # Información de pasajeros y servicios especiales con emojis
        with st.container():
            st.markdown("##### 👥 Información de Pasajeros y Servicios")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"👥 **Total Pax:** {flight.get('pax_ob_total', 'N/A')}")
                st.write(f"👤 **PAX C:** {flight.get('pax_c', 'N/A')}")
                st.write(f"👥 **PAX Y:** {flight.get('pax_y', 'N/A')}")
                st.write(f"👶 **Infantes:** {flight.get('infants', 'N/A')}")
            with col2:
                st.write(f"♿ **WCHR Vuelo Salida:** {flight.get('wchr_current_flight', 'N/A')}")
                st.write(f"👨‍✈️ **Agentes Vuelo Salida:** {flight.get('agents_current_flight', 'N/A')}")
                st.write(f"♿ **WCHR Vuelo Llegada:** {flight.get('wchr_previous_flight', 'N/A')}")
                st.write(f"👨‍✈️ **Agentes Vuelo Llegada:** {flight.get('agents_previous_flight', 'N/A')}")
            with col3:
                st.write(f"📋 **Customs In:** {flight.get('customs_in', 'N/A')}")
                st.write(f"📋 **Customs Out:** {flight.get('customs_out', 'N/A')}")
                st.write(f"📋 **Delay Code:** {flight.get('delay_code', 'N/A')}")

        # Eventos temporales con emojis
        with st.container():
            st.markdown("##### ⏰ Eventos Temporales")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"🧹 **Groomers In:** {flight.get('groomers_in', 'N/A')}")
                st.write(f"🧹 **Groomers Out:** {flight.get('groomers_out', 'N/A')}")
                st.write(f"👨‍✈️ **Crew at Gate:** {flight.get('crew_at_gate', 'N/A')}")
                st.write(f"✅ **OK to Board:** {flight.get('ok_to_board', 'N/A')}")
            with col2:
                st.write(f"🔒 **Flight Secure:** {flight.get('flight_secure', 'N/A')}")
                st.write(f"🚪 **Cierre de Puerta:** {flight.get('cierre_de_puerta', 'N/A')}")
                st.write(f"🚜 **Push Back:** {flight.get('push_back', 'N/A')}")

        # Información adicional con emojis
        with st.container():
            st.markdown("##### 📝 Información Adicional")
            if flight.get('comments'):
                st.write(f"💬 **Comentarios:** {flight.get('comments')}")
            col1, col2 = st.columns(2)
            with col1:
                if flight.get('created_at'):
                    try:
                        created_dt = datetime.fromisoformat(flight['created_at'].replace('Z', '+00:00'))
                        st.write(f"🕒 **Creado:** {created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        st.write(f"🕒 **Creado:** {flight.get('created_at', 'N/A')}")
            with col2:
                if flight.get('updated_at'):
                    try:
                        updated_dt = datetime.fromisoformat(flight['updated_at'].replace('Z', '+00:00'))
                        st.write(f"🕒 **Actualizado:** {updated_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        st.write(f"🕒 **Actualizado:** {flight.get('updated_at', 'N/A')}")
        
        # Línea divisoria entre vuelos si hay múltiples
        if len(flights) > 1:
            st.markdown("---")

def display_flight_schedule(flight):
    """
    Muestra la tabla de horarios de un vuelo.
    
    Args:
        flight: Diccionario con datos del vuelo
    """
    st.subheader("Horarios de Eventos")
    
    # Tabla de horarios sin incluir 'Customs'
    time_fields = {
        "STD": flight.get('std'),
        "ATD": flight.get('atd'),
        "Groomers In": flight.get('groomers_in'),
        "Groomers Out": flight.get('groomers_out'),
        "Crew at Gate": flight.get('crew_at_gate'),
        "OK to Board": flight.get('ok_to_board'),
        "Flight Secure": flight.get('flight_secure'),
        "Cierre de Puerta": flight.get('cierre_de_puerta'),
        "Push Back": flight.get('push_back')
    }

    # Crear un DataFrame para mostrar los horarios como tabla
    time_data = []
    for event, time_val in time_fields.items():
        # Formatear el tiempo para mostrarlo de manera legible
        if time_val is not None:
            if hasattr(time_val, 'strftime'):
                formatted_time = time_val.strftime("%H:%M")
            else:
                formatted_time = time_val
        else:
            formatted_time = "N/A"

        time_data.append({"Evento": event, "Hora": formatted_time})

    # Mostrar tabla de horarios
    st.dataframe(time_data, hide_index=True)