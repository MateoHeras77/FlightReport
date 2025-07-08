import streamlit as st
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Any, Optional

from src.config.logging_config import setup_logger
from src.config.supabase_config import DEFAULT_TABLE_NAME
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
        List[Dict]: Lista de datos de vuelos
    """
    try:
        # Iniciar consulta a Supabase
        query = client.table(DEFAULT_TABLE_NAME).select("*")
        
        # Aplicar filtros si existen
        if date:
            # Registrar la fecha para depuración
            logger.info(f"Filtrando por fecha: {date} (tipo: {type(date).__name__})")
            query = query.eq("flight_date", date)
        
        if flight_number:
            # Registrar el número de vuelo para depuración
            logger.info(f"Filtrando por vuelo: {flight_number}")
            query = query.eq("flight_number", flight_number)
        
        if created_at:
            # Registrar el timestamp de creación para depuración
            logger.info(f"Filtrando por timestamp de creación: {created_at}")
            query = query.eq("created_at", created_at)
            
        # Ordenar resultados
        query = query.order("flight_date", desc=True).order("std", desc=True)
        
        logger.info(f"Ejecutando consulta a Supabase en tabla: {DEFAULT_TABLE_NAME}")
        
        # Ejecutar consulta
        response = query.execute()
        
        # Verificar si hay errores
        if hasattr(response, 'error') and response.error is not None:
            logger.error(f"Error en la consulta a Supabase: {response.error}")
            return []
        
        # Convertir resultados a lista de diccionarios
        flights_data = response.data
        
        # Registrar la cantidad de resultados para depuración
        logger.info(f"Consulta exitosa. Resultados obtenidos: {len(flights_data)}")
        if len(flights_data) > 0:
            # Mostrar las claves del primer resultado para depuración
            logger.info(f"Claves disponibles en los datos: {list(flights_data[0].keys())}")
        
        return flights_data
    except Exception as e:
        logger.exception(f"Error al obtener datos de vuelo: {e}")
        st.error(f"Error al obtener datos: {str(e)}")
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
        # Consulta para fechas únicas
        logger.info(f"Consultando fechas únicas en tabla: {DEFAULT_TABLE_NAME}")
        dates_response = client.table(DEFAULT_TABLE_NAME).select("flight_date").execute()
        
        # Consulta para números de vuelo únicos
        logger.info(f"Consultando números de vuelo únicos en tabla: {DEFAULT_TABLE_NAME}")
        flights_response = client.table(DEFAULT_TABLE_NAME).select("flight_number").execute()
        
        if hasattr(dates_response, 'error') and dates_response.error is not None:
            logger.error(f"Error al obtener fechas: {dates_response.error}")
            dates = []
        else:
            all_dates = [item['flight_date'] for item in dates_response.data]
            dates = sorted(list(set(all_dates)), reverse=True)
        
        if hasattr(flights_response, 'error') and flights_response.error is not None:
            logger.error(f"Error al obtener números de vuelo: {flights_response.error}")
            flight_numbers = []
        else:
            all_flights = [item['flight_number'] for item in flights_response.data]
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
        st.error(f"Error en la visualización: {str(e)}")

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
                st.write(f"⏰ **Salida Tripulación:** {flight.get('crew_departure', 'N/A')}")
                st.write(f"👷 **Agentes Groomers:** {flight.get('number_groomers_agents', 'N/A')}")
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
        "Salida de Tripulación": flight.get('crew_departure'),
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

    # Mostrar tabla de horarios    st.dataframe(time_data, hide_index=True)