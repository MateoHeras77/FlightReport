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
    from src.utils.form_utils import create_copy_button
    from src.services.supabase_service import send_data_to_supabase
    from src.components.anuncios_textos import anuncios  # Importar el archivo de textos de anuncios
    from src.services.api_service import fetch_flight_status
    from datetime import date

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

# Crear tabs para las diferentes funcionalidades - Ahora con cuatro pestañas principales
try:
    tab1, tab2, tab3, tab4 = st.tabs(["🛫 Ingreso de Datos", "📊 Visualizador", "📢 Anuncios", "♿ Wheelchairs"])
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

            # Ya no mostrar el recuento detallado de variables y datos ingresados
            # Solo conservar la generación del texto del reporte y los botones

            # Generar el texto del reporte para copiar
            # Obtener los números de vuelo para mostrar en el reporte
            flight_number = display_data.get('flight_number', '')
            # Mapeo de vuelos para determinar el vuelo anterior
            previous_flight_mapping = {
                "AV205": "AV204",
                "AV627": "AV626",
                "AV255": "AV254"
            }
            previous_flight = previous_flight_mapping.get(flight_number, "")
            
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

♿ *Silla de ruedas:*
*Sillas Vuelo Llegada ({previous_flight}):* {display_data.get('wchr_previous_flight', '')}
*Agentes Vuelo Llegada ({previous_flight}):* {display_data.get('agents_previous_flight', '')}
*Sillas Vuelo Salida ({flight_number}):* {display_data.get('wchr_current_flight', '')}
*Agentes Vuelo Salida ({flight_number}):* {display_data.get('agents_current_flight', '')}

📍 *Información de Gate y Carrusel:*
*Gate:* {display_data.get('gate', '')}
*Carrousel:* {display_data.get('carrousel', '')}

🧳 *Información de Gate Bag:*
*Gate Bag:* {display_data.get('gate_bag', '')}

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
                        
                        # Guardar en session_state que los datos fueron enviados exitosamente
                        st.session_state.data_submitted = True
                        
                        # Botón para copiar el reporte generado (solo se muestra después de enviar exitosamente)
                        st.markdown("### Copiar reporte para WhatsApp")
                        create_copy_button(report_text)
                    else:
                        st.error(f"Error al enviar datos: {error_message}")
                        logger.error(f"Error al enviar datos a Supabase: {error_message}")
                except Exception as e:
                    st.error("Error al procesar el envío de datos")
                    logger.error(f"Error en envío de datos: {str(e)}", exc_info=True)
            # Mostrar el botón de copiar solo si aún no se han enviado los datos
            elif "data_submitted" not in st.session_state or not st.session_state.data_submitted:
                st.warning("⚠️ Debe hacer clic en 'Enviar y Finalizar' antes de copiar el reporte")
                st.markdown("### Copiar reporte para WhatsApp (primero debe enviar los datos)")
                # Botón deshabilitado o con estilo diferente
                st.info("El botón de copiar estará disponible después de enviar los datos correctamente.")
            else:
                # Si ya se enviaron los datos, mostrar el botón de copiar
                st.markdown("### Copiar reporte para WhatsApp")
                create_copy_button(report_text)

    except Exception as e:
        logger.error(f"Error en Tab 1: {str(e)}", exc_info=True)
        st.error("Error al procesar los datos del formulario")

# Tab 2: Visualizador (pestañas internas para Línea de Tiempo, Análisis y Resumen)
with tab2:
    try:
        # Usar el sistema de pestañas modular para visualización
        render_tabs(client)
    except Exception as e:
        logger.error(f"Error en Tab 2: {str(e)}", exc_info=True)
        st.error("Error al cargar la visualización de eventos")
        
# Tab 3: Anuncios
with tab3:
    try:
        st.title("✈️ Anuncio de Arrivals")

        # Botones para seleccionar vuelo
        col1, col2, col3 = st.columns(3)
        with col1:
            av254_button = st.button("AV254")
        with col2:
            av626_button = st.button("AV626")
        with col3:
            av204_button = st.button("AV204")

        # Variable para almacenar el número de banda
        baggage_belt_number = "____"

        # Llamar a la API según el botón presionado
        flight_data = None  # Inicializar como None para evitar llamadas automáticas
        if av254_button:
            flight_data = fetch_flight_status("AV254", date.today().strftime("%Y-%m-%d"))
        elif av626_button:
            logger.info(f"Consultando API para vuelo AV626 en la fecha {date.today().strftime('%Y-%m-%d')}")
            flight_data = fetch_flight_status("AV626", date.today().strftime("%Y-%m-%d"))
            logger.info(f"Datos devueltos por la API: {flight_data}")
        elif av204_button:
            flight_data = fetch_flight_status("AV204", date.today().strftime("%Y-%m-%d"))

        # Ajustar la lógica para buscar la entrada correcta en los datos devueltos por la API
        if flight_data:
            for entry in flight_data:
                arrival_info = entry.get('arrival', {})
                if 'baggageBelt' in arrival_info:
                    logger.info(f"Entrada seleccionada con número de banda: {arrival_info}")
                    baggage_belt_number = arrival_info.get('baggageBelt', "____")
                    break
            else:
                logger.warning("No se encontró ninguna entrada con número de banda en los datos devueltos por la API.")
        else:
            logger.warning("No se encontraron datos para el vuelo seleccionado o la respuesta de la API está vacía.")

        # Sección de Arrivals con el número de banda actualizado
        st.markdown(
            f"""
            <div style='background-color:#f0f8ff; padding:15px; border-radius:10px; margin-bottom:20px;'>
                Les damos la bienvenida a la ciudad de Toronto. Para su comodidad, les informamos que la banda asignada para recoger su equipaje es la número {baggage_belt_number}.
                Si tiene conexión dentro de Canadá en un vuelo doméstico, deberá recoger su equipaje y llevarlo a la banda de equipaje de conexión.
                <hr style='border:1px solid #ccc;'>
                Welcome to Toronto. For your convenience, the carousel assigned to pick up your luggage is number {baggage_belt_number}.
                All passengers with a connecting domestic flight within Canada must pick up their bag and drop it off at the connection baggage belt.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.title("👪🏽 Anuncio de Abordaje")

        # Sección de Inicio de Abordaje con texto interpolado
        st.markdown(
            f"""
            <div style='background-color:#e8f5e9; padding:15px; border-radius:10px; margin-bottom:20px;'>
                {anuncios['boarding_details']['inicio_abordaje']['es']}
                {anuncios['boarding_details']['inicio_abordaje']['en']}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Subsecciones de abordaje con diseño mejorado
        sections = [
            ("🛡️ Preabordaje", "preboarding"),
            ("🌟 Grupo A", "group_a"),
            ("👶 Abordaje Familia con Niños", "family_boarding"),
            ("🛫 Grupo B", "group_b"),
            ("🎒 Grupo C", "group_c"),
            ("📜 Grupo D y E", "group_d_e"),
            ("📦 Grupo F (Pasajeros XS o BASIC)", "group_f")
        ]

        for title, key in sections:
            st.markdown(
                f"""
                <div style='background-color:#f9fbe7; padding:15px; border-radius:10px; margin-bottom:20px;'>
                    <h3>{title}</h3>
                    <p>{anuncios['boarding_details'][key]['es']}</p>
                    <hr style='border:1px solid #ccc;'>
                    <p>{anuncios['boarding_details'][key]['en']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    except Exception as e:
        logger.error(f"Error en la pestaña de anuncios: {str(e)}", exc_info=True)
        st.error("Error al procesar los anuncios")

# Tab 4: Wheelchairs
with tab4:
    try:
        from src.components.tabs.wheelchair_tab import render_wheelchair_tab
        # Usar la función de la pestaña de Wheelchairs
        render_wheelchair_tab(client)
    except Exception as e:
        logger.error(f"Error en Tab 4 (Wheelchairs): {str(e)}", exc_info=True)
        st.error("Error al cargar la visualización de servicios de sillas de ruedas")
