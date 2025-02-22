import os
import datetime
import logging
import streamlit as st
from google.cloud import bigquery
from dotenv import load_dotenv
import streamlit.components.v1 as components
import tempfile
import json

# Leer credenciales desde Streamlit Secrets
credentials = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]

# Asegurarse de que los saltos de línea en la clave privada sean correctos
credentials = credentials.replace("\\n", "\n")

try:
    # Convertir la cadena a un diccionario JSON
    credentials_dict = json.loads(credentials)

    # Crear un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_file:
        json.dump(credentials_dict, temp_file)  # Guardar JSON correctamente
        temp_file_path = temp_file.name

    # Establecer la variable de entorno con la ruta al archivo temporal
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path

    st.write(f"Archivo de credenciales creado en: {temp_file_path}")

except json.JSONDecodeError as e:
    st.error(f"Error al decodificar JSON: {e}")
    st.write("Contenido de las credenciales (puede contener errores):", credentials)


# Configurar logger
logger = logging.getLogger("flight_report_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler("app.log", mode="a")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# Tabla en BigQuery
table_id = "unfc-439001.avianca2000.ReporteVuelo"
# `Para pruebas unfc-439001.avianca2000.ReporteVuelo`
# "unfc-439001.avianca2000.Reportes"

# Inicializar el cliente de BigQuery
try:
    client = bigquery.Client()
    logger.info("BigQuery client initialized successfully.")
except Exception as e:
    logger.exception("Error initializing BigQuery client:")
    st.error(f"Error al inicializar BigQuery: {e}")
    client = None  # Evita que el código siga si no hay cliente


def create_copy_button(text):
    """Crea un botón personalizado para copiar usando HTML y JavaScript"""
    copy_button_html = f"""
        <textarea id="textToCopy" style="position: absolute; left: -9999px;">{text}</textarea>
        <button 
            onclick="copyText()"
            style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;"
        >
            📋 Copiar Reporte
        </button>
        <div id="copyStatus" style="margin-top: 5px;"></div>

        <script>
        function copyText() {{
            var textArea = document.getElementById("textToCopy");
            textArea.select();
            try {{
                document.execCommand("copy");
                document.getElementById("copyStatus").innerHTML = "✅ Reporte copiado al portapapeles!";
                setTimeout(function() {{
                    document.getElementById("copyStatus").innerHTML = "";
                }}, 2000);
            }} catch (err) {{
                document.getElementById("copyStatus").innerHTML = "❌ Error al copiar";
            }}
        }}
        </script>
    """
    components.html(copy_button_html, height=80)

st.title("✈️ Ingreso de Datos - Reporte de Vuelo")

def validate_time_field(time_str: str, field_name: str):
    """Valida y formatea campos de tiempo"""
    if not time_str or time_str.strip() == "":
        return (False, f"El campo {field_name} es obligatorio.")
    try:
        dt = datetime.datetime.strptime(time_str.strip(), "%H:%M")
        return (True, dt.strftime("%H:%M"))
    except ValueError:
        return (False, f"El campo {field_name} tiene formato inválido. Use HH:MM.")

def format_time_for_bigquery(time_str: str) -> str:
    """Convierte HH:MM a HH:MM:SS para BigQuery"""
    return f"{time_str}:00" if time_str else None

# Inicializar form_data en session_state si no existe
if "form_data" not in st.session_state:
    st.session_state.form_data = None

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
        customs_in = st.text_input("Customs In", key="customs_in").strip()
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
    else:
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
                all_valid = False
            else:
                normalized_times[label] = result

        if all_valid:
            # Preparar datos para BigQuery
            bigquery_data = {
                "flight_date": flight_date.isoformat(),
                "origin": origin,
                "destination": destination,
                "flight_number": flight_number,
                "std": format_time_for_bigquery(normalized_times["STD"]),
                "atd": format_time_for_bigquery(normalized_times["ATD"]),
                "groomers_in": format_time_for_bigquery(normalized_times["Groomers In"]),
                "groomers_out": format_time_for_bigquery(normalized_times["Groomers Out"]),
                "crew_at_gate": format_time_for_bigquery(normalized_times["Crew at Gate"]),
                "ok_to_board": format_time_for_bigquery(normalized_times["OK to Board"]),
                "flight_secure": format_time_for_bigquery(normalized_times["Flight Secure"]),
                "cierre_de_puerta": format_time_for_bigquery(normalized_times["Cierre de Puerta"]),
                "push_back": format_time_for_bigquery(normalized_times["Push Back"]),
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
            display_data = bigquery_data.copy()
            for key in normalized_times.keys():
                field_name = key.lower().replace(" ", "_")
                if display_data[field_name]:
                    display_data[field_name] = normalized_times[key]
            st.session_state.form_data = {
                "data_to_display": display_data,
                "data_for_bigquery": bigquery_data
            }
            st.success("Datos revisados correctamente.")

if st.session_state.form_data:
    st.subheader("📑 Revisión de Datos")
    display_data = st.session_state.form_data["data_to_display"]

    cols = st.columns(3)
    keys = list(display_data.keys())
    for i, key in enumerate(keys):
        cols[i % 3].write(f"**{key}:** {display_data[key]}")

    report_text = "\n".join([f"{k}: {display_data[k]}" for k in keys])
    st.text_area("Reporte Final", value=report_text, height=200)
    create_copy_button(report_text)

    # Botón Único: Enviar a BigQuery
    if st.button("Enviar y Finalizar"):
        try:
            bigquery_data = st.session_state.form_data["data_for_bigquery"]
            logger.info("Intentando enviar datos a BigQuery")
            logger.info(f"Datos a enviar: {bigquery_data}")

            job_config = bigquery.LoadJobConfig()
            job = client.load_table_from_json([bigquery_data], table_id, job_config=job_config)
            job.result()

            if job.errors:
                logger.error(f"Errores en el job de BigQuery: {job.errors}")
                st.error(f"Error al enviar datos: {job.errors}")
            else:
                logger.info("Datos enviados exitosamente a BigQuery")
                st.success("Datos enviados exitosamente a BigQuery")
                # Se muestra el mensaje de éxito y la app permanece con los campos intactos.

        except Exception as e:
            error_msg = f"Error al enviar datos a BigQuery: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            logger.exception("Detalles completos del error:")
