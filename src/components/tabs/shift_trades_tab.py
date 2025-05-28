import streamlit as st

def render_shift_trades_tab(logger):
    try:
        st.title("🔄 Shift Trades")
        st.markdown(
            """
            <div style='text-align: center; padding: 20px;'>
                <p>Haz clic en el botón de abajo para acceder a la aplicación de intercambio de turnos:</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Crear un enlace que se abra en una nueva pestaña
        st.link_button("🔗 Ir a Shift Trades", "https://shifttrade.streamlit.app/")
        
    except Exception as e:
        logger.error(f"Error en Shift Trades Tab: {str(e)}", exc_info=True)
        st.error("Error al cargar la sección de intercambio de turnos")
