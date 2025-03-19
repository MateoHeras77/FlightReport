import datetime
import streamlit.components.v1 as components

def validate_time_field(time_str: str, field_name: str):
    """
    Valida y formatea campos de tiempo.
    
    Args:
        time_str (str): El tiempo en formato HH:MM
        field_name (str): Nombre del campo para mensajes de error
        
    Returns:
        tuple: (es_valido, resultado) donde:
            - es_valido: bool indicando si la validación pasó
            - resultado: str con el tiempo formateado o mensaje de error
    """
    if not time_str or time_str.strip() == "":
        return (False, f"El campo {field_name} es obligatorio.")
    try:
        dt = datetime.datetime.strptime(time_str.strip(), "%H:%M")
        return (True, dt.strftime("%H:%M"))
    except ValueError:
        return (False, f"El campo {field_name} tiene formato inválido. Use HH:MM.")


def format_time_for_database(time_str: str) -> str:
    """
    Convierte HH:MM a HH:MM:SS para la base de datos.
    
    Args:
        time_str (str): Tiempo en formato HH:MM
        
    Returns:
        str: Tiempo en formato HH:MM:SS o None si es vacío
    """
    return f"{time_str}:00" if time_str else None


def create_copy_button(text):
    """
    Crea un botón personalizado para copiar usando HTML y JavaScript.
    
    Args:
        text (str): El texto que se copiará al portapapeles
    """
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