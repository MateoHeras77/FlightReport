import datetime
import streamlit as st
from typing import Dict, Any, Tuple

from src.utils.form_utils import validate_time_field, format_time_for_database
from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def render_flight_form() -> Tuple[bool, Dict[str, Any]]:
    """
    Renderiza el formulario de vuelo y procesa los datos ingresados.
    
    Returns:
        tuple: (formulario_enviado, datos_procesados) donde:
            - formulario_enviado: bool que indica si el formulario fue enviado y validado
            - datos_procesados: diccionario con los datos procesados o None
    """
    with st.form("flight_form"):
        st.subheader("🚀 Datos Básicos")
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_date = st.date_input("📅 Fecha de vuelo", datetime.date.today(), key="flight_date")
        with col2:
            origin = st.text_input("🌍 Origen", key="origin").strip()
        with col3:
            destination = st.text_input("✈️ Destino", key="destination").strip()

        flight_number = st.selectbox("🔢 Número de vuelo", ["AV205", "AV255", "AV627"], key="flight_number")

        st.subheader("⏰ Horarios (solo HH:MM)")
        col3, col4 = st.columns(2)
        with col3:
            std = st.text_input("STD (Salida Programada)", value="", placeholder="HH:MM", key="std")
            atd = st.text_input("ATD (Salida Real)", value="", placeholder="HH:MM", key="atd")
            groomers_in = st.text_input("Groomers In", value="", placeholder="HH:MM", key="groomers_in")
            groomers_out = st.text_input("Groomers Out", value="", placeholder="HH:MM", key="groomers_out")
        with col4:
            crew_at_gate = st.text_input("Crew at Gate", value="", placeholder="HH:MM", key="crew_at_gate")
            ok_to_board = st.text_input("OK to Board", value="", placeholder="HH:MM", key="ok_to_board")
            flight_secure = st.text_input("Flight Secure", value="", placeholder="HH:MM", key="flight_secure")
            cierre_de_puerta = st.text_input("Cierre de Puerta", value="", placeholder="HH:MM", key="cierre_de_puerta")
            push_back = st.text_input("Push Back", value="", placeholder="HH:MM", key="push_back")

        st.subheader("📝 Otros Datos")
        col5, col6 = st.columns(2)
        with col5:
            pax_ob_total = st.text_input("PAX OB Total", key="pax_ob_total").strip()
            customs_in = st.text_input("Customs", key="customs_in").strip()
            delay = st.text_area("Delay", value="", key="delay")
        with col6:
            gate = st.text_input("Gate", key="gate").strip()
            carrousel = st.text_input("Carrousel", key="carrousel").strip()
            delay_code = st.text_area("Delay Code", value="", height=150, key="delay_code")

        st.subheader("💬 WCHR y Comentarios")
        col7, col8 = st.columns(2)
        with col7:
            WCHR = st.text_area("WCHR", value="", height=150, key="WCHR")
        with col8:
            comments = st.text_area("Comentarios", value="", height=150, key="comments")

        submitted = st.form_submit_button("🔍 Revisar")

    if submitted:
        return process_form_data(
            flight_date, origin, destination, flight_number,
            std, atd, groomers_in, groomers_out, crew_at_gate,
            ok_to_board, flight_secure, cierre_de_puerta, push_back,
            pax_ob_total, customs_in, delay, gate, carrousel,
            delay_code, WCHR, comments
        )
    else:
        return False, None


def process_form_data(
    flight_date, origin, destination, flight_number,
    std, atd, groomers_in, groomers_out, crew_at_gate,
    ok_to_board, flight_secure, cierre_de_puerta, push_back,
    pax_ob_total, customs_in, delay, gate, carrousel,
    delay_code, WCHR, comments
) -> Tuple[bool, Dict[str, Any]]:
    """
    Procesa y valida los datos del formulario.
    
    Returns:
        tuple: (es_valido, datos) donde:
            - es_valido: bool indicando si los datos son válidos
            - datos: dict con los datos procesados o None
    """
    logger.info("Procesando datos del formulario")
    
    # Validar campos obligatorios
    required_fields = {
        "Fecha de vuelo": flight_date,
        "Origen": origin,
        "Destino": destination,
        "Número de vuelo": flight_number,
        "PAX OB Total": pax_ob_total,
        "Customs In": customs_in,
        "Gate": gate,
        "Carrousel": carrousel,
        "WCHR": WCHR,
    }
    missing = [k for k, v in required_fields.items() if not v or str(v).strip() == ""]
    if missing:
        st.error("Complete los siguientes campos: " + ", ".join(missing))
        logger.warning(f"Faltan campos obligatorios: {missing}")
        return False, None
        
    # Validar campos de tiempo
    time_fields = {
        "STD": std,
        "ATD": atd,
        "Groomers In": groomers_in,
        "Groomers Out": groomers_out,
        "Crew at Gate": crew_at_gate,
        "OK to Board": ok_to_board,
        "Flight Secure": flight_secure,
        "Cierre de Puerta": cierre_de_puerta,
        "Push Back": push_back
    }
    
    all_valid = True
    normalized_times = {}
    for label, value in time_fields.items():
        valid, result = validate_time_field(value, label)
        if not valid:
            st.error(result)
            logger.warning(f"Campo de tiempo inválido: {label} - {result}")
            all_valid = False
        else:
            normalized_times[label] = result

    if not all_valid:
        return False, None

    # Preparar datos para la base de datos y visualización
    database_data = {
        "flight_date": flight_date.isoformat(),
        "origin": origin,
        "destination": destination,
        "flight_number": flight_number,
        "std": format_time_for_database(normalized_times["STD"]),
        "atd": format_time_for_database(normalized_times["ATD"]),
        "groomers_in": format_time_for_database(normalized_times["Groomers In"]),
        "groomers_out": format_time_for_database(normalized_times["Groomers Out"]),
        "crew_at_gate": format_time_for_database(normalized_times["Crew at Gate"]),
        "ok_to_board": format_time_for_database(normalized_times["OK to Board"]),
        "flight_secure": format_time_for_database(normalized_times["Flight Secure"]),
        "cierre_de_puerta": format_time_for_database(normalized_times["Cierre de Puerta"]),
        "push_back": format_time_for_database(normalized_times["Push Back"]),
        "pax_ob_total": pax_ob_total,
        "customs_in": customs_in,
        "delay": delay,
        "gate": gate,
        "carrousel": carrousel,
        "delay_code": delay_code,
        "WCHR": WCHR,
        "comments": comments
    }
    
    # Revertir formato de tiempo para visualización
    display_data = database_data.copy()
    for key in normalized_times.keys():
        field_name = key.lower().replace(" ", "_")
        if display_data[field_name]:
            display_data[field_name] = normalized_times[key]
            
    logger.info("Datos del formulario procesados y validados correctamente")
    return True, {
        "data_to_display": display_data,
        "data_for_database": database_data
    }