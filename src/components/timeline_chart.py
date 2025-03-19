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
        
    min_time = min(valid_times)
    adjusted_dict = {}
    
    for event, event_time in events_dict.items():
        if event_time is None:
            adjusted_dict[event] = None
            continue
            
        # Si hay una diferencia de más de 12 horas con la hora mínima
        # asumimos que el evento ocurrió el día anterior o siguiente
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
        flight_data: Diccionario con los datos del vuelo
        
    Returns:
        go.Figure: Gráfica de línea de tiempo
    """
    try:
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
        
        # Convertir fechas y horas a objetos datetime
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
            
            # Crear barra para el evento actual (ahora el eje Y tiene los tiempos y el eje X los eventos)
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
        
        # Ordenar los nombres de los eventos según su secuencia operativa, no por tiempo
        operational_order = [
            "groomers_in", "groomers_out", "crew_at_gate", "ok_to_board", 
            "flight_secure", "cierre_de_puerta", "push_back", "std", "atd"
        ]
        
        # Filtrar para incluir solo eventos presentes
        operational_order = [e for e in operational_order if e in events_dict]
        
        # Formato del gráfico
        fig.update_layout(
            title=f"Secuencia de Eventos - Vuelo {flight_data.get('flight_number', 'N/A')} ({flight_date})",
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

def create_gantt_chart(flight_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Crea un diagrama de Gantt con los eventos del vuelo.
    
    Args:
        flight_data: Diccionario con los datos del vuelo
        
    Returns:
        go.Figure: Gráfica de línea de tiempo tipo Gantt
    """
    try:
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
        
        # Convertir fechas y horas a objetos datetime
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
            x_start="Start",  # Usamos x_start (parámetro correcto)
            x_end="Finish", 
            y="Task",        # Evento en el eje Y (parámetro correcto)
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
            
            # Alternativa: convertir a datetime para operaciones aritméticas
            # start_dt = row["Start"].to_pydatetime()
            # end_dt = row["Finish"].to_pydatetime()
            # midpoint = start_dt + (end_dt - start_dt) / 2
            
            fig.add_annotation(
                x=midpoint,                      # Punto medio calculado correctamente
                y=row["Task"],                  # Evento en Y
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
        
        # Formato final del gráfico (para mantener el eje Y invertido)
        fig.update_layout(
            title=f"Secuencia de Eventos - Vuelo {flight_data.get('flight_number', 'N/A')} ({flight_date})",
            xaxis=dict(
                title='Hora',
                tickformat='%H:%M',
                tickmode='array',
                tickvals=time_range,
                ticktext=[t.strftime('%H:%M') for t in time_range],
                side="top"  # Colocamos las etiquetas de tiempo en la parte superior
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
            flight_options = []
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
            
            flight_to_display = flights_data[selected_flight_idx]
        else:
            flight_to_display = flights_data[0]
        
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
            st.write(f"**PAX Total:** {flight_to_display.get('pax_ob_total', 'N/A')}")
            st.write(f"**Customs In:** {flight_to_display.get('customs_in', 'N/A')}")
            
            # Mostrar timestamp de creación si existe
            if 'created_at' in flight_to_display and flight_to_display['created_at']:
                try:
                    dt = datetime.fromisoformat(flight_to_display['created_at'].replace('Z', '+00:00'))
                    created_at_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    st.write(f"**Creado:** {created_at_str}")
                except Exception as e:
                    st.write(f"**Creado:** {flight_to_display['created_at']}")
        
        # Segunda fila para información adicional
        if any(field for field in [
            flight_to_display.get('delay'), 
            flight_to_display.get('delay_code'),
            flight_to_display.get('comments'),
            flight_to_display.get('WCHR')
        ]):
            st.markdown("---")  # Separador
            
            col4, col5 = st.columns(2)
            
            with col4:
                if flight_to_display.get('delay'):
                    st.write(f"**Delay:** {flight_to_display.get('delay')}")
                if flight_to_display.get('delay_code'):
                    st.write(f"**Código de Demora:** {flight_to_display.get('delay_code')}")
            
            with col5:
                if flight_to_display.get('comments'):
                    st.write(f"**Comentarios:** {flight_to_display.get('comments')}")
                if flight_to_display.get('WCHR'):
                    st.write(f"**WCHR:** {flight_to_display.get('WCHR')}")
        
        # Tabla de horarios
        st.subheader("Horarios de Eventos")
        
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
            
        time_df = pd.DataFrame(time_data)
        st.dataframe(time_df, hide_index=True, use_container_width=True)
        
        # Radio para elegir el tipo de visualización
        chart_type = st.radio(
            "Seleccione el tipo de visualización:",
            options=["Gráfico de Gantt (Cascada)", "Gráfico de Puntos"],
            horizontal=True
        )
        
        # Crear y mostrar el gráfico según selección
        st.subheader("Visualización de Eventos")
        
        try:
            if chart_type == "Gráfico de Gantt (Cascada)":
                fig = create_gantt_chart(flight_to_display)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                # Usar el gráfico de puntos original
                fig = create_cascade_timeline_chart(flight_to_display)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.exception(f"Error al mostrar gráfico: {e}")
            st.error("Error al generar el gráfico. Usando versión simplificada.")
            
            # Versión simplificada del gráfico sin timedeltas
            events_data = []
            for name, value in time_fields.items():
                if value:
                    if isinstance(value, time):
                        time_str = value.strftime("%H:%M")
                    else:
                        time_str = str(value)
                    events_data.append({"Evento": name, "Hora": time_str})
            
            if events_data:
                events_df = pd.DataFrame(events_data)
                fig = px.timeline(events_df, x="Hora", y="Evento", color="Evento")
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        logger.exception(f"Error al renderizar la pestaña de línea de tiempo: {e}")
        st.error(f"Error en la visualización: {str(e)}")