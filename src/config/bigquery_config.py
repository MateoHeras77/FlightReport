import logging
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def initialize_bigquery_client():
    """
    Inicializa el cliente de BigQuery usando las credenciales de Streamlit Secrets.
    
    Returns:
        tuple: (client, project_id, error_message) donde:
            - client: Cliente de BigQuery o None si hay error
            - project_id: ID del proyecto de Google Cloud
            - error_message: Mensaje de error o None si todo está bien
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        project_id = st.secrets["gcp_service_account"]["project_id"]
        logger.info("Credenciales cargadas correctamente desde Streamlit Secrets.")
        
        try:
            client = bigquery.Client(credentials=credentials, project=project_id)
            logger.info("BigQuery client initialized successfully.")
            return client, project_id, None
        except Exception as e:
            error_msg = f"Error al inicializar BigQuery: {str(e)}"
            logger.exception("Error initializing BigQuery client:")
            return None, project_id, error_msg
            
    except Exception as e:
        error_msg = f"Error al cargar credenciales: {str(e)}"
        logger.exception("Error al cargar credenciales de Streamlit Secrets:")
        return None, None, error_msg

# Tabla predeterminada en BigQuery
DEFAULT_TABLE_ID = "unfc-439001.avianca2000.Reportes"