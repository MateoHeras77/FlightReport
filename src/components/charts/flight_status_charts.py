import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any, Optional

from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def create_flight_map(flight_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Creates a map showing the flight route between origin and destination.

    Args:
        flight_data: Dictionary containing flight information.

    Returns:
        go.Figure: Map with the flight route or None if an error occurs.
    """
    try:
        # Extract airport information
        departure = flight_data.get('departure', {}).get('airport', {})
        arrival = flight_data.get('arrival', {}).get('airport', {})

        # Validate coordinates
        if not (departure.get('location') and arrival.get('location')):
            st.warning("No location data available to create the map.")
            return None

        # Coordinates
        dep_lat, dep_lon = departure['location']['lat'], departure['location']['lon']
        arr_lat, arr_lon = arrival['location']['lat'], arrival['location']['lon']

        # City and IATA codes
        dep_city = f"{departure.get('municipalityName', 'Origin')} ({departure.get('iata', '---')})"
        arr_city = f"{arrival.get('municipalityName', 'Destination')} ({arrival.get('iata', '---')})"

        # Flight status
        status = flight_data.get('status', 'Unknown')

        # DataFrame for map points
        airports_df = pd.DataFrame({
            'name': [dep_city, arr_city],
            'lat': [dep_lat, arr_lat],
            'lon': [dep_lon, arr_lon],
            'type': ['Origin', 'Destination']
        })

        # Status colors
        status_colors = {
            'Scheduled': '#1E88E5',
            'EnRoute': '#43A047',
            'Landed': '#7CB342',
            'Delayed': '#FBC02D',
            'Diverted': '#F57C00',
            'Cancelled': '#E53935',
        }
        line_color = status_colors.get(status, '#757575')

        # Base map
        fig = px.scatter_mapbox(
            airports_df,
            lat='lat',
            lon='lon',
            hover_name='name',
            color='type',
            color_discrete_map={'Origin': '#1E88E5', 'Destination': '#E53935'},
            size_max=15,
            zoom=3,
            height=500,
            width=800
        )

        # Add route line with arrow
        fig.add_trace(
            go.Scattermapbox(
                lat=[dep_lat, arr_lat],
                lon=[dep_lon, arr_lon],
                mode='lines+markers',
                line=dict(width=3, color=line_color),
                marker=dict(size=12, symbol='arrow', color=line_color),
                hoverinfo='none',
                showlegend=False
            )
        )

        # Center and zoom calculation
        center_lat, center_lon = (dep_lat + arr_lat) / 2, (dep_lon + arr_lon) / 2
        distance = ((arr_lat - dep_lat)**2 + (arr_lon - dep_lon)**2)**0.5
        zoom = 6 if distance < 10 else 5 if distance < 20 else 4 if distance < 30 else 3

        # Map layout
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=zoom),
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

    except Exception as e:
        logger.exception(f"Error creating flight map: {e}")
        st.error(f"Error generating map: {str(e)}")
        return None

def create_flight_progress_chart(flight_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Crea un gráfico de progreso del vuelo con tiempos estimados y reales.
    
    Args:
        flight_data: Diccionario con información del vuelo
        
    Returns:
        go.Figure: Gráfico de progreso del vuelo o None si hay error
    """
    try:
        # Extraer información de tiempos
        departure = flight_data.get('departure', {})
        arrival = flight_data.get('arrival', {})
        
        # Verificar si tenemos información de horarios
        if not (departure.get('scheduledTime') and arrival.get('scheduledTime')):
            st.warning("No hay suficiente información de horarios para crear el gráfico de progreso.")
            return None
        
        # Extraer los tiempos en UTC para normalizar
        try:
            departure_scheduled = datetime.fromisoformat(departure['scheduledTime']['utc'].replace('Z', '+00:00'))
            arrival_scheduled = datetime.fromisoformat(arrival['scheduledTime']['utc'].replace('Z', '+00:00'))
            
            # Tiempo actual UTC
            now_utc = datetime.now(pytz.UTC)
            
            # Obtener tiempo revisado si existe
            departure_revised = departure_scheduled
            if departure.get('revisedTime'):
                departure_revised = datetime.fromisoformat(departure['revisedTime']['utc'].replace('Z', '+00:00'))
            
            arrival_revised = arrival_scheduled
            if arrival.get('revisedTime'):
                arrival_revised = datetime.fromisoformat(arrival['revisedTime']['utc'].replace('Z', '+00:00'))
            
            # Tiempo estimado de llegada si existe
            arrival_estimated = arrival_revised
            if arrival.get('predictedTime'):
                arrival_estimated = datetime.fromisoformat(arrival['predictedTime']['utc'].replace('Z', '+00:00'))
        except Exception as e:
            logger.error(f"Error al procesar tiempos: {e}")
            st.warning("Error al procesar los tiempos del vuelo.")
            return None
            
        # Calcular duración total programada y revisada en horas
        scheduled_duration = (arrival_scheduled - departure_scheduled).total_seconds() / 3600
        revised_duration = (arrival_revised - departure_revised).total_seconds() / 3600
        
        # Estado del vuelo
        status = flight_data.get('status', 'Desconocido')
        
        # Determinar el progreso del vuelo
        progress = 0
        if status == 'Landed':
            progress = 100
        elif status == 'EnRoute':
            # Calcular el progreso basado en el tiempo actual
            if now_utc >= departure_revised and now_utc <= arrival_estimated:
                elapsed = (now_utc - departure_revised).total_seconds() / 3600
                total = revised_duration
                progress = min(100, max(0, (elapsed / total) * 100))
        
        # Códigos IATA
        dep_iata = departure.get('airport', {}).get('iata', '---')
        arr_iata = arrival.get('airport', {}).get('iata', '---')
        
        # Crear figura para el gráfico de progreso
        fig = go.Figure()
        
        # Colores según estado
        status_colors = {
            'Scheduled': '#1E88E5',    # Azul
            'EnRoute': '#43A047',      # Verde
            'Landed': '#7CB342',       # Verde claro
            'Delayed': '#FBC02D',      # Amarillo
            'Diverted': '#F57C00',     # Naranja
            'Cancelled': '#E53935',    # Rojo
        }
        
        progress_color = status_colors.get(status, '#757575')
        
        # Añadir marcador de salida
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            mode='markers+text',
            marker=dict(size=15, symbol='circle', color='#1E88E5'),
            text=[dep_iata],
            textposition="bottom center",
            hoverinfo='text',
            hovertext=[f"Salida: {departure_revised.strftime('%H:%M')}"],
            name='Salida'
        ))
        
        # Añadir marcador de llegada
        fig.add_trace(go.Scatter(
            x=[100],
            y=[0],
            mode='markers+text',
            marker=dict(size=15, symbol='circle', color='#E53935'),
            text=[arr_iata],
            textposition="bottom center",
            hoverinfo='text',
            hovertext=[f"Llegada estimada: {arrival_estimated.strftime('%H:%M')}"],
            name='Llegada'
        ))
        
        # Añadir barra de progreso (fondo gris)
        fig.add_shape(
            type="rect",
            x0=0,
            x1=100,
            y0=-0.1,
            y1=0.1,
            line=dict(color="gray", width=1),
            fillcolor="lightgray",
            layer="below"
        )
        
        # Añadir barra de progreso completado
        if progress > 0:
            fig.add_shape(
                type="rect",
                x0=0,
                x1=progress,
                y0=-0.1,
                y1=0.1,
                line=dict(color=progress_color, width=1),
                fillcolor=progress_color,
                layer="below"
            )
            
            # Añadir posición actual del avión
            fig.add_trace(go.Scatter(
                x=[progress],
                y=[0],
                mode='markers',
                marker=dict(
                    size=18,
                    symbol='triangle-up',
                    color=progress_color,
                    angle=90
                ),
                hoverinfo='text',
                hovertext=[f"Progreso: {progress:.1f}%"],
                name='Posición actual'
            ))
        
        # Añadir sombra para retraso si aplica
        if arrival_revised > arrival_scheduled:
            delay_minutes = (arrival_revised - arrival_scheduled).total_seconds() / 60
            
            # Solo mostrar si hay retraso significativo
            if delay_minutes > 5:
                fig.add_annotation(
                    x=100,
                    y=0.3,
                    text=f"Retraso: {int(delay_minutes)} min",
                    showarrow=False,
                    font=dict(color="#FBC02D", size=14)
                )
        
        # Configurar diseño
        fig.update_layout(
            title=f"Progreso del Vuelo - {flight_data.get('number', 'N/A')}",
            showlegend=False,
            xaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                range=[-5, 105]
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                range=[-0.5, 0.5]
            ),
            height=250,
            margin=dict(l=20, r=20, t=50, b=20),
            plot_bgcolor='white'
        )
        
        # Añadir texto de estado
        fig.add_annotation(
            x=50,
            y=0.4,
            text=f"Estado: {status}",
            showarrow=False,
            font=dict(size=16, color=progress_color)
        )
        
        # Añadir información de duración
        hours = int(revised_duration)
        minutes = int((revised_duration - hours) * 60)
        
        fig.add_annotation(
            x=50,
            y=-0.3,
            text=f"Duración estimada: {hours}h {minutes}m",
            showarrow=False,
            font=dict(size=14)
        )
        
        return fig
    except Exception as e:
        logger.exception(f"Error al crear gráfico de progreso: {e}")
        st.error(f"Error al generar gráfico de progreso: {str(e)}")
        return None