import os
import streamlit as st
from dotenv import load_dotenv
import sys
from pathlib import Path

# Configuración inicial
try:
    print("Iniciando aplicación Avianca Flight Report...")
    
    # Cargar credenciales desde secrets.toml
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    
    # Configurar rutas base
    BASE_DIR = Path(__file__).resolve().parent
    LOGS_DIR = BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

    # Importar módulos propios
    from src.config.logging_config import setup_logger
    from src.config.supabase_config import initialize_supabase_client, DEFAULT_TABLE_NAME
    from src.components.flight_form import render_flight_form
    from src.components.tabs_manager import render_tabs  # Importar el sistema de pestañas para visualización
    from src.components.tabs.flight_status_tab import render_flight_status_tab  # Importar la pestaña de estado de vuelo
    from src.utils.form_utils import create_copy_button
    from src.services.supabase_service import send_data_to_supabase

    # Configurar logger
    logger = setup_logger()
    logger.info("Aplicación iniciada correctamente")

except Exception as e:
    st.error(f"Error al iniciar la aplicación: {str(e)}")
    logger.error(f"Error de inicialización: {str(e)}", exc_info=True)
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

# Crear tabs para las diferentes funcionalidades - Ahora con tres pestañas principales
try:
    tab1, tab2, tab3 = st.tabs(["🛫 Ingreso de Datos", "📊 Visualizador", "🛬 Estado de Vuelo"])
except Exception as e:
    logger.error(f"Error al crear tabs: {str(e)}", exc_info=True)
    st.error("Error al cargar la interfaz de usuario")
    st.stop()

# Tab 1: Ingreso de Datos
with tab1:
    try:
        st.title("✈️ Ingreso de Datos - Reporte de Vuelo")

        # Inicializar form_data en session_state si no existe
        if "form_data" not in st.session_state:
            st.session_state.form_data = None

        # Renderizar el formulario de vuelo
        form_submitted, form_data = render_flight_form()

        if form_submitted and form_data:
            st.session_state.form_data = form_data
            st.success("Datos revisados correctamente.")
            logger.info("Datos del formulario validados correctamente")

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
            customs_info = {k: v for k, v in display_data.items() if k in ['customs_in', 'customs_out']}
            passenger_info = {k: v for k, v in display_data.items() if k in ['total_pax', 'pax_c', 'pax_y', 'infants']}
            delay_info = {k: v for k, v in display_data.items() if k in ['delay', 'delay_code']}
            wchr_info = {k: v for k, v in display_data.items() if k in ['wchr_current_flight', 'wchr_previous_flight', 'agents_current_flight', 'agents_previous_flight']}
            gate_carrousel_info = {k: v for k, v in display_data.items() if k in ['gate', 'carrousel']}
            other_info = {k: v for k, v in display_data.items() if k not in operation_times and k not in flight_info and k not in customs_info and k not in passenger_info and k not in delay_info and k not in wchr_info and k not in gate_carrousel_info}

            # Combinar información adicional e información del vuelo
            st.subheader("✈️ Información del Vuelo")
            combined_info = {**flight_info, **other_info}
            cols = st.columns(3)
            for i, (key, value) in enumerate(combined_info.items()):
                cols[i % 3].write(f"*{key}:* {value}")

            # Mostrar información de tiempos de operación
            st.subheader("⏰ Tiempos de Operación")
            cols = st.columns(3)
            for i, (key, value) in enumerate(operation_times.items()):
                cols[i % 3].write(f"*{key}:* {value}")


            # Mostrar información de customs
            st.subheader("📋 Información de Customs")
            cols = st.columns(2)
            for i, (key, value) in enumerate(customs_info.items()):
                cols[i % 2].write(f"*{key}:* {value}")

            # Mostrar información de pasajeros
            st.subheader("👥 Información de Pasajeros")
            cols = st.columns(2)
            for i, (key, value) in enumerate(passenger_info.items()):
                cols[i % 2].write(f"*{key}:* {value}")

            # Asegurar que Total Pax se muestre correctamente en el reporte generado
            report_text = f"""
🚀 *Datos Básicos*:
*Fecha de vuelo:* {display_data.get('flight_date', '')}
*Origen:* {display_data.get('origin', '')}
*Destino:* {display_data.get('destination', '')}
*Número de vuelo:* {display_data.get('flight_number', '')}

⏰ *Tiempos:*
*STD:* {display_data.get('std', '')}
*ATD:* {display_data.get('atd', '')}
*Groomers In:* {display_data.get('groomers_in', '')}
*Groomers Out:* {display_data.get('groomers_out', '')}
*Crew at Gate:* {display_data.get('crew_at_gate', '')}
*OK to Board:* {display_data.get('ok_to_board', '')}
*Flight Secure:* {display_data.get('flight_secure', '')}
*Cierre de Puerta:* {display_data.get('cierre_de_puerta', '')}
*Push Back:* {display_data.get('push_back', '')}

📋 *Información de Customs:*
*Customs In:* {display_data.get('customs_in', '')}
*Customs Out:* {display_data.get('customs_out', '')}

👥 *Información de Pasajeros:*
*Total Pax:* {display_data.get('pax_ob_total', '')}
*PAX C:* {display_data.get('pax_c', '')}
*PAX Y:* {display_data.get('pax_y', '')}
*Infantes:* {display_data.get('infants', '')}

⏳ *Información por Demoras:*
*Delay:* {display_data.get('delay', '')}
*Delay Code:* {display_data.get('delay_code', '')}

💬 *WCHR:*
*WCHR Vuelo Anterior:* {display_data.get('wchr_previous_flight', '')}
*Agentes Vuelo Anterior:* {display_data.get('agents_previous_flight', '')}
*WCHR Vuelo Actual:* {display_data.get('wchr_current_flight', '')}
*Agentes Vuelo Actual:* {display_data.get('agents_current_flight', '')}

📍 *Información de Gate y Carrusel:*
*Gate:* {display_data.get('gate', '')}
*Carrousel:* {display_data.get('carrousel', '')}

💬 *Comentarios:*
{display_data.get('comments', '')}
"""
            st.text_area("Reporte Generado", value=report_text.strip(), height=300)

            # Botón para enviar a Supabase
            if st.button("Enviar y Finalizar"):
                try:
                    database_data = st.session_state.form_data["data_for_database"]
                    success, error_message = send_data_to_supabase(client, DEFAULT_TABLE_NAME, database_data)
                    
                    if success:
                        st.success("Datos enviados exitosamente a la base de datos")
                        logger.info("Datos enviados exitosamente a Supabase")
                    else:
                        st.error(f"Error al enviar datos: {error_message}")
                        logger.error(f"Error al enviar datos a Supabase: {error_message}")
                except Exception as e:
                    st.error("Error al procesar el envío de datos")
                    logger.error(f"Error en envío de datos: {str(e)}", exc_info=True)

            # Botón para copiar el reporte generado
            create_copy_button(report_text)

    except Exception as e:
        logger.error(f"Error en Tab 1: {str(e)}", exc_info=True)
        st.error("Error al procesar los datos del formulario")

# Tab 2: Visualizador (ahora solo incluye Line de Tiempo, Análisis y Resumen)
with tab2:
    try:
        # Usar el sistema de pestañas modular para visualización
        render_tabs(client)
    except Exception as e:
        logger.error(f"Error en Tab 2: {str(e)}", exc_info=True)
        st.error("Error al cargar la visualización de eventos")

# Tab 3: Estado de Vuelo (nueva pestaña principal)
with tab3:
    try:
        # Renderizar directamente la pestaña de estado de vuelo
        render_flight_status_tab(client)
    except Exception as e:
        logger.error(f"Error en Tab 3: {str(e)}", exc_info=True)
        st.error("Error al cargar la información de estado de vuelo")
