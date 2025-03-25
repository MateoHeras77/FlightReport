import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go

from src.config.logging_config import setup_logger
from src.components.data_processing.time_utils import convert_time_string_to_datetime, handle_midnight_crossover
from src.components.data_processing.event_processing import calculate_average_event_times

# Configurar logger
logger = setup_logger()

def create_gantt_chart(flight_data) -> Optional[go.Figure]:
    """
    Crea un diagrama de Gantt con los eventos del vuelo.
    
    Args:
        flight_data: Diccionario con los datos del vuelo o lista de diccionarios para múltiples vuelos
        
    Returns:
        go.Figure: Gráfica de línea de tiempo tipo Gantt
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
        
        # Verificar eventos con la misma hora de inicio
        modified_sorted_events = []
        i = 0
        while i < len(sorted_events):
            current_event, current_time = sorted_events[i]
            
            # Si es el último evento o el siguiente evento tiene tiempo diferente, no hay problema
            if i == len(sorted_events) - 1 or sorted_events[i+1][1] != current_time:
                modified_sorted_events.append((current_event, current_time))
                i += 1
                continue
            
            # Grupo de eventos con la misma hora de inicio
            same_time_events = [(current_event, current_time)]
            
            # Encuentra todos los eventos que ocurren al mismo tiempo
            j = i + 1
            while j < len(sorted_events) and sorted_events[j][1] == current_time:
                same_time_events.append(sorted_events[j])
                j += 1
            
            # Determinar la hora de fin para estos eventos
            end_time = None
            if j < len(sorted_events):
                end_time = sorted_events[j][1]  # El siguiente evento con diferente hora
            else:
                # Si todos los eventos restantes tienen la misma hora, añadir un pequeño incremento
                end_time = current_time + timedelta(minutes=5)
            
            # Distribuir los eventos uniformemente en el intervalo
            interval = (end_time - current_time) / len(same_time_events)
            
            for k, (event, _) in enumerate(same_time_events):
                if k == len(same_time_events) - 1:
                    # El último evento de este grupo termina en el tiempo final
                    modified_sorted_events.append((event, current_time + k * interval))
                else:
                    # Los demás eventos tienen duración uniforme
                    modified_sorted_events.append((event, current_time + k * interval))
            
            i = j  # Saltar al siguiente grupo de eventos
        
        sorted_events = modified_sorted_events
        
        # Preparar datos para el diagrama de Gantt usando plotly.express
        gantt_data = []
        
        for i in range(len(sorted_events) - 1):
            current_event, current_time = sorted_events[i]
            next_event, next_time = sorted_events[i + 1]
            
            # Asegurarse de que los tiempos sean diferentes para evitar duración cero
            if current_time == next_time:
                next_time = current_time + timedelta(minutes=1)  # Añadir 1 minuto si son iguales
            
            # Calcular la duración en segundos (asegurar que sea positiva)
            duration_seconds = max(60, (next_time - current_time).total_seconds())  # Mínimo 60 segundos
            
            gantt_data.append({
                "Task": event_labels[current_event],
                "Start": current_time,
                "Finish": next_time,
                "Duration": duration_seconds / 60,  # Convertir a minutos
                "Event": current_event,
                "Time": current_time.strftime("%H:%M")
            })
            
        # Para el último evento, añadir una duración fija de 5 minutos
        last_event, last_time = sorted_events[-1]
        end_time = last_time + timedelta(minutes=5)
        
        gantt_data.append({
            "Task": event_labels[last_event],
            "Start": last_time,
            "Finish": end_time,
            "Duration": 5,  # 5 minutos
            "Event": last_event,
            "Time": last_time.strftime("%H:%M")
        })
        
        # Crear DataFrame para Gantt chart
        df = pd.DataFrame(gantt_data)
        
        # Colores para los eventos
        colors_discrete_map = {
            "Groomers In": "#1f77b4",
            "Groomers Out": "#ff7f0e",
            "Crew at Gate": "#2ca02c",
            "OK to Board": "#d62728",
            "Flight Secure": "#9467bd",
            "Cierre de Puerta": "#8c564b",
            "Push Back": "#e377c2",
            "STD (Salida Programada)": "#7f7f7f",
            "ATD (Salida Real)": "#bcbd22"
        }
        
        # Crear el gráfico de Gantt utilizando Express
        fig = px.timeline(
            df, 
            x_start="Start", 
            x_end="Finish", 
            y="Task",
            color="Task",
            color_discrete_map=colors_discrete_map,
            hover_data=["Time", "Duration"]
        )
        
        # Después de crear el gráfico, invertimos los ejes con update_layout
        fig.update_layout(
            # Intercambiar definiciones de ejes
            xaxis=dict(
                title='Hora',
                tickformat='%H:%M',
            ),
            yaxis=dict(
                title='Eventos',
            )
        )
        
        # Añadir texto a cada barra con la duración
        for i, row in df.iterrows():
            # Calcular el punto medio usando microsegundos para evitar problemas con los tipos Timestamp
            midpoint = pd.Timestamp(row["Start"].value / 2 + row["Finish"].value / 2)
            
            fig.add_annotation(
                x=midpoint,
                y=row["Task"],
                text=f"{int(row['Duration'])} min",
                showarrow=False,
                font=dict(size=10, color="white"),
                xanchor="center",
                yanchor="middle"
            )
        
        # Ordenar los nombres de los eventos según su secuencia operativa
        operational_order = [
            "Groomers In", "Groomers Out", "Crew at Gate", "OK to Board", 
            "Flight Secure", "Cierre de Puerta", "Push Back", "STD (Salida Programada)", "ATD (Salida Real)"
        ]
        
        # Filtrar para incluir solo eventos presentes
        operational_order = [event_labels[e] for e in events if e in events_dict]
        
        # Determinar el rango de tiempo para el eje X
        all_times = [row["Start"] for _, row in df.iterrows()]
        min_time = min(all_times)
        max_time = df["Finish"].max()
        
        # Añadir un margen de tiempo
        time_margin = timedelta(minutes=15)
        plot_min_time = min_time - time_margin
        plot_max_time = max_time + time_margin
        
        # Crear rangos de tiempo para el eje X
        time_range = pd.date_range(plot_min_time, plot_max_time, freq='15min')
        
        # Formato final del gráfico
        title = "Secuencia de Eventos"
        if is_multiple_flights:
            title += f" - Promedio de {len(flights_to_process)} Vuelos"
        else:
            title += f" - Vuelo {flight_data.get('flight_number', 'N/A')} ({flight_data.get('flight_date', 'N/A')})"
            
        fig.update_layout(
            title=title,
            xaxis=dict(
                title='Hora',
                tickformat='%H:%M',
                tickmode='array',
                tickvals=time_range,
                ticktext=[t.strftime('%H:%M') for t in time_range],
                side="top"
            ),
            yaxis=dict(
                title='Eventos',
                categoryorder='array',
                categoryarray=operational_order
            ),
            height=500,
            margin=dict(l=20, r=20, t=60, b=60),
            showlegend=False
        )
        
        return fig
    except Exception as e:
        logger.exception(f"Error al crear diagrama de Gantt: {e}")
        st.error(f"Error al crear diagrama: {str(e)}")
        return None