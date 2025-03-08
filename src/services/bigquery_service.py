from google.cloud import bigquery
from typing import Dict, Any, Tuple, Optional

from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def send_data_to_bigquery(client: bigquery.Client, table_id: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Envía datos a BigQuery.
    
    Args:
        client (bigquery.Client): Cliente de BigQuery inicializado
        table_id (str): ID de la tabla de BigQuery
        data (Dict[str, Any]): Datos a enviar
        
    Returns:
        tuple: (éxito, mensaje_error) donde:
            - éxito: bool indicando si la operación fue exitosa
            - mensaje_error: str con el mensaje de error o None si fue exitoso
    """
    if client is None:
        logger.error("No se puede enviar datos: el cliente de BigQuery no está inicializado")
        return False, "No se ha inicializado el cliente de BigQuery"
        
    try:
        logger.info(f"Enviando datos a BigQuery tabla: {table_id}")
        logger.info(f"Datos a enviar: {data}")
        
        job_config = bigquery.LoadJobConfig()
        job = client.load_table_from_json([data], table_id, job_config=job_config)
        job.result()  # Esperar a que termine el job

        if job.errors:
            error_msg = f"Errores en el job de BigQuery: {job.errors}"
            logger.error(error_msg)
            return False, error_msg
        else:
            logger.info("Datos enviados exitosamente a BigQuery")
            return True, None
            
    except Exception as e:
        error_msg = f"Error al enviar datos a BigQuery: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg