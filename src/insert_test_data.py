import streamlit as st
import sys
import os
import datetime

# Agregar el directorio rau00edz al path para que las importaciones funcionen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.supabase_config import initialize_supabase_client, DEFAULT_TABLE_NAME
from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def main():
    st.title("Insertar Datos de Prueba en Supabase")
    
    # Inicializar cliente de Supabase
    client, project_ref, error = initialize_supabase_client()
    
    if error:
        st.error(f"Error al conectar con Supabase: {error}")
        return
    
    st.success("Conexiu00f3n a Supabase establecida correctamente")
    st.write(f"Proyecto: {project_ref}")
    
    # Datos de prueba para insertar
    test_data = [
        {
            "flight_date": "2025-03-19",
            "origin": "BOG",
            "destination": "MDE",
            "flight_number": "AV205",
            "std": "08:30:00",
            "atd": "08:45:00",
            "groomers_in": "07:15:00",
            "groomers_out": "07:45:00",
            "crew_at_gate": "08:00:00",
            "ok_to_board": "08:15:00",
            "flight_secure": "08:35:00",
            "cierre_de_puerta": "08:40:00",
            "push_back": "08:45:00",
            "pax_ob_total": "120",
            "customs_in": "N/A",
            "delay": "15",
            "gate": "G12",
            "carrousel": "3",
            "delay_code": "CREW",
            "WCHR": "0",
            "comments": "Vuelo de prueba"
        },
        {
            "flight_date": "2025-03-18",
            "origin": "MDE",
            "destination": "BOG",
            "flight_number": "AV255",
            "std": "14:30:00",
            "atd": "14:40:00",
            "groomers_in": "13:15:00",
            "groomers_out": "13:45:00",
            "crew_at_gate": "14:00:00",
            "ok_to_board": "14:15:00",
            "flight_secure": "14:35:00",
            "cierre_de_puerta": "14:38:00",
            "push_back": "14:40:00",
            "pax_ob_total": "150",
            "customs_in": "N/A",
            "delay": "10",
            "gate": "G5",
            "carrousel": "2",
            "delay_code": "WEATHER",
            "WCHR": "2",
            "comments": "Retraso por lluvia"
        }
    ]
    
    # Botu00f3n para insertar datos
    if st.button("Insertar Datos de Prueba"):
        with st.spinner("Insertando datos..."):
            success_count = 0
            for data in test_data:
                try:
                    response = client.table(DEFAULT_TABLE_NAME).insert(data).execute()
                    
                    if hasattr(response, 'error') and response.error is not None:
                        st.error(f"Error al insertar datos: {response.error}")
                        logger.error(f"Error al insertar datos: {response.error}")
                    else:
                        success_count += 1
                        logger.info(f"Datos insertados correctamente: {data['flight_number']}")
                except Exception as e:
                    st.error(f"Error al insertar datos: {str(e)}")
                    logger.exception(f"Error al insertar datos: {e}")
            
            if success_count > 0:
                st.success(f"Se insertaron {success_count} registros correctamente")
            else:
                st.warning("No se pudo insertar ningu00fan registro")
    
    # Verificar datos existentes
    st.subheader("Datos Existentes en la Tabla")
    try:
        response = client.table(DEFAULT_TABLE_NAME).select("*").execute()
        
        if hasattr(response, 'error') and response.error is not None:
            st.error(f"Error al consultar datos: {response.error}")
        else:
            st.write(f"Registros encontrados: {len(response.data)}")
            if len(response.data) > 0:
                st.write("Registros:")
                for i, record in enumerate(response.data):
                    with st.expander(f"Vuelo {i+1}: {record.get('flight_number')} - {record.get('flight_date')}"):
                        st.json(record)
            else:
                st.warning("No hay registros en la tabla")
    except Exception as e:
        st.error(f"Error al consultar datos: {str(e)}")

if __name__ == "__main__":
    main()
