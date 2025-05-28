from dotenv import load_dotenv
from pathlib import Path
import streamlit as st # Import streamlit

# Configuración inicial
try:
    # Importar módulos propios primero para que el logger esté disponible
    from src.config.logging_config import setup_logger
    from src.config.supabase_config import initialize_supabase_client
    from src.components.tabs_manager import render_tabs  # Importar el sistema de pestañas para visualización
    from src.components.tabs import (
        render_data_entry_tab,
        render_announcements_tab,
        render_wheelchair_tab,
        render_shift_trades_tab
    )
    
    # Configurar logger
    logger = setup_logger()
    logger.info("Iniciando aplicación Avianca Flight Report...") # Moved and changed to logger.info

    # Cargar credenciales desde secrets.toml
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    logger.info("Credenciales cargadas correctamente desde estructura anidada.") # Added log for confirmation

    # Configurar rutas base
    BASE_DIR = Path(__file__).resolve().parent
    LOGS_DIR = BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

    logger.info("Aplicación iniciada correctamente")

except Exception as e:
    # Log error before st.error if logger is available
    try:
        logger.error(f"Error de inicialización: {str(e)}", exc_info=True)
    except NameError: # Handle case where logger setup failed
        print(f"Error de inicialización (logger no disponible): {str(e)}")
    st.error(f"Error al iniciar la aplicación: {str(e)}")
    st.stop()

# Configuración de la página de Streamlit
try:
    st.set_page_config(
        page_title="Avianca - Reporte de Vuelo",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    logger.error(f"Error en configuración de página: {str(e)}", exc_info=True)
    st.error("Error al configurar la interfaz de usuario")
    st.stop()

# Inicializar cliente de Supabase con manejo de errores
try:
    client, project_ref, error_msg = initialize_supabase_client()
    if error_msg:
        st.error(error_msg)
        logger.error(f"Error al inicializar Supabase: {error_msg}")
except Exception as e:
    st.error("Error al conectar con la base de datos")
    logger.error(f"Error de conexión Supabase: {str(e)}", exc_info=True)
    st.stop()

# Crear tabs para las diferentes funcionalidades - Ahora con cinco pestañas principales
try:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛫 Ingreso de Datos", "📊 Visualizador", "📢 Anuncios", "♿ Wheelchairs", "🔄 Shift Trades"])
except Exception as e:
    logger.error(f"Error al crear tabs: {str(e)}", exc_info=True)
    st.error("Error al cargar la interfaz de usuario")
    st.stop()

# Anuncio de nueva funcionalidad con animación
if "balloons_shown" not in st.session_state:
    st.balloons()
    st.session_state.balloons_shown = True

st.success("🆕 **Nueva Funcionalidad: Shift Trades** - Ve a la última pestaña para revisar (Versión Beta)")

# Tab 1: Ingreso de Datos
with tab1:
    render_data_entry_tab(client, logger)

# Tab 2: Visualizador (pestañas internas para Línea de Tiempo, Análisis y Resumen)
with tab2:
    render_tabs(client) # Assumes render_tabs handles its own error logging
        
# Tab 3: Anuncios
with tab3:
    render_announcements_tab(logger)

# Tab 4: Wheelchairs
with tab4:
    render_wheelchair_tab(client) # Assumes render_wheelchair_tab handles its own error logging

# Tab 5: Shift Trades
with tab5:
    render_shift_trades_tab(logger)
