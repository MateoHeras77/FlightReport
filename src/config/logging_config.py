import os
import logging
from datetime import datetime

def setup_logger(logger_name="flight_report_logger", log_folder="logs"):
    """
    Configura un logger con handlers para archivo y consola.
    
    Args:
        logger_name (str): Nombre del logger
        log_folder (str): Carpeta donde se guardarán los logs
    
    Returns:
        logging.Logger: Logger configurado
    """
    # Crear directorio de logs si no existe
    os.makedirs(log_folder, exist_ok=True)
    
    # Crear o recuperar logger existente
    logger = logging.getLogger(logger_name)
    
    # Si el logger ya está configurado, devolverlo tal cual
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Formato estándar para todos los handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
    # Crear handler para archivo con fecha en el nombre para rotar logs diarios
    current_date = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        os.path.join(log_folder, f"app_{current_date}.log"),
        mode="a"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para la consola
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger