import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, cast
import plotly.graph_objects as go

from src.config.logging_config import setup_logger
from src.components.data_processing.time_utils import convert_time_string_to_datetime, handle_midnight_crossover
from src.components.data_processing.event_processing import calculate_average_event_times

# Configurar logger
logger = setup_logger()

def create_combined_events_chart(flight_data) -> Optional[go.Figure]:
    """
    Crea un gráfico de barras con eventos combinados que muestra la duración de procesos específicos.
    
    Args:
        flight_data: Diccionario con los datos del vuelo o lista de diccionarios para múltiples vuelos
        
    Returns:
        go.Figure: Gráfica de barras con eventos combinados
    """
    try:
        # Determinar si estamos manejando un solo vuelo o múltiples vuelos usando type() en lugar de isinstance()
        is_multiple_flights = type(flight_data) is list
        flights_to_process = flight_data if is_multiple_flights else [flight_data]
        
        # Eventos necesarios para los cálculos
        required_events = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", "flight_secure"
        ]
        
        # Nombres descriptivos para los eventos combinados
        combined_event_labels = {
            "groomers_total": "Groomers Total",
            "revision_avion": "Revisión del Avión",
            "boarding": "Boarding"
        }
        
        # Colores para los eventos combinados
        colors = {
            "groomers_total": "#1f77b4",
            "revision_avion": "#2ca02c",
            "boarding": "#9467bd"
        }
        
        if is_multiple_flights:
            # Calcular tiempos promedio para múltiples vuelos
            average_times = calculate_average_event_times(flights_to_process)
            
            if not average_times:
                st.warning("No hay suficientes datos para calcular tiempos promedio")
                return None
            
            # Crear un diccionario con los tiempos promedio
            events_dict = average_times
        else:
            # Procesar un solo vuelo
            flight_date = flight_data.get("flight_date")
            if not flight_date:
                st.error("No hay fecha de vuelo disponible")
                return None
                
            # Convertir a string si es un objeto datetime.date
            if hasattr(flight_date, 'isoformat'):
                flight_date = flight_date.isoformat()
                
            # Convertir todos los eventos requeridos a datetime
            events_dict = {}
            for event in required_events:
                time_obj = flight_data.get(event)
                if time_obj:
                    events_dict[event] = convert_time_string_to_datetime(flight_date, time_obj)
                else:
                    events_dict[event] = None
                    
            # Manejar eventos que cruzan la medianoche
            events_dict = handle_midnight_crossover(events_dict, flight_date)
        
        # Verificar si tenemos todos los eventos necesarios para cada evento combinado
        combined_events = {}
        durations = {}
        
        # 1. Groomers Total = groomers_out - groomers_in
        if events_dict.get("groomers_in") and events_dict.get("groomers_out"):
            start_time = events_dict["groomers_in"]
            end_time = events_dict["groomers_out"]
            
            # Asegurarse de que el tiempo final es posterior al inicial
            if end_time <= start_time:
                # Si el tiempo final es anterior o igual al inicial, podría ser un cruce de medianoche no detectado
                logger.warning(f"Posible cruce de medianoche no detectado en Groomers: {start_time} -> {end_time}")
                # Intentar ajustar añadiendo un día al tiempo final
                end_time_adjusted = end_time + timedelta(days=1)
                duration = (end_time_adjusted - start_time).total_seconds() / 60
                
                # Solo aplicar el ajuste si la duración resultante es razonable (menos de 12 horas)
                if duration < 12 * 60:
                    logger.info(f"Ajustando tiempo final de Groomers: {end_time} -> {end_time_adjusted}")
                    combined_events["groomers_total"] = (start_time, end_time_adjusted)
                    durations["groomers_total"] = duration
            else:
                # Caso normal: el tiempo final es posterior al inicial
                combined_events["groomers_total"] = (start_time, end_time)
                duration = (end_time - start_time).total_seconds() / 60
                durations["groomers_total"] = duration
        
        # 2. Revisión del Avión = Ok_to_Board - crew_at_gate
        if events_dict.get("crew_at_gate") and events_dict.get("ok_to_board"):
            start_time = events_dict["crew_at_gate"]
            end_time = events_dict["ok_to_board"]
            
            # Asegurarse de que el tiempo final es posterior al inicial
            if end_time <= start_time:
                # Si el tiempo final es anterior o igual al inicial, podría ser un cruce de medianoche no detectado
                logger.warning(f"Posible cruce de medianoche no detectado en Revisión: {start_time} -> {end_time}")
                # Intentar ajustar añadiendo un día al tiempo final
                end_time_adjusted = end_time + timedelta(days=1)
                duration = (end_time_adjusted - start_time).total_seconds() / 60
                
                # Solo aplicar el ajuste si la duración resultante es razonable (menos de 12 horas)
                if duration < 12 * 60:
                    logger.info(f"Ajustando tiempo final de Revisión: {end_time} -> {end_time_adjusted}")
                    combined_events["revision_avion"] = (start_time, end_time_adjusted)
                    durations["revision_avion"] = duration
            else:
                # Caso normal: el tiempo final es posterior al inicial
                combined_events["revision_avion"] = (start_time, end_time)
                duration = (end_time - start_time).total_seconds() / 60
                durations["revision_avion"] = duration
        
        # 3. Boarding = flight_secure - Ok_to_Board
        if events_dict.get("ok_to_board") and events_dict.get("flight_secure"):
            start_time = events_dict["ok_to_board"]
            end_time = events_dict["flight_secure"]
            
            # Asegurarse de que el tiempo final es posterior al inicial
            if end_time <= start_time:
                # Si el tiempo final es anterior o igual al inicial, podría ser un cruce de medianoche no detectado
                logger.warning(f"Posible cruce de medianoche no detectado en Boarding: {start_time} -> {end_time}")
                # Intentar ajustar añadiendo un día al tiempo final
                end_time_adjusted = end_time + timedelta(days=1)
                duration = (end_time_adjusted - start_time).total_seconds() / 60
                
                # Solo aplicar el ajuste si la duración resultante es razonable (menos de 12 horas)
                if duration < 12 * 60:
                    logger.info(f"Ajustando tiempo final de Boarding: {end_time} -> {end_time_adjusted}")
                    combined_events["boarding"] = (start_time, end_time_adjusted)
                    durations["boarding"] = duration
            else:
                # Caso normal: el tiempo final es posterior al inicial
                combined_events["boarding"] = (start_time, end_time)
                duration = (end_time - start_time).total_seconds() / 60
                durations["boarding"] = duration
        
        # Si no hay eventos combinados válidos, mostrar mensaje y salir
        if not combined_events:
            st.warning("No hay suficientes datos para mostrar eventos combinados")
            return None
            
        # Crear la figura
        fig = go.Figure()
        
        # Datos para el gráfico
        bar_data = []
        
        # Crear datos para cada evento combinado
        for event_key, (start_time, end_time) in combined_events.items():
            duration = durations[event_key]
            
            # Información para el tooltip
            if event_key == "groomers_total":
                start_label = "Groomers In"
                end_label = "Groomers Out"
            elif event_key == "revision_avion":
                start_label = "Crew at Gate"
                end_label = "OK to Board"
            elif event_key == "boarding":
                start_label = "OK to Board"
                end_label = "Flight Secure"
            else:
                start_label = "Inicio"
                end_label = "Fin"
            
            hover_text = f"{combined_event_labels[event_key]}<br>" \
                       f"Inicio: {start_label} ({start_time.strftime('%H:%M')})<br>" \
                       f"Fin: {end_label} ({end_time.strftime('%H:%M')})<br>" \
                       f"Duración: {int(duration)} minutos"
            
            bar_data.append({
                "Evento": combined_event_labels[event_key],
                "Duración": duration,
                "Inicio": start_time,
                "Fin": end_time,
                "HoverText": hover_text
            })
        
        # Crear DataFrame para el gráfico
        df = pd.DataFrame(bar_data)
        
        # Ordenar los eventos en el orden deseado
        event_order = ["Groomers Total", "Revisión del Avión", "Boarding"]
        df["Evento"] = pd.Categorical(df["Evento"], categories=event_order, ordered=True)
        df = df.sort_values("Evento")
        
        # Crear el gráfico de barras
        fig = px.bar(
            df,
            x="Evento",
            y="Duración",
            color="Evento",
            color_discrete_map={
                "Groomers Total": colors["groomers_total"],
                "Revisión del Avión": colors["revision_avion"],
                "Boarding": colors["boarding"]
            },
            text="Duración",
            hover_data=["Inicio", "Fin"],
            custom_data=["HoverText"]
        )
        
        # Personalizar el tooltip
        fig.update_traces(
            hovertemplate="%{customdata[0]}",
            texttemplate="%{y:.0f} min",
            textposition="inside"
        )
        
        # Formato del gráfico
        title = "Duración de Procesos"
        if is_multiple_flights:
            title += f" - Promedio de {len(flights_to_process)} Vuelos"
        else:
            title += f" - Vuelo {flight_data.get('flight_number', 'N/A')} ({flight_data.get('flight_date', 'N/A')})"
            
        fig.update_layout(
            title=title,
            xaxis_title="Procesos",
            yaxis_title="Duración (minutos)",
            height=500,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=60)
        )
        
        return fig
    except Exception as e:
        logger.exception(f"Error al crear gráfico de eventos combinados: {e}")
        st.error(f"Error al crear gráfico: {str(e)}")
        return None