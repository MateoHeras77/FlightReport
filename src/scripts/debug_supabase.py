import streamlit as st
import logging
import sys
import os

# Agregar el directorio raíz al path para que las importaciones funcionen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.config.supabase_config import initialize_supabase_client, DEFAULT_TABLE_NAME
from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def main():
    st.title("Depuración de Conexión a Supabase")
    
    # Inicializar cliente de Supabase
    client, project_ref, error = initialize_supabase_client()
    
    if error:
        st.error(f"Error al conectar con Supabase: {error}")
        return
    
    st.success("Conexión a Supabase establecida correctamente")
    st.write(f"Proyecto: {project_ref}")
    
    # Intentar diferentes consultas para depurar
    st.subheader("Prueba 1: Listar todas las tablas")
    try:
        # Listar todas las tablas disponibles
        tables = client.table("pg_tables").select("tablename").eq("schemaname", "public").execute()
        st.write("Tablas disponibles:")
        for table in tables.data:
            st.write(f"- {table['tablename']}")
    except Exception as e:
        st.error(f"Error al listar tablas: {str(e)}")
    
    st.subheader(f"Prueba 2: Consultar tabla '{DEFAULT_TABLE_NAME}' sin filtros")
    try:
        # Consulta simple sin filtros
        response = client.table(DEFAULT_TABLE_NAME).select("*").limit(5).execute()
        
        if hasattr(response, 'error') and response.error is not None:
            st.error(f"Error en la consulta: {response.error}")
        else:
            st.write(f"Registros encontrados: {len(response.data)}")
            if len(response.data) > 0:
                st.write("Columnas disponibles:")
                st.write(list(response.data[0].keys()))
                st.write("Primer registro:")
                st.json(response.data[0])
            else:
                st.warning("No se encontraron registros en la tabla")
    except Exception as e:
        st.error(f"Error al consultar tabla: {str(e)}")
    
    st.subheader("Prueba 3: Consultar tabla con nombre en minúsculas")
    try:
        # Probar con nombre de tabla en minúsculas
        table_name_lower = DEFAULT_TABLE_NAME.lower()
        response = client.table(table_name_lower).select("*").limit(5).execute()
        
        if hasattr(response, 'error') and response.error is not None:
            st.error(f"Error en la consulta: {response.error}")
        else:
            st.write(f"Registros encontrados: {len(response.data)}")
            if len(response.data) > 0:
                st.write("Columnas disponibles:")
                st.write(list(response.data[0].keys()))
                st.write("Primer registro:")
                st.json(response.data[0])
            else:
                st.warning("No se encontraron registros en la tabla")
    except Exception as e:
        st.error(f"Error al consultar tabla: {str(e)}")

if __name__ == "__main__":
    main()
