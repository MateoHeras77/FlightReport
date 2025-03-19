import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, time
import json
from typing import Dict, List, Any, Optional

from src.config.logging_config import setup_logger
from src.config.supabase_config import DEFAULT_TABLE_NAME

# Configurar logger
logger = setup_logger()

# Clase para manejar la serialización de timedelta a JSON
class TimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return (obj.days * 24 * 60 * 60 + obj.seconds) * 1000  # Convertir a milisegundos
        return super().default(obj)

def convert_time_string_to_datetime(date_str: str, time_obj) -> datetime:
    """
    Convierte una cadena de fecha y un objeto time a un objeto datetime.
    
    Args:
        date_str: Fecha en formato 'YYYY-MM-DD'
        time_obj: Objeto time de Python o cadena en formato 'HH:MM:SS'
        
    Returns:
        datetime: Objeto datetime combinado o None si hay error
    """
    try:
        # Manejar caso donde time_obj es None
        if time_obj is None:
            return None
            
        # Si time_obj ya es un objeto time, usarlo directamente
        if isinstance(time_obj, time):
            return datetime.combine(datetime.strptime(date_str, "%Y-%m-%d").date(), time_obj)
            
        # Si es string, procesar como antes
        time_str = time_obj
        # Eliminar segundos si están presentes
        if isinstance(time_str, str) and len(time_str) > 5:
            time_str = time_str[:5]
            
        # Combinar fecha y hora
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except Exception as e:
        logger.warning(f"Error al convertir {date_str} {time_obj} a datetime: {e}")
        return None

def handle_midnight_crossover(events_dict: Dict[str, datetime], flight_date: datetime.date) -> Dict[str, datetime]:
    """
    Maneja los casos donde los eventos pueden cruzar la medianoche.
    
    Args:
        events_dict: Diccionario con eventos y sus timestamps
        flight_date: Fecha del vuelo
        
    Returns:
        Dict: Diccionario con eventos y timestamps ajustados
    """
    # Encontrar la hora mínima y máxima
    valid_times = [t for t in events_dict.values() if t is not None]
    if not valid_times:
        return events_dict
        
    # Identificar eventos clave para determinar si el vuelo es nocturno
    # Generalmente los primeros eventos (groomers_in, crew_at_gate) ocurren antes
    early_events = ["groomers_in", "crew_at_gate"]
    late_events = ["flight_secure", "cierre_de_puerta", "push_back", "atd"]
    
    early_times = [events_dict[e] for e in early_events if e in events_dict and events_dict[e] is not None]
    late_times = [events_dict[e] for e in late_events if e in events_dict and events_dict[e] is not None]
    
    # Si hay eventos tempranos y tardíos, y los tempranos tienen hora mayor (ej. 23:00)
    # que los tardíos (ej. 01:00), entonces estamos cruzando la medianoche
    is_overnight = False
    if early_times and late_times:
        avg_early = sum((dt.hour * 60 + dt.minute) for dt in early_times) / len(early_times)
        avg_late = sum((dt.hour * 60 + dt.minute) for dt in late_times) / len(late_times)
        
        # Si el promedio de horas tempranas es mayor que el de horas tardías,
        # probablemente estamos cruzando la medianoche
        if avg_early > avg_late and avg_early > 20 * 60 and avg_late < 4 * 60:  # 20:00 y 04:00
            is_overnight = True
            logger.info(f"Detectado vuelo nocturno: eventos tempranos ~{avg_early/60:.1f}h, eventos tardíos ~{avg_late/60:.1f}h")
    
    # Enfoque tradicional: usar la hora mínima como referencia
    min_time = min(valid_times)
    adjusted_dict = {}
    
    for event, event_time in events_dict.items():
        if event_time is None:
            adjusted_dict[event] = None
            continue
            
        # Si detectamos que es un vuelo nocturno y este es un evento tardío con hora temprana
        if is_overnight and event in late_events and event_time.hour < 12:
            # Añadir un día para que sea posterior a los eventos tempranos
            adjusted_dict[event] = event_time + timedelta(days=1)
            logger.info(f"Ajustando evento nocturno {event}: {event_time} -> {adjusted_dict[event]}")
        else:
            # Enfoque tradicional: verificar diferencia de horas
            hours_diff = (event_time - min_time).total_seconds() / 3600
            if hours_diff > 12:
                adjusted_dict[event] = event_time - timedelta(days=1)
            elif hours_diff < -12:
                adjusted_dict[event] = event_time + timedelta(days=1)
            else:
                adjusted_dict[event] = event_time
            
    return adjusted_dict

def create_cascade_timeline_chart(flight_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Crea una gráfica de cascada con los eventos del vuelo.
    
    Args:
        flight_data: Diccionario con los datos del vuelo o lista de diccionarios para múltiples vuelos
        
    Returns:
        go.Figure: Gráfica de línea de tiempo
    """
    try:
        # Determinar si estamos manejando un solo vuelo o múltiples vuelos
        is_multiple_flights = isinstance(flight_data, list)
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

def calculate_average_event_times(flights_data: List[Dict[str, Any]]) -> Dict[str, datetime]:
    """
    Calcula los tiempos promedio para cada evento considerando cruces de medianoche.
    
    Args:
        flights_data: Lista de diccionarios con datos de vuelos
        
    Returns:
        Dict[str, datetime]: Diccionario con eventos y sus tiempos promedio
    """
    try:
        # Eventos a procesar
        events = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", 
            "flight_secure", "cierre_de_puerta", "push_back", "std", "atd"
        ]
        
        # Diccionario para almacenar todos los tiempos por evento
        event_times = {event: [] for event in events}
        
        # Procesar cada vuelo
        for flight in flights_data:
            flight_date = flight.get("flight_date")
            if not flight_date:
                continue
                
            # Convertir tiempos a datetime
            for event in events:
                time_obj = flight.get(event)
                if time_obj:
                    dt = convert_time_string_to_datetime(flight_date, time_obj)
                    if dt:
                        event_times[event].append(dt)
        
        # Calcular promedios considerando cruces de medianoche
        average_times = {}
        
        for event, times in event_times.items():
            if not times:
                continue
                
            # Ordenar tiempos
            sorted_times = sorted(times)
            
            # Detectar si hay cruces de medianoche
            is_overnight = False
            for i in range(len(sorted_times) - 1):
                if (sorted_times[i+1] - sorted_times[i]).total_seconds() > 12 * 3600:  # Más de 12 horas de diferencia
                    is_overnight = True
                    break
            
            if is_overnight:
                # Para cruces de medianoche, ajustar tiempos
                adjusted_times = []
                for i, t in enumerate(sorted_times):
                    if i > 0 and (t - sorted_times[i-1]).total_seconds() > 12 * 3600:
                        # Si hay un salto grande, ajustar el tiempo actual
                        adjusted_times.append(t - timedelta(days=1))
                    else:
                        adjusted_times.append(t)
                
                # Calcular promedio de tiempos ajustados
                total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in adjusted_times)
                avg_seconds = total_seconds / len(adjusted_times)
                
                # Crear datetime promedio
                avg_hour = int(avg_seconds // 3600)
                avg_minute = int((avg_seconds % 3600) // 60)
                avg_second = int(avg_seconds % 60)
                
                # Usar la fecha del primer vuelo como referencia
                reference_date = sorted_times[0].date()
                average_times[event] = datetime.combine(reference_date, time(avg_hour, avg_minute, avg_second))
            else:
                # Para vuelos normales, calcular promedio directo
                total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in sorted_times)
                avg_seconds = total_seconds / len(sorted_times)
                
                avg_hour = int(avg_seconds // 3600)
                avg_minute = int((avg_seconds % 3600) // 60)
                avg_second = int(avg_seconds % 60)
                
                reference_date = sorted_times[0].date()
                average_times[event] = datetime.combine(reference_date, time(avg_hour, avg_minute, avg_second))
        
        return average_times
        
    except Exception as e:
        logger.exception(f"Error al calcular tiempos promedio: {e}")
        return {}

def create_gantt_chart(flight_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Crea un diagrama de Gantt con los eventos del vuelo.
    
    Args:
        flight_data: Diccionario con los datos del vuelo o lista de diccionarios para múltiples vuelos
        
    Returns:
        go.Figure: Gráfica de línea de tiempo tipo Gantt
    """
    try:
        # Determinar si estamos manejando un solo vuelo o múltiples vuelos
        is_multiple_flights = isinstance(flight_data, list)
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

def create_combined_events_chart(flight_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Crea un gráfico de barras con eventos combinados que muestra la duración de procesos específicos.
    
    Args:
        flight_data: Diccionario con los datos del vuelo o lista de diccionarios para múltiples vuelos
        
    Returns:
        go.Figure: Gráfica de barras con eventos combinados
    """
    try:
        # Determinar si estamos manejando un solo vuelo o múltiples vuelos
        is_multiple_flights = isinstance(flight_data, list)
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
            # Extraer fechas únicas
            logger.info(f"Datos de fechas obtenidos: {len(dates_response.data)}")
            all_dates = [item['flight_date'] for item in dates_response.data]
            dates = sorted(list(set(all_dates)), reverse=True)
            logger.info(f"Fechas únicas encontradas: {dates}")
        
        if hasattr(flights_response, 'error') and flights_response.error is not None:
            logger.error(f"Error al obtener números de vuelo: {flights_response.error}")
            flight_numbers = []
        else:
            # Extraer números de vuelo únicos
            logger.info(f"Datos de vuelos obtenidos: {len(flights_response.data)}")
            all_flights = [item['flight_number'] for item in flights_response.data]
            flight_numbers = sorted(list(set(all_flights)))
            logger.info(f"Números de vuelo únicos encontrados: {flight_numbers}")
        
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
        
        # Mostrar filtros aplicados para depuración
        logger.info(f"Filtros aplicados - Fecha: {date_filter}, Vuelo: {flight_filter}")
        
        # Obtener datos preliminares según los dos primeros filtros para el tercer filtro
        preliminary_data = fetch_flight_data_for_chart(client, date_filter, flight_filter)
        
        # Tercer filtro: created_at (condicionado a los dos primeros filtros)
        created_at_filter = None
        if preliminary_data:
            # Extraer timestamps de creación únicos
            created_at_values = []
            for item in preliminary_data:
                if 'created_at' in item and item['created_at']:
                    # Formatear el timestamp para mostrar fecha y hora completa
                    try:
                        dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                        formatted_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
                        created_at_values.append((formatted_dt, item['created_at']))
                    except Exception as e:
                        logger.error(f"Error al formatear timestamp: {e}")
                        created_at_values.append((str(item['created_at']), item['created_at']))
            
            # Ordenar por timestamp (más reciente primero)
            created_at_values = sorted(set(created_at_values), key=lambda x: x[0], reverse=True)
            
            # Si hay timestamps disponibles, mostrar el filtro
            if created_at_values:
                display_values = ["Todos"] + [dt[0] for dt in created_at_values]
                raw_values = [None] + [dt[1] for dt in created_at_values]
                
                selected_index = st.selectbox(
                    "Seleccione timestamp de creación:",
                    options=display_values,
                    index=0
                )
                
                # Obtener el valor raw correspondiente al valor seleccionado
                if selected_index != "Todos":
                    selected_idx = display_values.index(selected_index)
                    created_at_filter = raw_values[selected_idx]
                    logger.info(f"Filtrando por timestamp de creación: {created_at_filter}")
        
        # Obtener datos finales con los tres filtros
        flights_data = fetch_flight_data_for_chart(client, date_filter, flight_filter, created_at_filter)
        
        if not flights_data:
            st.warning("No se encontraron vuelos con los filtros seleccionados.")
            return
            
        # Si hay más de un vuelo, permitir seleccionar cuál visualizar
        if len(flights_data) > 1:
            # Crear opciones para mostrar en selectbox
            flight_options = ["Todos los vuelos"]  # Añadir opción para visualizar todos
            for flight in flights_data:
                option_text = f"{flight.get('flight_date')} - {flight.get('flight_number')} ({flight.get('origin', 'N/A')} → {flight.get('destination', 'N/A')})"
                
                # Añadir timestamp de creación si existe
                if 'created_at' in flight and flight['created_at']:
                    try:
                        dt = datetime.fromisoformat(flight['created_at'].replace('Z', '+00:00'))
                        created_at_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        option_text += f" - Creado: {created_at_str}"
                    except Exception as e:
                        option_text += f" - Creado: {str(flight['created_at'])}"
                        
                flight_options.append(option_text)
            
            selected_flight_idx = st.selectbox(
                "Seleccione el vuelo a visualizar:",
                options=range(len(flight_options)),
                format_func=lambda i: flight_options[i]
            )
            
            if selected_flight_idx == 0:  # Si seleccionó "Todos los vuelos"
                # Mostrar información resumida de todos los vuelos
                st.subheader("Información Resumida de Todos los Vuelos")
                
                # Crear una tabla con información básica de todos los vuelos
                flight_summary = []
                for flight in flights_data:
                    flight_summary.append({
                        "Fecha": flight.get('flight_date', 'N/A'),
                        "Vuelo": flight.get('flight_number', 'N/A'),
                        "Origen": flight.get('origin', 'N/A'),
                        "Destino": flight.get('destination', 'N/A'),
                        "STD": flight.get('std', 'N/A'),
                        "ATD": flight.get('atd', 'N/A'),
                        "Delay": flight.get('delay', 'N/A')
                    })
                
                st.dataframe(flight_summary)
                
                # Usar todos los vuelos para visualización
                flights_to_display = flights_data
            else:
                # Ajustar el índice para compensar la opción "Todos los vuelos"
                flight_to_display = flights_data[selected_flight_idx - 1]
                flights_to_display = [flight_to_display]
                
                # Mostrar información del vuelo seleccionado
                st.subheader("Información del Vuelo")
                
                # Primera fila de información básica
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Fecha:** {flight_to_display.get('flight_date')}")
                    st.write(f"**Vuelo:** {flight_to_display.get('flight_number', 'N/A')}")
                    st.write(f"**Gate:** {flight_to_display.get('gate', 'N/A')}")
                
                with col2:
                    st.write(f"**Origen:** {flight_to_display.get('origin', 'N/A')}")
                    st.write(f"**Destino:** {flight_to_display.get('destination', 'N/A')}")
                    st.write(f"**Carrousel:** {flight_to_display.get('carrousel', 'N/A')}")
                
                with col3:
                    st.write(f"**STD:** {flight_to_display.get('std', 'N/A')}")
                    st.write(f"**ATD:** {flight_to_display.get('atd', 'N/A')}")
                    st.write(f"**Delay:** {flight_to_display.get('delay', 'N/A')} min")
        else:
            flight_to_display = flights_data[0]
            flights_to_display = [flight_to_display]
            
            # Mostrar información del vuelo
            st.subheader("Información del Vuelo")
            
            # Primera fila de información básica
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Fecha:** {flight_to_display.get('flight_date')}")
                st.write(f"**Vuelo:** {flight_to_display.get('flight_number', 'N/A')}")
                st.write(f"**Gate:** {flight_to_display.get('gate', 'N/A')}")
            
            with col2:
                st.write(f"**Origen:** {flight_to_display.get('origin', 'N/A')}")
                st.write(f"**Destino:** {flight_to_display.get('destination', 'N/A')}")
                st.write(f"**Carrousel:** {flight_to_display.get('carrousel', 'N/A')}")
            
            with col3:
                st.write(f"**STD:** {flight_to_display.get('std', 'N/A')}")
                st.write(f"**ATD:** {flight_to_display.get('atd', 'N/A')}")
                st.write(f"**Delay:** {flight_to_display.get('delay', 'N/A')} min")
        
        # Tabla de horarios
        if len(flights_to_display) == 1:
            st.subheader("Horarios de Eventos")
            
            flight_to_display = flights_to_display[0]
            time_fields = {
                "STD": flight_to_display.get('std'),
                "ATD": flight_to_display.get('atd'),
                "Groomers In": flight_to_display.get('groomers_in'),
                "Groomers Out": flight_to_display.get('groomers_out'),
                "Crew at Gate": flight_to_display.get('crew_at_gate'),
                "OK to Board": flight_to_display.get('ok_to_board'),
                "Flight Secure": flight_to_display.get('flight_secure'),
                "Cierre de Puerta": flight_to_display.get('cierre_de_puerta'),
                "Push Back": flight_to_display.get('push_back')
            }
            
            # Crear un DataFrame para mostrar los horarios como tabla
            time_data = []
            for event, time_val in time_fields.items():
                # Formatear el tiempo para mostrarlo de manera legible
                if time_val is not None:
                    if isinstance(time_val, time):
                        formatted_time = time_val.strftime("%H:%M")
                    else:
                        formatted_time = time_val
                else:
                    formatted_time = "N/A"
                    
                time_data.append({"Evento": event, "Hora": formatted_time})
            
            # Mostrar tabla de horarios
            st.dataframe(time_data, hide_index=True)
        
        # Radio para elegir el tipo de visualización
        chart_type = st.radio(
            "Seleccione el tipo de visualización:",
            options=["Gráfico de Gantt (Cascada)", "Gráfico de Puntos", "Gráfico de Eventos Combinados"],
            horizontal=True
        )
        
        # Crear y mostrar el gráfico según selección
        st.subheader("Visualización de Eventos")
        
        try:
            if chart_type == "Gráfico de Gantt (Cascada)":
                # Pasar la lista completa de vuelos al gráfico de Gantt
                fig = create_gantt_chart(flights_to_display)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Gráfico de Eventos Combinados":
                fig = create_combined_events_chart(flights_to_display[0] if len(flights_to_display) == 1 else flights_to_display)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                # Usar el gráfico de puntos original
                fig = create_cascade_timeline_chart(flights_to_display[0] if len(flights_to_display) == 1 else flights_to_display)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.exception(f"Error al mostrar gráfico: {e}")
            st.error(f"Error al generar el gráfico: {str(e)}")
    except Exception as e:
        logger.exception(f"Error al renderizar la pestaña de línea de tiempo: {e}")
        st.error(f"Error en la visualización: {str(e)}")