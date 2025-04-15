import logging
import streamlit as st
from supabase import create_client

from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def initialize_supabase_client():
    """
    Inicializa el cliente de Supabase usando las credenciales de Streamlit Secrets.
    
    Returns:
        tuple: (client, project_ref, error_message) donde:
            - client: Cliente de Supabase o None si hay error
            - project_ref: Referencia del proyecto de Supabase
            - error_message: Mensaje de error o None si todo está bien
    """
    try:
        # Intentar cargar credenciales con estructura anidada
        try:
            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]
            project_ref = st.secrets["supabase"]["project_ref"]
            
            # Verificar si se ha especificado un service_role_key
            if "service_role_key" in st.secrets["supabase"]:
                # Usar service_role_key si está disponible
                service_role_key = st.secrets["supabase"]["service_role_key"]
                if service_role_key and service_role_key.strip():
                    logger.info("Usando service_role_key para autenticación")
                    supabase_key = service_role_key
            
            logger.info("Credenciales cargadas correctamente desde estructura anidada.")
        except:
            # Intentar cargar credenciales con estructura plana
            supabase_url = st.secrets["url"]
            supabase_key = st.secrets["key"]
            project_ref = st.secrets["project_ref"]
            
            # Verificar si se ha especificado un service_role_key
            if "service_role_key" in st.secrets:
                # Usar service_role_key si está disponible
                service_role_key = st.secrets["service_role_key"]
                if service_role_key and service_role_key.strip():
                    logger.info("Usando service_role_key para autenticación")
                    supabase_key = service_role_key
            
            logger.info("Credenciales cargadas correctamente desde estructura plana.")
        
        try:
            client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully.")
            return client, project_ref, None
        except Exception as e:
            error_msg = f"Error al inicializar Supabase: {str(e)}"
            logger.exception("Error initializing Supabase client:")
            return None, project_ref, error_msg
            
    except Exception as e:
        error_msg = f"Error al cargar credenciales: {str(e)}"
        logger.exception("Error al cargar credenciales de Streamlit Secrets:")
        return None, None, error_msg

# Tabla predeterminada en Supabase
DEFAULT_TABLE_NAME = "flightfeportava"
