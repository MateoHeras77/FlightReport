import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.config.logging_config import setup_logger
from src.components.data_processing.time_utils import convert_time_string_to_datetime, handle_midnight_crossover
from src.components.data_processing.event_processing import calculate_average_event_times

# Configurar logger
logger = setup_logger()

def create_cascade_timeline_chart(flight_data) -> Optional[go.Figure]:
    """
    Crea una gráfica de cascada con los eventos del vuelo.
    
    Args:
        flight_data: Diccionario con los datos del vuelo o lista de diccionarios para múltiples vuelos
        
    Returns:
        go.Figure: Gráfica de línea de tiempo
    """
    try:
        # Determinar si estamos manejando un solo vuelo o múltiples vuelos usando type() en lugar de isinstance()
        is_multiple_flights = type(flight_data) is list
        flights_to_process = flight_data if is_multiple_flights else [flight_data]
        
        # Eventos a mostrar en el orden correcto
        events = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", 
            "flight_secure", "cierre_de_puerta", "push_back", "std", "atd"
        ]
        
        # Nombres de eventos para mostrar
        event_labels = {
            "std": "STD (Salida Programada)",
            "atd": "ATD (Salida Real)",
            "groomers_in": "Groomers In",
            "groomers_out": "Groomers Out",
            "crew_at_gate": "Crew at Gate",
            "ok_to_board": "OK to Board",
            "flight_secure": "Flight Secure",
            "cierre_de_puerta": "Cierre de Puerta",
            "push_back": "Push Back"
        }
        
        if is_multiple_flights:
            # Calcular tiempos promedio para múltiples vuelos
            average_times = calculate_average_event_times(flights_to_process)
            
            if not average_times:
                st.warning("No hay suficientes datos para calcular tiempos promedio")
                return None
            
            # Crear un diccionario con los tiempos promedio
            events_dict = average_times
            
            # Usar la fecha del primer vuelo como referencia
            reference_date = flights_to_process[0].get("flight_date")
            if not reference_date:
                st.error("No hay fecha de vuelo disponible")
                return None
        else:
            # Procesar un solo vuelo
            flight_date = flight_data.get("flight_date")
            if not flight_date:
                st.error("No hay fecha de vuelo disponible")
                return None
                
            # Convertir a string si es un objeto datetime.date
            if hasattr(flight_date, 'isoformat'):
                flight_date = flight_date.isoformat()
                
            events_dict = {}
            for event in events:
                time_obj = flight_data.get(event)
                if time_obj:
                    events_dict[event] = convert_time_string_to_datetime(flight_date, time_obj)
                else:
                    events_dict[event] = None
                    
            # Manejar eventos que cruzan la medianoche
            events_dict = handle_midnight_crossover(events_dict, flight_date)
        
        # Filtrar eventos nulos
        events_dict = {k: v for k, v in events_dict.items() if v is not None}
        
        if not events_dict:
            st.warning("No hay datos de eventos para mostrar")
            return None
            
        # Ordenar los eventos por su tiempo (ascendente)
        sorted_events = sorted(
            [(event, time) for event, time in events_dict.items()],
            key=lambda x: x[1]
        )
        
        # Crear la figura
        fig = go.Figure()
        
        # Colores para los eventos
        colors = {
            "groomers_in": "#1f77b4",
            "groomers_out": "#ff7f0e",
            "crew_at_gate": "#2ca02c",
            "ok_to_board": "#d62728",
            "flight_secure": "#9467bd",
            "cierre_de_puerta": "#8c564b",
            "push_back": "#e377c2",
            "std": "#7f7f7f",
            "atd": "#bcbd22"
        }
        
        # Para cada evento, crear una barra horizontal que va desde su tiempo hasta el tiempo del siguiente evento
        for i in range(len(sorted_events) - 1):
            current_event, current_time = sorted_events[i]
            next_event, next_time = sorted_events[i + 1]
            
            # Asegurarse de que los tiempos sean diferentes para evitar duración cero
            if current_time == next_time:
                next_time = current_time + timedelta(minutes=1)  # Añadir 1 minuto si son iguales
            
            # Calcular la duración en minutos
            duration_minutes = max(1, (next_time - current_time).total_seconds() / 60)  # Mínimo 1 minuto
            
            # Crear barra para el evento actual
            fig.add_trace(go.Bar(
                y=[duration_minutes],  # Duración en minutos como valor numérico para el eje Y
                x=[event_labels[current_event]],  # Evento en el eje X
                orientation='v',  # Barras verticales
                name=event_labels[current_event],
                marker=dict(color=colors.get(current_event, "#636363")),
                text=[f"{int(duration_minutes)} min"],  # Mostrar duración en minutos
                textposition="inside",  # Texto dentro de la barra
                insidetextanchor="middle",  # Alinear en el medio
                hoverinfo="text",
                hovertext=[f"{current_event}: {current_time.strftime('%H:%M')} - Duración: {int(duration_minutes)} min"],
                base=[current_time],  # Punto de inicio de la barra
                showlegend=False
            ))
            
        # Para el último evento, mostrar solo un punto 
        last_event, last_time = sorted_events[-1]
        fig.add_trace(go.Scatter(
            y=[last_time],
            x=[event_labels[last_event]],
            mode='markers+text',
            name=event_labels[last_event],
            marker=dict(size=14, symbol='circle', color=colors.get(last_event, "#636363")),
            text=[last_time.strftime('%H:%M')],
            textposition="top center",
            hoverinfo="text",
            hovertext=[f"{event_labels[last_event]}: {last_time.strftime('%H:%M')}"]
        ))
        
        # Determinar el rango de tiempo para el eje Y
        all_times = [time for _, time in sorted_events]
        min_time = min(all_times)
        max_time = max(all_times)
        
        # Añadir un margen de tiempo
        time_margin = timedelta(minutes=30)
        plot_min_time = min_time - time_margin
        plot_max_time = max_time + time_margin
        
        # Crear rangos de tiempo para el eje Y
        time_range = pd.date_range(plot_min_time, plot_max_time, freq='15min')
        
        # Ordenar los nombres de los eventos según su secuencia operativa
        operational_order = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", 
            "flight_secure", "cierre_de_puerta", "push_back", "std", "atd"
        ]
        
        # Filtrar para incluir solo eventos presentes
        operational_order = [e for e in operational_order if e in events_dict]
        
        # Formato del gráfico
        title = "Secuencia de Eventos"
        if is_multiple_flights:
            title += f" - Promedio de {len(flights_to_process)} Vuelos"
        else:
            title += f" - Vuelo {flight_data.get('flight_number', 'N/A')} ({flight_data.get('flight_date', 'N/A')})"
            
        fig.update_layout(
            title=title,
            yaxis=dict(  # Ahora el eje Y es el tiempo
                title='Hora',
                tickformat='%H:%M',
                tickmode='array',
                tickvals=time_range,
                ticktext=[t.strftime('%H:%M') for t in time_range]
            ),
            xaxis=dict(  # Ahora el eje X son los eventos
                title='Eventos',
                categoryorder='array',
                categoryarray=[event_labels[e] for e in operational_order]
            ),
            height=500,
            barmode='overlay',
            bargap=0.2,
            margin=dict(l=20, r=20, t=60, b=60)
        )
        
        # Añadir anotaciones para cada barra con su tiempo y duración
        for i, (event, event_time) in enumerate(sorted_events[:-1]):  # Excluir el último evento
            next_event, next_time = sorted_events[i + 1]
            duration_minutes = int((next_time - event_time).total_seconds() / 60)
            
            fig.add_annotation(
                x=event_labels[event],
                y=event_time + (next_time - event_time)/2,  # Punto medio de la barra
                text=f"{duration_minutes} min",
                showarrow=False,
                font=dict(size=12, color="white"),
                xanchor='center',
                yanchor='middle'
            )
        
        return fig
    except Exception as e:
        logger.exception(f"Error al crear gráfico de cascada: {e}")
        st.error(f"Error al crear gráfico: {str(e)}")
        return None