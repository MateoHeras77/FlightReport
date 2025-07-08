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
    # Inicializar variables en session_state para mantener valores entre recargas
    if "flight_number_previous" not in st.session_state:
        st.session_state.flight_number_previous = ""
    
    # Inicializar más variables del session_state para valores predeterminados
    if "default_destination" not in st.session_state:
        st.session_state.default_destination = ""
    if "default_std" not in st.session_state:
        st.session_state.default_std = ""
    
    # Mapeo de vuelos para determinar el vuelo anterior
    previous_flight_mapping = {
        "AV205": "AV204",
        "AV627": "AV626",
        "AV255": "AV254",
        "AV619": "AV618", # Added new flight
        "AV625": "AV624"  # Added new flight
    }
    
    # Información predeterminada para cada vuelo
    flight_defaults = {
        "AV255": {"destination": "BOG", "std": "09:05"},
        "AV627": {"destination": "SAL", "std": "17:10"},
        "AV205": {"destination": "BOG", "std": "23:50"},
        "AV619": {"destination": "SAL", "std": "07:55"}, # Added new flight
        "AV625": {"destination": "SAL", "std": "01:55"}  # Added new flight
    }
    
    # Paso 1: Selección del vuelo antes de mostrar el formulario
    st.markdown("### Paso 1: Seleccione el vuelo para el reporte")
    
    # Callback para actualizar valores predeterminados cuando cambia el vuelo
    def update_flight_defaults():
        selected = st.session_state.flight_number_selector
        st.session_state.flight_number_previous = previous_flight_mapping.get(selected, "")
        
        # Actualizar valores predeterminados en session_state
        if selected in flight_defaults:
            st.session_state.default_destination = flight_defaults[selected]["destination"]
            st.session_state.default_std = flight_defaults[selected]["std"]
        else:
            st.session_state.default_destination = ""
            st.session_state.default_std = ""
    
    flight_number_selected = st.selectbox(
        "🔢 Seleccione el número de vuelo primero:",
        ["", "AV205", "AV255", "AV627", "AV619", "AV625"], # Added new flights
        format_func=lambda x: "Elegir vuelo" if x == "" else x,
        key="flight_number_selector",
        on_change=update_flight_defaults
    )
    
    # Solo continuar si se ha seleccionado un vuelo
    if not flight_number_selected:
        st.info("⚠️ Por favor, seleccione un número de vuelo para continuar.")
        # Devolver False, None para indicar que el formulario no se ha enviado
        return False, None
    
    # Mostrar información sobre la selección actual
    previous_flight = st.session_state.flight_number_previous
    st.success(f"✅ Vuelo seleccionado: {flight_number_selected} - Vuelo anterior correspondiente: {previous_flight}")
    
    if st.session_state.default_destination and st.session_state.default_std:
        st.info(f"📝 Información predeterminada: Destino: {st.session_state.default_destination}, " 
                f"Hora programada de salida (STD): {st.session_state.default_std}")
    
    # Paso 2: Mostrar el formulario solo después de seleccionar un vuelo
    st.markdown("### Paso 2: Complete el formulario de reporte")
    
    with st.form("flight_form"):
        st.subheader("🚀 Datos Básicos")
        col1, col2, col3 = st.columns(3)
        with col1:
            flight_date = st.date_input("📅 Fecha de vuelo", value=None, key="flight_date")
        with col2:
            origin = st.selectbox("🌍 Origen", ["YYZ"], index=0, key="origin")
        with col3:
            # Usar el destino predeterminado desde session_state
            destination_options = ["", "BOG", "SAL"]
            default_index = 0
            if st.session_state.default_destination in destination_options:
                default_index = destination_options.index(st.session_state.default_destination)
            
            destination = st.selectbox(
                "✈️ Destino", 
                destination_options, 
                index=default_index, 
                key="destination"
            )

        # Selectbox para número de vuelo dentro del formulario, pero usando el valor ya seleccionado
        flight_number_options = ["", "AV205", "AV255", "AV627", "AV619", "AV625"] # Added new flights
        default_index = flight_number_options.index(flight_number_selected) if flight_number_selected in flight_number_options else 0
        
        flight_number = st.selectbox(
            "🔢 Confirme el número de vuelo",
            flight_number_options,
            index=default_index,
            key="flight_number"
        )

        st.subheader("⏰ Tiempos")
        col3, col4 = st.columns(2)
        with col3:
            # Usar el STD predeterminado desde session_state
            std = st.text_input(
                "STD (Salida Programada)",
                value=st.session_state.default_std,
                placeholder="HH:MM",
                key="std"
            )
            atd = st.text_input("ATD (Salida Real)", value="", placeholder="HH:MM", key="atd")
            crew_departure = st.text_input(
                "Salida de Tripulacion",
                value="",
                placeholder="HH:MM",
                key="crew_departure"
            )
            groomers_agents_options = [str(i) for i in range(31)]
            number_groomers_agents = st.selectbox(
                "Cantidad de Agentes Groomers",
                options=groomers_agents_options,
                index=0,
                key="number_groomers_agents"
            )
            groomers_in = st.text_input("Groomers In", value="", placeholder="HH:MM", key="groomers_in")
            groomers_out = st.text_input("Groomers Out", value="", placeholder="HH:MM", key="groomers_out")
        with col4:
            crew_at_gate = st.text_input("Crew at Gate", value="", placeholder="HH:MM", key="crew_at_gate")
            ok_to_board = st.text_input("OK to Board", value="", placeholder="HH:MM", key="ok_to_board")
            flight_secure = st.text_input("Flight Secure", value="", placeholder="HH:MM", key="flight_secure")
            cierre_de_puerta = st.text_input("Cierre de Puerta", value="", placeholder="HH:MM", key="cierre_de_puerta")
            push_back = st.text_input("Push Back", value="", placeholder="HH:MM", key="push_back")

        st.subheader("📋 Información de Customs")
        col_customs1, col_customs2 = st.columns(2)
        with col_customs1:
            customs_in = st.text_input("Customs In", value="No Customs", placeholder="HH:MM", key="customs_in")
        with col_customs2:
            customs_out = st.text_input("Customs Out", value="No Customs", placeholder="HH:MM", key="customs_out")

        st.subheader("👥 Información de Pasajeros")
        col_pax1, col_pax2 = st.columns(2)
        with col_pax1:
            # Lista desplegable para Total Pax (0-200)
            total_pax_options = [str(i) for i in range(201)]
            total_pax = st.selectbox(
                "Total Pax", 
                options=total_pax_options,
                index=0,  # Valor por defecto: 0
                key="total_pax"
            )
            
            # Lista desplegable para PAX C (0-18)
            pax_c_options = [str(i) for i in range(19)]
            pax_c = st.selectbox(
                "PAX C", 
                options=pax_c_options,
                index=0,  # Valor por defecto: 0
                key="pax_c"
            )
        with col_pax2:
            # Lista desplegable para PAX Y (0-200)
            pax_y_options = [str(i) for i in range(201)]
            pax_y = st.selectbox(
                "PAX Y", 
                options=pax_y_options,
                index=0,  # Valor por defecto: 0
                key="pax_y"
            )
            
            # Lista desplegable para Infantes (0-200)
            infants_options = [str(i) for i in range(201)]
            infants = st.selectbox(
                "Infantes", 
                options=infants_options,
                index=0,  # Valor por defecto: 0
                key="infants"
            )

        st.subheader("⏳ Información por Demoras")
        col_delay1, col_delay2 = st.columns(2)
        with col_delay1:
            # Crear una lista de opciones de 0 a 200 para el selector de delay, más la opción adicional
            delay_options = [str(i) for i in range(201)] + [">200 Escribir en comentarios"]
            delay = st.selectbox(
                "Delay (Ingresar minutos de demora)", 
                options=delay_options,
                index=0,  # Valor por defecto: 0
                key="delay"
            )
        with col_delay2:
            delay_code = st.text_area("Delay Code (Reporte)", placeholder="Ingresar los codigos del retraso",value="", key="delay_code")

        # Actualizar etiquetas de WCHR y Agentes eliminando "AV2**" y simplificando el código
        wchr_current_label = "WCHR Vuelo Salida (AV255 - AV627 - AV205)"
        agents_current_label = "Agentes Vuelo Salida (AV255 - AV627 - AV205)"

        # Obtener el vuelo anterior desde session_state
        previous_flight = st.session_state.flight_number_previous
        wchr_previous_label = "WCHR Vuelo Llegada (AV254 - AV626 - AV204)"
        agents_previous_label = "Agentes Vuelo Llegada (AV254 - AV626 - AV204)"

        st.subheader("♿ Sillas de Ruedas")
        
        # Sección de Llegada (izquierda)
        col_llegada, col_salida = st.columns(2)
        
        with col_llegada:
            # Mostrar el vuelo anterior, usar el valor ya determinado fuera del formulario
            if st.session_state.flight_number_previous:
                llegada_title = f"##### 🛬 Sillas de Ruedas Llegada ({st.session_state.flight_number_previous})"
            else:
                llegada_title = "##### 🛬 Sillas de Ruedas Llegada (Seleccione vuelo de salida primero)"
            
            st.markdown(llegada_title)
            
            # Listas desplegables para WCHR y WCHC de llegada
            col_wchr_prev1, col_wchr_prev2 = st.columns(2)
            with col_wchr_prev1:
                wchr_previous_options = [str(i).zfill(2) for i in range(51)]
                wchr_previous_count = st.selectbox(
                    "Cantidad WCHR",
                    options=wchr_previous_options,
                    index=0,
                    key="wchr_previous_count"
                )
            with col_wchr_prev2:
                wchc_previous_options = [str(i).zfill(2) for i in range(51)]
                wchc_previous_count = st.selectbox(
                    "Cantidad WCHC",
                    options=wchc_previous_options,
                    index=0,
                    key="wchc_previous_count"
                )
            
            # Agentes de llegada
            agent_options = [str(i) for i in range(21)] + ["> 20 Escribir en comentarios"]
            agents_previous_flight = st.selectbox(
                "Agentes Llegada",
                options=agent_options,
                index=0,
                key="agents_previous_flight"
            )
        
        # Sección de Salida (derecha)
        with col_salida:
            # Mostrar el vuelo actual
            if flight_number_selected:
                salida_title = f"##### 🛫 Sillas de Ruedas Salida ({flight_number_selected})"
            else:
                salida_title = "##### 🛫 Sillas de Ruedas Salida (Seleccione vuelo primero)"
            
            st.markdown(salida_title)
            
            # Listas desplegables para WCHR y WCHC de salida
            col_wchr_curr1, col_wchr_curr2 = st.columns(2)
            with col_wchr_curr1:
                wchr_current_options = [str(i).zfill(2) for i in range(51)]
                wchr_current_count = st.selectbox(
                    "Cantidad WCHR",
                    options=wchr_current_options,
                    index=0,
                    key="wchr_current_count"
                )
            with col_wchr_curr2:
                wchc_current_options = [str(i).zfill(2) for i in range(51)]
                wchc_current_count = st.selectbox(
                    "Cantidad WCHC",
                    options=wchc_current_options,
                    index=0,
                    key="wchc_current_count"
                )
            
            # Agentes de salida
            agents_current_flight = st.selectbox(
                "Agentes Salida",
                options=agent_options,
                index=0,
                key="agents_current_flight"
            )
        
        # Combinar valores seleccionados en el formato requerido para la base de datos
        wchr_current_flight = f"{wchr_current_count} WCHR | {wchc_current_count} WCHC"
        wchr_previous_flight = f"{wchr_previous_count} WCHR | {wchc_previous_count} WCHC"

        st.subheader("📍 Información de Gate y Carrusel")
        col_gate1, col_gate2 = st.columns(2)
        with col_gate1:
            gate = st.text_input("Gate", key="gate").strip()
        with col_gate2:
            carrousel = st.text_input("Carrousel", key="carrousel").strip()

        st.subheader("💬 Comentarios")
        comments = st.text_area("Comentarios", value="", height=150,placeholder="Ingresar comentarios generales", key="comments")

        # Nuevo campo para Información de Gate Bag
        st.subheader("🧳  Información del Gate Bag")
        gate_bag = st.text_area("Información de Gate Bag", value="", height=150, placeholder="Ingresar status del gate bag. (Ejm: Faltan boarding pass, hojas del reporte, etc)", key="gate_bag")

        submitted = st.form_submit_button("🔍 Revisar")

    if submitted:
        return process_form_data(
                flight_date, origin, destination, flight_number,
                std, atd, crew_departure, number_groomers_agents,
                groomers_in, groomers_out, crew_at_gate,
                ok_to_board, flight_secure, cierre_de_puerta, push_back,
                total_pax, pax_c, pax_y, infants, customs_in, customs_out,
                delay, gate, carrousel, delay_code,
                wchr_current_flight, wchr_previous_flight,
                agents_current_flight, agents_previous_flight, comments, gate_bag
            )
    else:
        return False, None


def process_form_data(
    flight_date, origin, destination, flight_number,
    std, atd, crew_departure, number_groomers_agents,
    groomers_in, groomers_out, crew_at_gate,
    ok_to_board, flight_secure, cierre_de_puerta, push_back,
    total_pax, pax_c, pax_y, infants, customs_in, customs_out,
    delay, gate, carrousel, delay_code,
    wchr_current_flight, wchr_previous_flight,
    agents_current_flight, agents_previous_flight, comments, gate_bag
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
        "Total Pax": total_pax,
        "Gate": gate,
        "Carrousel": carrousel,
        "WCHR": wchr_current_flight,
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
        "Salida de Tripulacion": crew_departure,
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

    # Validar campos obligatorios y numéricos para pasajeros
    passenger_fields = {
        "Total Pax": total_pax,
        "PAX C": pax_c,
        "PAX Y": pax_y,
        "Infantes": infants
    }

    for field_name, value in passenger_fields.items():
        if not value.strip():
            st.error(f"El campo '{field_name}' es obligatorio.")
            logger.warning(f"Campo obligatorio faltante: {field_name}")
            return False, None
        if not value.isdigit():
            st.error(f"El campo '{field_name}' debe contener únicamente números.")
            logger.warning(f"Campo no numérico: {field_name} - Valor ingresado: {value}")
            return False, None

    # Ya no se valida que el campo delay sea numérico, ahora acepta cualquier texto
    
    # Ya no se validan los campos de agentes como numéricos, ahora aceptan cualquier texto

    # Actualizar el esquema de datos para reflejar los cambios en la base de datos
    database_data = {
        "flight_date": flight_date.isoformat(),
        "origin": origin,
        "destination": destination,
        "flight_number": flight_number,
        "std": format_time_for_database(normalized_times["STD"]),
        "atd": format_time_for_database(normalized_times["ATD"]),
        "crew_departure": format_time_for_database(normalized_times["Salida de Tripulacion"]),
        "number_groomers_agents": number_groomers_agents,
        "groomers_in": format_time_for_database(normalized_times["Groomers In"]),
        "groomers_out": format_time_for_database(normalized_times["Groomers Out"]),
        "crew_at_gate": format_time_for_database(normalized_times["Crew at Gate"]),
        "ok_to_board": format_time_for_database(normalized_times["OK to Board"]),
        "flight_secure": format_time_for_database(normalized_times["Flight Secure"]),
        "cierre_de_puerta": format_time_for_database(normalized_times["Cierre de Puerta"]),
        "push_back": format_time_for_database(normalized_times["Push Back"]),
        "pax_c": pax_c,
        "pax_y": pax_y,
        "infants": infants,
        "customs_in": customs_in,
        "customs_out": customs_out,
        "delay": delay,
        "gate": gate,
        "carrousel": carrousel,
        "delay_code": delay_code,
        "wchr_previous_flight": wchr_previous_flight,
        "agents_previous_flight": agents_previous_flight,
        "agents_current_flight": agents_current_flight,
        "wchr_current_flight": wchr_current_flight,
        "comments": comments,
        "gate_bag": gate_bag
    }

    # Revertir formato de tiempo para visualización
    display_data = database_data.copy()
    for key in normalized_times.keys():
        field_name = key.lower().replace(" ", "_")
        # Ajuste para campos cuyo nombre en la base de datos no coincide con la
        # conversión simple de la etiqueta
        db_field_name = field_name
        if field_name == "salida_de_tripulacion":
            db_field_name = "crew_departure"
        if db_field_name in display_data and display_data[db_field_name]:
            display_data[db_field_name] = normalized_times[key]

    # Asegurar que el valor de Total Pax se incluya en los datos enviados y en el reporte
    database_data["pax_ob_total"] = total_pax
    display_data["pax_ob_total"] = total_pax

    logger.info("Datos del formulario procesados y validados correctamente")

    return True, {
        "data_to_display": display_data,
        "data_for_database": database_data    }