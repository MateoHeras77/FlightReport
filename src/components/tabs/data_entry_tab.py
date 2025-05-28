import streamlit as st
from src.components.flight_form import render_flight_form
from src.services.supabase_service import send_data_to_supabase, SupabaseWriteError
from src.config.supabase_config import DEFAULT_TABLE_NAME
from src.utils import generate_flight_report_text, create_copy_button

def render_data_entry_tab(client, logger):
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

            # Generar el texto del reporte para copiar
            report_text = generate_flight_report_text(display_data)
            
            st.text_area("Reporte Generado", value=report_text, height=300)

            # Botón para enviar a Supabase
            if st.button("Enviar y Finalizar"):
                try:
                    database_data = st.session_state.form_data["data_for_database"]
                    send_data_to_supabase(client, DEFAULT_TABLE_NAME, database_data)
                    
                    st.success("Datos enviados exitosamente a la base de datos")
                    logger.info("Datos enviados exitosamente a Supabase")
                    
                    # Guardar en session_state que los datos fueron enviados exitosamente
                    st.session_state.data_submitted = True
                    
                    # Botón para copiar el reporte generado (solo se muestra después de enviar exitosamente)
                    st.markdown("### Copiar reporte para WhatsApp")
                    create_copy_button(report_text)

                except SupabaseWriteError as e:
                    st.error(f"Error al enviar datos: {str(e)}")
                    logger.error(f"Error al enviar datos a Supabase: {str(e)}", exc_info=True)
                except Exception as e: # Catch any other unexpected errors
                    st.error("Error inesperado al procesar el envío de datos.")
                    logger.error(f"Error inesperado en envío de datos: {str(e)}", exc_info=True)
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
        logger.error(f"Error en Data Entry Tab: {str(e)}", exc_info=True)
        st.error("Error al procesar los datos del formulario")
