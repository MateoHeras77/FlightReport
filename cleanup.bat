@echo off
echo Eliminando archivos relacionados con Google Cloud y BigQuery...

REM Eliminar archivos de configuracion de BigQuery
if exist src\config\bigquery_config.py del src\config\bigquery_config.py

REM Eliminar archivos de servicios de BigQuery
if exist src\services\bigquery_service.py del src\services\bigquery_service.py

REM Eliminar archivos de credenciales de Google Cloud (si existen)
if exist .streamlit\secrets.toml.bak del .streamlit\secrets.toml.bak

echo Limpieza completada.
echo Recuerda verificar que no queden referencias a Google Cloud o BigQuery en el codigo.
