import streamlit as st
from datetime import date
from src.services.api_service import fetch_flight_status
from src.components.anuncios_textos import anuncios # Assuming this path is correct

def render_announcements_tab(logger):
    try:
        st.title("✈️ Anuncio de Arrivals")

        # Initialize session state variables if they don't exist
        if 'announcement_flight_data' not in st.session_state:
            st.session_state.announcement_flight_data = None
        if 'baggage_belt_number' not in st.session_state:
            st.session_state.baggage_belt_number = "____"
        if 'selected_flight_for_announcement' not in st.session_state:
            st.session_state.selected_flight_for_announcement = None

        today_str = date.today().strftime("%Y-%m-%d")

        # Botones para seleccionar vuelo
        col1, col2, col3 = st.columns(3)
        fetch_triggered = False
        flight_to_fetch = None

        with col1:
            if st.button("AV254"):
                fetch_triggered = True
                flight_to_fetch = "AV254"
                st.session_state.selected_flight_for_announcement = flight_to_fetch
        with col2:
            if st.button("AV626"):
                fetch_triggered = True
                flight_to_fetch = "AV626"
                st.session_state.selected_flight_for_announcement = flight_to_fetch
        with col3:
            if st.button("AV204"):
                fetch_triggered = True
                flight_to_fetch = "AV204"
                st.session_state.selected_flight_for_announcement = flight_to_fetch

        # Llamar a la API solo si un botón fue presionado en esta rerun
        if fetch_triggered and flight_to_fetch:
            logger.info(f"Consultando API para vuelo {flight_to_fetch} en la fecha {today_str}")
            st.session_state.announcement_flight_data = fetch_flight_status(flight_to_fetch, today_str)
            logger.info(f"Datos devueltos por la API para {flight_to_fetch}: {st.session_state.announcement_flight_data}")
            # Reset baggage belt number before processing new data
            st.session_state.baggage_belt_number = "____"

        # Procesar los datos almacenados en session_state
        if st.session_state.announcement_flight_data:
            found_belt = False
            for entry in st.session_state.announcement_flight_data:
                arrival_info = entry.get('arrival', {})
                # Check if the arrival airport is Toronto (YYZ) and baggage belt exists
                if arrival_info.get('airport', {}).get('iata') == 'YYZ' and 'baggageBelt' in arrival_info:
                    logger.info(f"Entrada seleccionada con número de banda para YYZ: {arrival_info}")
                    st.session_state.baggage_belt_number = arrival_info.get('baggageBelt', "____")
                    found_belt = True
                    break # Stop after finding the relevant Toronto arrival info

            if not found_belt:
                 logger.warning(f"No se encontró número de banda para Toronto (YYZ) en los datos del vuelo {st.session_state.selected_flight_for_announcement}.")
                 # Keep baggage_belt_number as "____" if not found specifically for YYZ
                 st.session_state.baggage_belt_number = "____"

        elif st.session_state.selected_flight_for_announcement is not None: # Only show warning if a flight was selected but no data found
             logger.warning(f"No se encontraron datos para el vuelo {st.session_state.selected_flight_for_announcement} o la respuesta de la API está vacía.")
             st.session_state.baggage_belt_number = "____" # Ensure reset if no data

        # Sección de Arrivals con el número de banda actualizado desde session_state
        st.markdown(
            f"""
            <div style='background-color:#f0f8ff; padding:15px; border-radius:10px; margin-bottom:20px;'>
                Les damos la bienvenida a la ciudad de Toronto. Para su comodidad, les informamos que la banda asignada para recoger su equipaje es la número {st.session_state.baggage_belt_number}.
                Si tiene conexión dentro de Canadá en un vuelo doméstico, deberá recoger su equipaje y llevarlo a la banda de equipaje de conexión.
                <hr style='border:1px solid #ccc;'>
                Welcome to Toronto. For your convenience, the carousel assigned to pick up your luggage is number {st.session_state.baggage_belt_number}.
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
