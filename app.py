import os
import streamlit as st
from dotenv import load_dotenv

# Configuración inicial
print("Iniciando aplicación Avianca Flight Report...")
load_dotenv()  # Cargar variables de entorno desde .env

# Importar módulos propios
from src.config.logging_config import setup_logger
from src.config.supabase_config import initialize_supabase_client, DEFAULT_TABLE_NAME
from src.components.flight_form import render_flight_form
from src.components.timeline_chart import render_timeline_tab
from src.utils.form_utils import create_copy_button
from src.services.supabase_service import send_data_to_supabase

# Configurar logger
logger = setup_logger()
logger.info("Aplicación iniciada")

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Avianca - Reporte de Vuelo",
    page_icon="✈️",
    layout="wide"
)

# Inicializar cliente de Supabase
client, project_ref, error_msg = initialize_supabase_client()
if error_msg:
    st.error(error_msg)

# Crear tabs para las diferentes funcionalidades
tab1, tab2 = st.tabs(["🛫 Ingreso de Datos", "📊 Visualización de Eventos"])

# Tab 1: Ingreso de Datos
with tab1:
    st.title("✈️ Ingreso de Datos - Reporte de Vuelo")

    # Inicializar form_data en session_state si no existe
    if "form_data" not in st.session_state:
        st.session_state.form_data = None

    # Renderizar el formulario de vuelo
    form_submitted, form_data = render_flight_form()

    if form_submitted and form_data:
        st.session_state.form_data = form_data
        st.success("Datos revisados correctamente.")

    # Mostrar datos de revisión si existen
    if st.session_state.form_data:
        st.subheader("📑 Revisión de Datos")
        display_data = st.session_state.form_data["data_to_display"]

        # Agrupar los datos por categorías más lógicas
        operation_times = {k: v for k, v in display_data.items() if k in [
            'std', 'atd', 'groomers_in', 'groomers_out', 'crew_at_gate',
            'ok_to_board', 'flight_secure', 'cierre_de_puerta', 'push_back'
        ]}
        flight_info = {k: v for k, v in display_data.items() if any(x in k.lower() for x in ['flight', 'route', 'aircraft']) and k not in operation_times}
        other_info = {k: v for k, v in display_data.items() if k not in operation_times and k not in flight_info}

        # Mostrar información de tiempos de operación
        st.subheader("⏰ Tiempos de Operación")
        cols = st.columns(3)
        for i, (key, value) in enumerate(operation_times.items()):
            cols[i % 3].write(f"*{key}:* {value}")

        # Mostrar información del vuelo
        st.subheader("✈️ Información del Vuelo")
        cols = st.columns(3)
        for i, (key, value) in enumerate(flight_info.items()):
            cols[i % 3].write(f"*{key}:* {value}")

        # Mostrar información adicional
        if other_info:
            st.subheader("📝 Otros Detalles")
            cols = st.columns(3)
            for i, (key, value) in enumerate(other_info.items()):
                cols[i % 3].write(f"*{key}:* {value}")

        # Mostrar el reporte completo y botón para copiar
        st.subheader("📋 Reporte Final")
        report_text = "\n".join([
            "⏰ TIEMPOS DE OPERACIÓN",
            *[f"*{k}:* {v}" for k, v in operation_times.items()],
            "\n✈️ INFORMACIÓN DEL VUELO",
            *[f"*{k}:* {v}" for k, v in flight_info.items()],
            "\n📝 OTROS DETALLES",
            *[f"*{k}:* {v}" for k, v in other_info.items()]
        ])
        st.text_area("Reporte Final", value=report_text, height=200)
        create_copy_button(report_text)

        # Botón para enviar a Supabase
        if st.button("Enviar y Finalizar"):
            database_data = st.session_state.form_data["data_for_database"]
            success, error_message = send_data_to_supabase(client, DEFAULT_TABLE_NAME, database_data)
            
            if success:
                st.success("Datos enviados exitosamente a la base de datos")
            else:
                st.error(f"Error al enviar datos: {error_message}")

# Tab 2: Visualización de Eventos
with tab2:
    render_timeline_tab(client)
