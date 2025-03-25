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
    Creates a progress chart for the flight showing the timeline from departure to arrival.

    Args:
        flight_data: Dictionary containing flight information.

    Returns:
        go.Figure: Progress chart or None if an error occurs.
    """
    try:
        # Extract times from flight data
        departure = flight_data.get('departure', {})
        arrival = flight_data.get('arrival', {})

        # Validate required times
        if not (departure.get('scheduledTime') and arrival.get('scheduledTime')):
            st.warning("No sufficient time information available to create the progress chart.")
            return None

        # Convert times to Toronto timezone
        toronto_tz = pytz.timezone("America/Toronto")
        departure_scheduled = datetime.fromisoformat(departure['scheduledTime']['utc'].replace('Z', '+00:00')).astimezone(toronto_tz)
        arrival_scheduled = datetime.fromisoformat(arrival['scheduledTime']['utc'].replace('Z', '+00:00')).astimezone(toronto_tz)

        departure_revised = departure_scheduled
        if departure.get('revisedTime'):
            departure_revised = datetime.fromisoformat(departure['revisedTime']['utc'].replace('Z', '+00:00')).astimezone(toronto_tz)

        arrival_revised = arrival_scheduled
        if arrival.get('revisedTime'):
            arrival_revised = datetime.fromisoformat(arrival['revisedTime']['utc'].replace('Z', '+00:00')).astimezone(toronto_tz)

        arrival_estimated = arrival_revised
        if arrival.get('predictedTime'):
            arrival_estimated = datetime.fromisoformat(arrival['predictedTime']['utc'].replace('Z', '+00:00')).astimezone(toronto_tz)

        # Current time in Toronto
        now_toronto = datetime.now(toronto_tz)

        # Calculate progress
        total_duration = (arrival_revised - departure_revised).total_seconds()
        elapsed_time = (now_toronto - departure_revised).total_seconds()
        progress = max(0, min(100, (elapsed_time / total_duration) * 100)) if total_duration > 0 else 0

        # Create the progress chart
        fig = go.Figure()

        # Add progress bar background
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

        # Add progress bar foreground
        if progress > 0:
            fig.add_shape(
                type="rect",
                x0=0,
                x1=progress,
                y0=-0.1,
                y1=0.1,
                line=dict(color="#43A047", width=1),
                fillcolor="#43A047",
                layer="below"
            )

        # Add markers for departure and arrival
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            mode='markers+text',
            marker=dict(size=15, symbol='circle', color='#1E88E5'),
            text=["Salida"],
            textposition="bottom center",
            hoverinfo='text',
            hovertext=[f"Salida: {departure_revised.strftime('%H:%M %Z')}"],
            name='Salida'
        ))

        fig.add_trace(go.Scatter(
            x=[100],
            y=[0],
            mode='markers+text',
            marker=dict(size=15, symbol='circle', color='#E53935'),
            text=["Llegada"],
            textposition="bottom center",
            hoverinfo='text',
            hovertext=[f"Llegada estimada: {arrival_estimated.strftime('%H:%M %Z')}"],
            name='Llegada'
        ))

        # Add current position marker
        if progress > 0:
            fig.add_trace(go.Scatter(
                x=[progress],
                y=[0],
                mode='markers',
                marker=dict(size=18, symbol='triangle-up', color='#43A047', angle=90),
                hoverinfo='text',
                hovertext=[f"Progreso: {progress:.1f}%"],
                name='Posición actual'
            ))

        # Add time details to the sides of the chart
        fig.add_annotation(
            x=20,
            y=0.35,
            text=f"<b>Salida</b><br>Programado: {departure_scheduled.strftime('%H:%M %Z')}<br>Revisado: {departure_revised.strftime('%H:%M %Z')}",
            showarrow=False,
            font=dict(size=12),
            xanchor='right',
            align='right'
        )

        fig.add_annotation(
            x=80,
            y=0.35,
            text=f"<b>Llegada</b><br>Programado: {arrival_scheduled.strftime('%H:%M %Z')}<br>Revisado: {arrival_revised.strftime('%H:%M %Z')}<br><b>Estimado: {arrival_estimated.strftime('%H:%M %Z')}</b>",
            showarrow=False,
            font=dict(size=12),
            xanchor='left',
            align='left'
        )

        # Add last update time
        last_update = flight_data.get('lastUpdatedUtc', 'Desconocido')
        if last_update != 'Desconocido':
            try:
                update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00')).astimezone(toronto_tz)
                update_str = update_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
                fig.add_annotation(
                    x=50,
                    y=-0.5,
                    text=f"Última actualización: {update_str}",
                    showarrow=False,
                    font=dict(size=12, color="gray"),
                    xanchor='center'
                )
            except Exception as e:
                logger.error(f"Error parsing last update time: {e}")

        # Configure layout
        fig.update_layout(
            title="Progreso del Vuelo",
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
                range=[-0.6, 0.6]
            ),
            height=300,
            margin=dict(l=20, r=20, t=50, b=50),
            plot_bgcolor='white'
        )

        return fig

    except Exception as e:
        logger.exception(f"Error creating flight progress chart: {e}")
        st.error(f"Error generating progress chart: {str(e)}")
        return None