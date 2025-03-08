# Avianca - Sistema de Reporte de Vuelos

Aplicación desarrollada en Streamlit para la gestión y envío de reportes de vuelos de Avianca a BigQuery.

## Estructura del Proyecto

```
avianca/
├── app.py                  # Punto de entrada principal de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── logs/                   # Directorio para archivos de log
└── src/                    # Código fuente de la aplicación
    ├── components/         # Componentes UI de Streamlit
    │   └── flight_form.py  # Formulario de vuelo
    ├── config/             # Configuraciones
    │   ├── bigquery_config.py  # Configuración de BigQuery
    │   └── logging_config.py   # Configuración de logging
    ├── models/             # Modelos de datos
    ├── services/           # Servicios externos
    │   └── bigquery_service.py  # Servicios para BigQuery
    └── utils/              # Utilidades
        └── form_utils.py   # Utilidades para formularios
```

## Requisitos

- Python 3.8 o superior
- Streamlit
- Google Cloud BigQuery
- Otras dependencias en `requirements.txt`

## Instalación

1. Clonar el repositorio
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Configurar credenciales:
   - Crear un archivo `.streamlit/secrets.toml` con las credenciales de Google Cloud
   - O configurar las credenciales en la plataforma donde se despliega Streamlit

## Ejecución

Para ejecutar la aplicación localmente:

```bash
streamlit run app.py
```

## Logging

Los logs se almacenan en el directorio `logs/` con archivos diarios con formato `app_YYYY-MM-DD.log`.

## BigQuery

La aplicación envía datos a la tabla `unfc-439001.avianca2000.ReporteVuelo` en BigQuery. Esta tabla debe estar configurada con las columnas apropiadas para recibir los datos del formulario.