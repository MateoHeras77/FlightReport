import streamlit as st
from src.components.tabs.timeline_tab import render_timeline_tab
from src.components.tabs.flight_status_tab import render_flight_status_tab

def render_tabs(client):
    """
    Renderiza un sistema de pestañas para la visualización.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    # Definir las pestañas disponibles - Ya sin "Estado de Vuelo"
    tabs = ["Línea de Tiempo", "Análisis", "Resumen"]
    
    # Crear el contenedor de pestañas
    selected_tab = st.radio("Seleccione una vista:", tabs, horizontal=True)
    
    # Renderizar la pestaña seleccionada
    if selected_tab == "Línea de Tiempo":
        render_timeline_tab(client)
    elif selected_tab == "Análisis":
        render_analytics_tab(client)
    elif selected_tab == "Resumen":
        render_summary_tab(client)
        
def render_analytics_tab(client):
    """
    Renderiza la pestaña de análisis con gráficos estadísticos.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    st.header("Análisis de Eventos")
    
    # Mostrar mensaje de funcionalidad en desarrollo
    st.info("Esta funcionalidad está en desarrollo. Pronto podrás ver análisis estadísticos de los eventos de vuelo.")
    
    # Aquí se pueden agregar visualizaciones y análisis estadísticos
    st.write("En esta sección se incluirán:")
    st.markdown("""
    - Análisis de tiempos promedio entre eventos
    - Distribución de retrasos y sus causas
    - Correlación entre variables operativas
    - Tendencias a lo largo del tiempo
    """)
    
def render_summary_tab(client):
    """
    Renderiza la pestaña de resumen con información general.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    st.header("Resumen de Vuelos")
    
    # Mostrar mensaje de funcionalidad en desarrollo
    st.info("Esta funcionalidad está en desarrollo. Pronto podrás ver un resumen general de los vuelos.")
    
    # Aquí se pueden agregar resúmenes y estadísticas generales
    st.write("En esta sección se incluirán:")
    st.markdown("""
    - Total de vuelos por ruta y fecha
    - Estadísticas de puntualidad
    - Indicadores de rendimiento operativo
    - Métricas clave de desempeño
    """)