from typing import Dict, Any, Tuple, Optional

from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def send_data_to_supabase(client, table_name: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Envu00eda datos a Supabase.
    
    Args:
        client: Cliente de Supabase inicializado
        table_name (str): Nombre de la tabla de Supabase
        data (Dict[str, Any]): Datos a enviar
        
    Returns:
        tuple: (u00e9xito, mensaje_error) donde:
            - u00e9xito: bool indicando si la operaciu00f3n fue exitosa
            - mensaje_error: str con el mensaje de error o None si fue exitoso
    """
    if client is None:
        logger.error("No se puede enviar datos: el cliente de Supabase no estu00e1 inicializado")
        return False, "No se ha inicializado el cliente de Supabase"
        
    try:
        logger.info(f"Enviando datos a Supabase tabla: {table_name}")
        logger.info(f"Datos a enviar: {data}")
        
        # Insertar datos en la tabla de Supabase
        response = client.table(table_name).insert(data).execute()
        
        # Verificar si hay errores
        if hasattr(response, 'error') and response.error is not None:
            error_msg = f"Errores al insertar en Supabase: {response.error}"  
            logger.error(error_msg)
            return False, error_msg
        else:
            logger.info("Datos enviados exitosamente a Supabase")
            return True, None
            
    except Exception as e:
        error_msg = f"Error al enviar datos a Supabase: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg

def fetch_data_from_supabase(client, table_name: str, query_params: Dict[str, Any] = None) -> Tuple[bool, Any, Optional[str]]:
    """
    Obtiene datos de Supabase con filtros opcionales.
    
    Args:
        client: Cliente de Supabase inicializado
        table_name (str): Nombre de la tabla de Supabase
        query_params (Dict[str, Any]): Paru00e1metros de consulta opcionales
        
    Returns:
        tuple: (u00e9xito, datos, mensaje_error) donde:
            - u00e9xito: bool indicando si la operaciu00f3n fue exitosa
            - datos: Datos obtenidos o None si hubo error
            - mensaje_error: str con el mensaje de error o None si fue exitoso
    """
    if client is None:
        logger.error("No se puede obtener datos: el cliente de Supabase no estu00e1 inicializado")
        return False, None, "No se ha inicializado el cliente de Supabase"
    
    try:
        logger.info(f"Obteniendo datos de Supabase tabla: {table_name}")
        
        # Iniciar la consulta
        query = client.table(table_name).select("*")
        
        # Aplicar filtros si existen
        if query_params:
            for key, value in query_params.items():
                if value is not None:
                    query = query.eq(key, value)
        
        # Ejecutar la consulta
        response = query.execute()
        
        # Verificar si hay errores
        if hasattr(response, 'error') and response.error is not None:
            error_msg = f"Errores al consultar Supabase: {response.error}"
            logger.error(error_msg)
            return False, None, error_msg
        else:
            data = response.data
            logger.info(f"Datos obtenidos exitosamente de Supabase: {len(data)} registros")
            return True, data, None
            
    except Exception as e:
        error_msg = f"Error al obtener datos de Supabase: {str(e)}"
        logger.exception(error_msg)
        return False, None, error_msg
