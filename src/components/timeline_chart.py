import streamlit as st
from src.components.tabs.timeline_tab import render_timeline_tab

def display_timeline_chart(client):
    """
    Función principal para mostrar la visualización de eventos de vuelo.
    Este archivo se mantiene por compatibilidad con código existente,
    pero delega toda la funcionalidad a la estructura modular.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    # Renderizar la pestaña de línea de tiempo utilizando la implementación modular
    render_timeline_tab(client)

# Mantener la función render_timeline_tab para compatibilidad con código existente
def render_timeline_tab(client):
    """
    Función mantenida por compatibilidad con código existente.
    Delega la funcionalidad a la implementación modular.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    # Redirigir a la implementación actual
    from src.components.tabs.timeline_tab import render_timeline_tab as render_tab_impl
    render_tab_impl(client)